/**
 * probe: Jev 论文类型分类 benchmark（对齐 DeepSeek v0.3 prompt 语义）。
 *
 * DeepSeek prompt 的 RESEARCH TYPE 段定义了：
 *   - 三个成分标记 empirical / theory / structural（yes/no/unclear，非互斥）
 *   - 一个主类型 primary_type（empirical / theory / mixed_or_structural / methods / unclear）
 *
 * Jev 接口是布尔问题，所以把三个成分 + methods 主贡献 各做成一个 boolean 问题，
 * 再用代码组合出 primary_type，组合规则对齐 DeepSeek 的优先级说明。
 *
 * 只调用 typesafe-ai/jev。
 */
import 'dotenv/config';
import { experimental_evaluate as evaluate } from 'ai';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import fs from 'node:fs';
import dotenv from 'dotenv';

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
const RUN_DIR = path.join(
  repoRoot,
  'data/processed/abstract_structure/run_20260909_v03_full'
);
const CORPUS = path.join(
  repoRoot,
  'data/processed/abstract_structure/run_20260908_a/corpus_manifest.jsonl'
);
const OUT = path.join(__dirname, 'jev_results_sample.jsonl');

const PER_CLASS = Number(process.env.PER_CLASS ?? 5);
const THRESHOLD = Number(process.env.JEV_THRESHOLD ?? 0.5);

// ---------- 读取 DeepSeek 标注 + 摘要语料 ----------
interface Ann {
  article_id: string;
  primary_type: string;
  empirical_component: string;
  theory_component: string;
  structural_component: string;
}
interface CorpusRow {
  article_id: string;
  title: string;
  abstract_normalized: string;
  journal_code: string;
  year: string;
}

function loadAnnotations(): Map<string, Ann> {
  const m = new Map<string, Ann>();
  const lines = fs
    .readFileSync(path.join(RUN_DIR, 'annotation_flash/annotations.jsonl'), 'utf-8')
    .split('\n')
    .filter(Boolean);
  for (const line of lines) {
    const d = JSON.parse(line);
    const pt = d.output?.paper_type;
    if (!pt) continue;
    m.set(d.article_id, {
      article_id: d.article_id,
      primary_type: pt.primary_type,
      empirical_component: pt.empirical_component,
      theory_component: pt.theory_component,
      structural_component: pt.structural_component,
    });
  }
  return m;
}

function loadCorpus(): Map<string, CorpusRow> {
  const m = new Map<string, CorpusRow>();
  const lines = fs.readFileSync(CORPUS, 'utf-8').split('\n').filter(Boolean);
  for (const line of lines) {
    const d = JSON.parse(line);
    if (d.abstract_normalized && d.included) {
      m.set(d.article_id, d);
    }
  }
  return m;
}

// ---------- 组合规则：对齐 DeepSeek primary_type 优先级 ----------
// DeepSeek 语义：
//   methods: main contribution 是方法/估计量/推断程序/测量工具/方法性质（优先）
//   mixed_or_structural: 理论+实证结合，或结构模型被估计/校准并量化使用
//   empirical: 主贡献是观测/实验数据的实质分析
//   theory: 主贡献是理论分析或形式经济结果
//   unclear: 证据不足或冲突
function composePrimaryType(
  methods: number,
  empirical: number,
  theory: number,
  structural: number,
  th = THRESHOLD
): string {
  const m = methods >= th;
  const e = empirical >= th;
  const t = theory >= th;
  const s = structural >= th;

  if (m) return 'methods';
  if (s) return 'mixed_or_structural'; // 结构估计/校准 → mixed_or_structural
  if (t && e) return 'mixed_or_structural'; // 理论+实证结合
  if (e) return 'empirical';
  if (t) return 'theory';
  return 'unclear';
}

// ---------- Jev 问题（措辞对齐 DeepSeek 成分定义） ----------
const QUESTIONS = {
  // -- 成分层：非互斥布尔 --
  methods: {
    type: 'boolean' as const,
    instructions: `Is the paper's main contribution a research method, estimator, inferential procedure, measurement tool, or a methodological property? Answer yes even if proofs or applications are also present; answer yes only when methodological development is the main contribution.`,
  },
  empirical: {
    type: 'boolean' as const,
    instructions: `Does the abstract provide explicit evidence that the paper conducts substantive analysis of observed or experimental data? This is a non-exclusive component judgment, not the paper's primary type.`,
  },
  theory: {
    type: 'boolean' as const,
    instructions: `Does the abstract provide explicit evidence that the paper develops theoretical analysis or formal economic results? A statistical regression model is not automatically economic theory. This is a non-exclusive component judgment.`,
  },
  structural: {
    type: 'boolean' as const,
    instructions: `Does the abstract provide explicit evidence that an economic structural model is estimated, calibrated, or fit to data and used quantitatively? A statistical regression model is not automatically structural modeling. This is a non-exclusive component judgment.`,
  },

  // -- 主类型层：Choice 单选，类别描述对齐 DeepSeek primary_type 定义 --
  primary_type: {
    type: 'choice' as const,
    instructions: `Classify this economics paper by its primary contribution type, based only on the abstract. The categories are mutually exclusive.`,
    criteria: {
      empirical:
        'Main contribution is substantive analysis of observed or experimental data.',
      theory:
        'Main contribution is theoretical analysis or formal economic results.',
      mixed_or_structural:
        'Substantive theory and empirical analysis are combined, or an economic structural model is estimated/calibrated and used quantitatively.',
      methods:
        'Main contribution is a research method, estimator, inferential procedure, measurement tool, or methodological property, even if proofs or applications are present.',
      unclear:
        'Insufficient or conflicting evidence in the abstract.',
    },
  },
};

async function main() {
  const anns = loadAnnotations();
  const corpus = loadCorpus();

  // 分层抽样
  const byType = new Map<string, string[]>();
  for (const [id, a] of anns) {
    if (!corpus.has(id)) continue;
    const arr = byType.get(a.primary_type) ?? [];
    arr.push(id);
    byType.set(a.primary_type, arr);
  }

  const sample: string[] = [];
  for (const [t, ids] of [...byType.entries()].sort()) {
    ids.sort();
    const step = Math.max(1, Math.floor(ids.length / PER_CLASS));
    let taken = 0;
    for (let i = 0; i < ids.length && taken < PER_CLASS; i += step) {
      sample.push(ids[i]);
      taken++;
    }
    console.log(`类型 ${t}: 总 ${ids.length} 篇，抽 ${taken} 篇`);
  }

  console.log(`\n共抽 ${sample.length} 篇，阈值=${THRESHOLD}，开始 Jev 判定...\n`);

  const out = fs.createWriteStream(OUT, 'utf-8');
  let n = 0;

  // 成分层一致率（Jev 布尔概率 >= 阈值 → yes，否则 no；DeepSeek 是 yes/no/unclear）
  let compAgree = { empirical: 0, theory: 0, structural: 0 };
  let compTotal = { empirical: 0, theory: 0, structural: 0 };
  const compConfusion = new Map<string, number>(); // "comp|ds|jev" -> count

  // 主类型一致率
  let agreeComposed = 0;
  let agreeChoice = 0;
  const confusionComposed = new Map<string, number>();
  const confusionChoice = new Map<string, number>();

  for (const id of sample) {
    const c = corpus.get(id)!;
    const a = anns.get(id)!;
    const state = `Title: ${c.title}\n\nAbstract: ${c.abstract_normalized}`;

    const result = await evaluate({
      model: JEV_MODEL,
      state,
      questions: QUESTIONS,
    });

    const m = result.answers.methods.probability;
    const e = result.answers.empirical.probability;
    const t = result.answers.theory.probability;
    const s = result.answers.structural.probability;
    const jevComposed = composePrimaryType(m, e, t, s);
    const jevChoice = result.answers.primary_type;
    const jevChoiceLabel = jevChoice.choice;
    const jevChoiceProbs = jevChoice.probabilities ?? {};

    // --- 成分层对比（empirical / theory / structural）---
    const dsComps: Record<string, string> = {
      empirical: a.empirical_component,
      theory: a.theory_component,
      structural: a.structural_component,
    };
    const jevProbs: Record<string, number> = {
      empirical: e,
      theory: t,
      structural: s,
    };
    const compDetail: Record<string, { ds: string; jev: number; match: boolean | null }> = {};
    for (const comp of ['empirical', 'theory', 'structural']) {
      const dsVal = dsComps[comp];
      const jevVal = jevProbs[comp];
      if (dsVal === 'unclear') {
        compDetail[comp] = { ds: dsVal, jev: jevVal, match: null };
        continue; // DS=unclear 不参与一致率
      }
      const jevBool = jevVal >= THRESHOLD ? 'yes' : 'no';
      const match = jevBool === dsVal;
      compDetail[comp] = { ds: dsVal, jev: jevVal, match };
      compTotal[comp as keyof typeof compTotal]++;
      if (match) compAgree[comp as keyof typeof compAgree]++;
      const ck = `${comp}|${dsVal}|${jevBool}`;
      compConfusion.set(ck, (compConfusion.get(ck) ?? 0) + 1);
    }

    // --- 主类型对比 ---
    const matchComposed = jevComposed === a.primary_type;
    const matchChoice = jevChoiceLabel === a.primary_type;
    if (matchComposed) agreeComposed++;
    if (matchChoice) agreeChoice++;
    n++;
    const keyC = `${a.primary_type}|${jevComposed}`;
    confusionComposed.set(keyC, (confusionComposed.get(keyC) ?? 0) + 1);
    const keyCh = `${a.primary_type}|${jevChoiceLabel}`;
    confusionChoice.set(keyCh, (confusionChoice.get(keyCh) ?? 0) + 1);

    const rec = {
      article_id: id,
      journal: c.journal_code,
      year: c.year,
      title: c.title.slice(0, 80),
      ds_primary_type: a.primary_type,
      ds_components: `e=${a.empirical_component} t=${a.theory_component} s=${a.structural_component}`,
      jev_probs: { methods: m, empirical: e, theory: t, structural: s },
      jev_composed: jevComposed,
      jev_choice: jevChoiceLabel,
      jev_choice_probs: jevChoiceProbs,
      comp_detail: compDetail,
      match_composed: matchComposed,
      match_choice: matchChoice,
    };
    out.write(JSON.stringify(rec) + '\n');

    const compStr = ['empirical', 'theory', 'structural']
      .map((k) => {
        const d = compDetail[k];
        if (d.match === null) return `${k[0]}=DS:unclear`;
        return `${k[0]}=${d.ds}/${d.jev >= THRESHOLD ? 'yes' : 'no'}${d.match ? '✓' : '✗'}`;
      })
      .join(' ');
    console.log(
      `[${n}/${sample.length}] ${id} | DS=${a.primary_type.padEnd(19)} | comp ${compStr} | composed=${jevComposed.padEnd(19)}${matchComposed ? '✓' : '✗'} | choice=${jevChoiceLabel.padEnd(19)}${matchChoice ? '✓' : '✗'}`
    );
  }

  out.end();

  // --- 汇总 ---
  console.log('\n========== 成分层一致率（Jev 布尔 vs DS component） ==========');
  for (const comp of ['empirical', 'theory', 'structural']) {
    const ag = compAgree[comp as keyof typeof compAgree];
    const tot = compTotal[comp as keyof typeof compTotal];
    console.log(`  ${comp}: ${ag}/${tot} = ${tot > 0 ? ((ag / tot) * 100).toFixed(1) : 'N/A'}%`);
  }
  console.log('\n成分层混淆 (component|DS|Jev → count):');
  for (const [k, v] of [...compConfusion.entries()].sort()) {
    console.log(`  ${k} → ${v}`);
  }

  console.log('\n========== 主类型一致率 ==========');
  console.log(`  composed: ${agreeComposed}/${n} = ${((agreeComposed / n) * 100).toFixed(1)}%`);
  console.log(`  choice:   ${agreeChoice}/${n} = ${((agreeChoice / n) * 100).toFixed(1)}%`);
  console.log('\n混淆矩阵 composed (DS|Jev → count):');
  for (const [k, v] of [...confusionComposed.entries()].sort()) {
    console.log(`  ${k} → ${v}`);
  }
  console.log('\n混淆矩阵 choice (DS|Jev → count):');
  for (const [k, v] of [...confusionChoice.entries()].sort()) {
    console.log(`  ${k} → ${v}`);
  }
  console.log(`\n结果写入 ${OUT}`);
}

main().catch((err) => {
  console.error('调用失败：', err);
  process.exit(1);
});
