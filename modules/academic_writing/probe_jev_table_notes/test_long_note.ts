/**
 * test_jev_table_notes.ts — Jev 表注标注 v2：每句单选 + 多功能标记。
 *
 * 每张表一次调用：
 *   state = caption + body_head + footnote
 *   questions =
 *     table_type: Choice（10 类）
 *     s{i}_func:  Choice（12 功能 + none，该句的**主要**功能）
 *     s{i}_multi: boolean（该句是否同时承担多个功能）
 *
 * 对 multi=true 的句子，第二次调用补问其余功能的布尔。
 *
 * 问题数 = 1 + 2×句数（+ 二次调用的 11×multi句数）。
 * 只调用 typesafe-ai/jev。
 */
import 'dotenv/config';
import { experimental_evaluate as evaluate } from 'ai';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import fs from 'node:fs';
import dotenv from 'dotenv';
import { splitSentences } from './sentence_split.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '..', '..', '..');
dotenv.config({ path: path.join(repoRoot, '.env') });
if (!process.env.AI_GATEWAY_API_KEY && process.env.JEV_API_KEY) {
  process.env.AI_GATEWAY_API_KEY = process.env.JEV_API_KEY;
}
if (!process.env.AI_GATEWAY_API_KEY) {
  throw new Error('缺少 AI_GATEWAY_API_KEY / JEV_API_KEY');
}

const JEV_MODEL = 'typesafe-ai/jev';
const UNITS = path.join(repoRoot, 'modules/academic_writing/outputs/table_notes/table_units_v3.jsonl');
const DS_ANN = path.join(repoRoot, 'modules/academic_writing/outputs/table_notes/run_v03_full/annotations.jsonl');

// ---------- 表类型 ----------
const TABLE_TYPE = {
  type: 'choice' as const,
  instructions: `What is the primary role of this table in the paper? Judge from the caption, the row/column labels, and the note text.`,
  criteria: {
    summary_stats: 'Descriptive statistics of variables (means, SDs, distributions).',
    main_results: 'Main regression/estimation results of the paper\'s central question.',
    robustness: 'Robustness checks, sensitivity analyses, alternative specifications or samples.',
    heterogeneity: 'Heterogeneity analysis: results split by subgroups or subsamples.',
    mechanism: 'Mechanism, channel, or mediation analysis explaining the main result.',
    balance_test: 'Balance tests, randomization checks, covariate comparisons across groups.',
    first_stage_iv: 'First-stage regressions or instrument diagnostics for IV designs.',
    structural_model: 'Structural model results: calibration, simulation, counterfactuals, welfare analysis, model fit.',
    data_description: 'Sample selection, data construction, or experimental design description.',
    other: 'None of the above.',
  },
};

// ---------- 句级功能 ----------
const ROLES: Record<string, string> = {
  sig_marker: 'standard errors / significance stars / clustering level (e.g. "SE in parentheses", "clustered at classroom")',
  table_purpose: 'what the table estimates or reports (e.g. "The table presents OLS coefficients...")',
  identification: 'identification strategy (IV, DID, RDD, RCT, instrument, fixed effects)',
  var_def: 'variable/abbreviation definition or construction (e.g. "X is coded as...", "refers to")',
  data_source: 'data source / survey wave / sample period (e.g. "from the 1990 Census", "See Data Appendix")',
  method: 'estimation method detail (OLS, MLE, block bootstrap, GLS)',
  sample: 'sample composition or restriction (e.g. "control sample only", "N=", "excludes")',
  col_nav: 'column or panel navigation (e.g. "Column 1 is the baseline", "Panel A reports")',
  multiple_test: 'multiple-hypothesis correction (FDR q-value, Romano-Wolf)',
  cross_ref: 'pointer to another table\'s note (e.g. "See notes to Table 1", "as in Table")',
  abbrev_expand: 'expands an abbreviation into its full form (e.g. "MTO stands for Moving to Opportunity")',
};

const FUNC_CHOICE_CRITERIA: Record<string, string> = {
  ...Object.fromEntries(Object.entries(ROLES).map(([k, v]) => [k, `The sentence serves this function: ${v}`])),
  other: 'The sentence has substantive content but serves none of the listed functions.',
  none: 'The sentence carries no substantive note content (pure connective, fragment, or leftover marker).',
};

// ---------- 数据 ----------
interface TableUnit {
  idx: number;
  caption: string;
  body_head: string[];
  footnote: string | null;
  footnote_source: string | null;
}

function loadDsAnn(): Map<string, any> {
  const m = new Map<string, any>();
  for (const line of fs.readFileSync(DS_ANN, 'utf-8').split('\n').filter(Boolean)) {
    const d = JSON.parse(line);
    for (const t of d.output.tables) {
      m.set(`${d.paper_id}|${t.idx}`, t);
    }
  }
  return m;
}

function loadUnits(): Map<string, { paperId: string; t: TableUnit }> {
  const m = new Map<string, { paperId: string; t: TableUnit }>();
  for (const line of fs.readFileSync(UNITS, 'utf-8').split('\n').filter(Boolean)) {
    const p = JSON.parse(line);
    for (const t of p.tables) {
      m.set(`${p.paper_id}|${t.idx}`, { paperId: p.paper_id, t });
    }
  }
  return m;
}

// ---------- 标注一张表 ----------
async function annotateTable(paperId: string, t: TableUnit) {
  const footnote = (t.footnote ?? '').trim();
  const sentences = splitSentences(footnote);

  const state = [
    `Table caption: ${t.caption}`,
    `Table row/column labels: ${t.body_head.slice(0, 30).join(' | ')}`,
    `Footnote text: ${footnote}`,
  ].join('\n');

  // ---- 第 1 次调用：表类型 + 每句主功能单选 + 多功能标记 ----
  const questions: Record<string, any> = { table_type: TABLE_TYPE };
  sentences.forEach((s, i) => {
    questions[`s${i + 1}_func`] = {
      type: 'choice',
      instructions: `Consider sentence ${i + 1} of the footnote: "${s}" — Which function BEST describes this sentence's PRIMARY role in the note?`,
      criteria: FUNC_CHOICE_CRITERIA,
    };
    questions[`s${i + 1}_multi`] = {
      type: 'boolean',
      instructions: `Consider sentence ${i + 1} of the footnote: "${s}" — Does this sentence serve MORE THAN ONE of the note functions at the same time (e.g. it both states the table's purpose and gives the data source, or both defines variables and describes the sample)?`,
    };
  });

  const r1 = await evaluate({ model: JEV_MODEL, state, questions });

  const sentsOut = sentences.map((s, i) => {
    const funcAns = r1.answers[`s${i + 1}_func`] as { choice: string; probabilities?: Record<string, number> };
    const multiAns = r1.answers[`s${i + 1}_multi`] as { probability: number };
    return {
      sentence: s,
      primary_func: funcAns.choice,
      func_probs: funcAns.probabilities ?? {},
      multi_prob: multiAns.probability,
      extra_roles: {} as Record<string, number>,
    };
  });

  // ---- 第 2 次调用：多功能句补问其余功能 ----
  const multiIdx = sentsOut
    .map((s, i) => ({ s, i }))
    .filter(({ s }) => s.multi_prob >= 0.5 && s.primary_func !== 'none');

  let usage2: any = null;
  if (multiIdx.length > 0) {
    const q2: Record<string, any> = {};
    for (const { s, i } of multiIdx) {
      for (const [role, desc] of Object.entries(ROLES)) {
        if (role === s.primary_func) continue; // 主功能已知，跳过
        q2[`s${i + 1}_${role}`] = {
          type: 'boolean',
          instructions: `Consider sentence ${i + 1} of the footnote: "${s.sentence}" — Besides its primary function (${s.primary_func}), does this sentence ALSO serve this function: ${desc}?`,
        };
      }
    }
    const r2 = await evaluate({ model: JEV_MODEL, state, questions: q2 });
    usage2 = r2.usage ?? null;
    for (const { s, i } of multiIdx) {
      for (const role of Object.keys(ROLES)) {
        if (role === s.primary_func) continue;
        sentsOut[i].extra_roles[role] = (r2.answers[`s${i + 1}_${role}`] as { probability: number }).probability;
      }
    }
  }

  return {
    paper_id: paperId,
    idx: t.idx,
    n_sentences: sentences.length,
    table_type: (r1.answers.table_type as { choice: string }).choice,
    table_type_probs: (r1.answers.table_type as { probabilities?: Record<string, number> }).probabilities,
    sentences: sentsOut,
    n_questions_pass1: Object.keys(questions).length,
    n_questions_pass2: multiIdx.length * (Object.keys(ROLES).length - 1),
    usage: r1.usage ?? null,
    usage2,
  };
}

// ---------- 测试主流程 ----------
async function main() {
  const dsAnn = loadDsAnn();
  const units = loadUnits();

  const wanted: string[] = ['qje_2026_qjag002|6'];

  for (const key of wanted) {
    const { paperId, t } = units.get(key)!;
    const ds = dsAnn.get(key)!;
    console.log(`\n${'='.repeat(90)}`);
    console.log(`${key} | DS: n_sent=${ds.n_sentences} roles=${ds.roles.join(',')}`);
    console.log(`caption: ${t.caption.slice(0, 100)}`);

    try {
      const r = await annotateTable(paperId, t);
      console.log(`Jev: ${r.n_sentences} 句 | 调用1: ${r.n_questions_pass1} 问 (${r.usage?.totalTokens ?? '?'} tok) | 调用2: ${r.n_questions_pass2} 问 (${r.usage2?.totalTokens ?? 0} tok)`);
      console.log(`表类型: ${r.table_type}  probs=${JSON.stringify(r.table_type_probs)}`);
      r.sentences.forEach((s, i) => {
        const top2 = Object.entries(s.func_probs).sort((a, b) => b[1] - a[1]).slice(0, 2)
          .map(([k, p]) => `${k}(${p.toFixed(2)})`).join(' ');
        const extra = Object.entries(s.extra_roles).filter(([, p]) => p >= 0.5).map(([k, p]) => `${k}(${p.toFixed(2)})`);
        console.log(`  句${i + 1}: ${s.sentence.slice(0, 85)}`);
        console.log(`       主功能=${s.primary_func} [${top2}] multi=${s.multi_prob.toFixed(2)}${extra.length ? ' 附加=' + extra.join(' ') : ''}`);
      });
    } catch (err: any) {
      console.log(`  !! 失败: ${String(err?.message ?? err).slice(0, 150)}`);
    }
  }
}

main().catch((err) => {
  console.error('调用失败：', err);
  process.exit(1);
});
