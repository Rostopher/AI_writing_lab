/**
 * test_split.ts — 用 DeepSeek 已标注的 n_sentences 验证拆句器质量。
 *
 * 对比 run_v03_full 里每张表的 n_sentences（DS 数的）和拆句器拆出的句数。
 * 只统计 footnote 非空且 note_verdict=ok 的表。
 */
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import fs from 'node:fs';
import { splitSentences } from './sentence_split.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const AW = path.resolve(__dirname, '..');
const UNITS = path.join(AW, 'outputs', 'table_notes', 'table_units_v3.jsonl');
const ANN = path.join(AW, 'outputs', 'table_notes', 'run_v03_full', 'annotations.jsonl');

interface Unit {
  paper_id: string;
  tables: { idx: number; footnote: string | null }[];
}

// DS 标注：paper_id|idx -> {n_sentences, note_verdict}
const dsMap = new Map<string, { n: number; verdict: string | null }>();
for (const line of fs.readFileSync(ANN, 'utf-8').split('\n').filter(Boolean)) {
  const d = JSON.parse(line);
  for (const t of d.output.tables) {
    dsMap.set(`${d.paper_id}|${t.idx}`, { n: t.n_sentences, verdict: t.note_verdict });
  }
}

let exact = 0;
let off1 = 0;
let off2plus = 0;
let total = 0;
const mismatches: { id: string; ds: number; ours: number; footnote: string; ours_sents: string[] }[] = [];

for (const line of fs.readFileSync(UNITS, 'utf-8').split('\n').filter(Boolean)) {
  const p: Unit = JSON.parse(line);
  for (const t of p.tables) {
    const fn = (t.footnote ?? '').trim();
    if (!fn) continue;
    const ds = dsMap.get(`${p.paper_id}|${t.idx}`);
    if (!ds || ds.verdict !== 'ok') continue;
    const ours = splitSentences(fn);
    total++;
    const diff = Math.abs(ours.length - ds.n);
    if (diff === 0) exact++;
    else if (diff === 1) off1++;
    else {
      off2plus++;
      if (mismatches.length < 15) {
        mismatches.push({
          id: `${p.paper_id}|${t.idx}`,
          ds: ds.n,
          ours: ours.length,
          footnote: fn.slice(0, 400),
          ours_sents: ours.slice(0, 12),
        });
      }
    }
  }
}

console.log(`共 ${total} 张有注且 verdict=ok 的表`);
console.log(`句数完全一致: ${exact} (${((exact / total) * 100).toFixed(1)}%)`);
console.log(`差 1 句:      ${off1} (${((off1 / total) * 100).toFixed(1)}%)`);
console.log(`差 >=2 句:    ${off2plus} (${((off2plus / total) * 100).toFixed(1)}%)`);

console.log('\n=== 差 >=2 的例子 ===');
for (const m of mismatches) {
  console.log(`\n--- ${m.id}  DS=${m.ds} ours=${m.ours} ---`);
  m.ours_sents.forEach((s, i) => console.log(`  [${i + 1}] ${s.slice(0, 110)}`));
}
