/**
 * sentence_split.ts — 表注拆句。
 *
 * 规则：
 * - 按 [.!?] + 空白 拆分
 * - 保护常见缩写（e.g. i.e. et al. vs. cf. Fig. No. ...）、小数、p<.05、单字母缩写
 * - 忽略 "(continued)" 等翻页标记
 * - 纯标点碎片并入前句
 */

const ABBREVS = [
  'e\\.g', 'i\\.e', 'et al', 'vs', 'cf', 'Fig', 'Figs', 'No', 'Nos', 'Dr', 'Mr', 'Ms',
  'St', 'Jr', 'Sr', 'Inc', 'Ltd', 'Co', 'Corp', 'approx', 'est', 'resp', 'viz',
  'U\\.S', 'U\\.K', 'U\\.N', 'D\\.C', 'Ph\\.D', 'M\\.D', 'B\\.A', 'M\\.A',
  'Jan', 'Feb', 'Mar', 'Apr', 'Jun', 'Jul', 'Aug', 'Sep', 'Sept', 'Oct', 'Nov', 'Dec',
  'pp', 'p', 'vol', 'ed', 'eds', 'trans', 'rev', 'ca', 'ibid',
];

const ABBREV_RE = new RegExp(`(?:^|\\s)(?:${ABBREVS.join('|')})$`, 'i');

export function splitSentences(text: string): string[] {
  // 预处理：去翻页标记、合并连字符断词（OCR 常见 "cov- erage"）、压缩空白
  let t = text
    .replace(/\(continued\)/gi, ' ')
    .replace(/(\w)- (\w)/g, '$1$2')
    .replace(/\s+/g, ' ')
    .trim();
  if (!t) return [];

  const cuts: number[] = [];
  for (let i = 0; i < t.length; i++) {
    const ch = t[i];
    if (ch !== '.' && ch !== '!' && ch !== '?') continue;
    // 句点后必须跟空白+非空白字符才可能是句末
    if (!/^\s+\S/.test(t.slice(i + 1))) continue;

    const before = t.slice(0, i);
    // 小数点：前后都是数字
    if (ch === '.' && /\d/.test(t[i - 1] ?? '') && /\d/.test(t[i + 2] ?? '')) continue;
    // 缩写：句点前的词在缩写表里
    const lastWord = before.match(/(\S+)$/)?.[1] ?? '';
    if (ch === '.' && ABBREV_RE.test(lastWord)) continue;
    // p<.05 之类：句点前是 < > =
    if (ch === '.' && /[<>=]$/.test(before)) continue;
    // 单字母缩写（"A. Smith"）
    if (ch === '.' && /^[A-Z]$/.test(lastWord)) continue;
    // 编号列表标记（"as follows: 1. excluding..." 中的 "1."）——
    // 只在句点后跟空白+小写/逗号/括号时保护，避免误伤 "in 1991. All..." 这种真句末
    if (ch === '.' && /^\d{1,2}$/.test(lastWord) && /^\s+[a-z,(]/.test(t.slice(i + 1))) continue;

    cuts.push(i + 1);
  }

  const sents: string[] = [];
  let prev = 0;
  for (const c of cuts) {
    sents.push(t.slice(prev, c).trim());
    prev = c;
  }
  if (prev < t.length) sents.push(t.slice(prev).trim());

  // 纯标点/过短碎片并入前句
  const merged: string[] = [];
  for (const s of sents) {
    if (merged.length > 0 && s.length < 3 && !/[a-zA-Z0-9]/.test(s)) {
      merged[merged.length - 1] += ' ' + s;
    } else {
      merged.push(s);
    }
  }
  return merged.filter((s) => s.length > 0);
}
