/**
 * 全量 Jev 论文类型分类：对 run_20260909_v03_full 的 4250 篇摘要逐篇判定。
 *
 * 每篇一次 evaluate 调用，含 5 个问题：
 *   4 个布尔成分（methods / empirical / theory / structural）
 *   1 个 Choice 主类型（empirical / theory / mixed_or_structural / methods / unclear）
 *
 * 支持断点续跑：已写入结果的 article_id 跳过。
 * 只调用 typesafe-ai/jev。
 *
 * 用法：
 *   npx tsx run_full.ts                    # 全量
 *   PER_CLASS=10 npx tsx run_full.ts       # 每类抽 10 篇（测试）
 *   CONCURRENCY=5 npx tsx run_full.ts      # 并发数（默认 3）
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

const PER_CLASS = process.env.PER_CLASS ? Number(process.env.PER_CLASS) : 0; // 0 = 全量
const CONCURRENCY = Number(process.env.CONCURRENCY ?? 3);
const THRESHOLD = Number(process.env.JEV_THRESHOLD ?? 0.5);

const RUN_TAG = PER_CLASS > 0 ? `sample${PER_CLASS}` : 'full';
const OUT = path.join(__dirname, `jev_results_${RUN_TAG}.jsonl`);

// ---------- 数据加载 ----------
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

function loadDone(): Set<string> {
  const s = new Set<string>();
  if (!fs.existsSync(OUT)) return s;
  for (const line of fs.readFileSync(OUT, 'utf-8').split('\n').filter(Boolean)) {
    try {
      const d = JSON.parse(line);
      if (!d.error) s.add(d.article_id); // 只把成功的算作完成，错误记录会重试
    } catch { /* skip */ }
  }
  return s;
}

// ---------- 组合规则 ----------
function composePrimaryType(
  methods: number,
  empirical: number,
  theory: number,
  structural: number,
  th = THRESHOLD
): string {
  if (methods >= th) return 'methods';
  if (structural >= th) return 'mixed_or_structural';
  if (theory >= th && empirical >= th) return 'mixed_or_structural';
  if (empirical >= th) return 'empirical';
  if (theory >= th) return 'theory';
  return 'unclear';
}

// ---------- Jev 问题 ----------
const QUESTIONS = {
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
  primary_type: {
    type: 'choice' as const,
    instructions: `Classify this economics paper by its primary contribution type, based only on the abstract. The categories are mutually exclusive.`,
    criteria: {
      empirical: 'Main contribution is substantive analysis of observed or experimental data.',
      theory: 'Main contribution is theoretical analysis or formal economic results.',
      mixed_or_structural: 'Substantive theory and empirical analysis are combined, or an economic structural model is estimated/calibrated and used quantitatively.',
      methods: 'Main contribution is a research method, estimator, inferential procedure, measurement tool, or methodological property, even if proofs or applications are present.',
      unclear: 'Insufficient or conflicting evidence in the abstract.',
    },
  },
};

// ---------- 并发执行 ----------
async function processOne(
  id: string,
  corpus: Map<string, CorpusRow>,
  anns: Map<string, Ann>
): Promise<string | null> {
  const c = corpus.get(id)!;
  const a = anns.get(id)!;
  const state = `Title: ${c.title}\n\nAbstract: ${c.abstract_normalized}`;

  try {
    const result = await evaluate({ model: JEV_MODEL, state, questions: QUESTIONS });
    const m = result.answers.methods.probability;
    const e = result.answers.empirical.probability;
    const t = result.answers.theory.probability;
    const s = result.answers.structural.probability;
    const jevComposed = composePrimaryType(m, e, t, s);
    const jevChoiceLabel = result.answers.primary_type.choice;
    const jevChoiceProbs = result.answers.primary_type.probabilities ?? {};

    return JSON.stringify({
      article_id: id,
      journal: c.journal_code,
      year: c.year,
      ds_primary_type: a.primary_type,
      ds_empirical: a.empirical_component,
      ds_theory: a.theory_component,
      ds_structural: a.structural_component,
      jev_prob_methods: m,
      jev_prob_empirical: e,
      jev_prob_theory: t,
      jev_prob_structural: s,
      jev_composed: jevComposed,
      jev_choice: jevChoiceLabel,
      jev_choice_probs: jevChoiceProbs,
      usage: result.usage ?? null,
    });
  } catch (err: any) {
    return JSON.stringify({
      article_id: id,
      error: String(err?.message ?? err),
    });
  }
}

async function main() {
  const anns = loadAnnotations();
  const corpus = loadCorpus();
  const done = loadDone();

  // 收集候选 ID
  let ids: string[] = [];
  if (PER_CLASS > 0) {
    // 分层抽样
    const byType = new Map<string, string[]>();
    for (const [id, a] of anns) {
      if (!corpus.has(id)) continue;
      const arr = byType.get(a.primary_type) ?? [];
      arr.push(id);
      byType.set(a.primary_type, arr);
    }
    for (const [, typeIds] of [...byType.entries()].sort()) {
      typeIds.sort();
      const step = Math.max(1, Math.floor(typeIds.length / PER_CLASS));
      let taken = 0;
      for (let i = 0; i < typeIds.length && taken < PER_CLASS; i += step) {
        ids.push(typeIds[i]);
        taken++;
      }
    }
  } else {
    // 全量：按 article_id 排序保证确定性
    ids = [...anns.keys()].filter((id) => corpus.has(id)).sort();
  }

  const todo = ids.filter((id) => !done.has(id));
  console.log(
    `总 ${ids.length} 篇，已完成 ${done.size} 篇，待跑 ${todo.length} 篇，并发=${CONCURRENCY}`
  );

  if (todo.length === 0) {
    console.log('全部完成，退出。');
    return;
  }

  const out = fs.createWriteStream(OUT, { flags: 'a', encoding: 'utf-8' });
  let completed = 0;
  let errors = 0;
  const startTime = Date.now();

  // 简单并发池
  async function worker(queue: string[]) {
    while (queue.length > 0) {
      const id = queue.shift()!;
      const line = await processOne(id, corpus, anns);
      if (line) {
        out.write(line + '\n');
        const rec = JSON.parse(line);
        if (rec.error) errors++;
      }
      completed++;
      if (completed % 50 === 0 || completed === todo.length) {
        const elapsed = ((Date.now() - startTime) / 1000).toFixed(0);
        const rate = (completed / (Date.now() - startTime)) * 1000 * 60;
        console.log(
          `  进度 ${done.size + completed}/${ids.length} | 本轮 ${completed}/${todo.length} | ${errors} 错误 | ${elapsed}s | ~${rate.toFixed(0)}/min`
        );
      }
    }
  }

  const queue = [...todo];
  await Promise.all(Array.from({ length: CONCURRENCY }, () => worker(queue)));

  out.end();
  const totalTime = ((Date.now() - startTime) / 1000).toFixed(0);
  console.log(`\n完成：${completed} 篇，${errors} 错误，耗时 ${totalTime}s`);
  console.log(`结果写入 ${OUT}`);
}

main().catch((err) => {
  console.error('调用失败：', err);
  process.exit(1);
});
