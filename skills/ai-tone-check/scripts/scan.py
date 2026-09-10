#!/usr/bin/env python3
"""扫描文本中的「AI 味」标记：词表 + 句式正则，纯标准库零依赖。

用法:
    python scan.py <文件> [--json]
    cat draft.md | python scan.py -

词表位于 ../wordlists/*.txt，格式: 匹配串<TAB>类别[<TAB>备注]，
re: 前缀表示正则；纯英文单词自动加词边界，其余按字面子串匹配。
命中是候选信号，不是 verdict，需结合文体人工/agent 判断。
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

WORDLIST_DIR = Path(__file__).resolve().parent.parent / "wordlists"


def load_entries():
    entries = []
    for path in sorted(WORDLIST_DIR.glob("*.txt")):
        for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            pattern = parts[0].strip()
            category = parts[1].strip() if len(parts) > 1 and parts[1].strip() else "未分类"
            note = parts[2].strip() if len(parts) > 2 else ""
            try:
                entries.append((compile_pattern(pattern), pattern, category, note, path.name))
            except re.error as e:
                print(f"[词表错误] {path.name}:{lineno} 无效正则 {pattern!r}: {e}", file=sys.stderr)
    return entries


def compile_pattern(pattern):
    if pattern.startswith("re:"):
        return re.compile(pattern[3:], re.IGNORECASE)
    if re.fullmatch(r"[A-Za-z][A-Za-z'~-]*", pattern):
        return re.compile(r"\b" + re.escape(pattern) + r"\b", re.IGNORECASE)
    return re.compile(re.escape(pattern), re.IGNORECASE)


def scan(text, entries):
    raw_hits = []
    lines = text.splitlines()
    for regex, pattern, category, note, source in entries:
        for lineno, line in enumerate(lines, 1):
            for m in regex.finditer(line):
                raw_hits.append((lineno, m.start(), m.end(), {
                    "line": lineno,
                    "category": category,
                    "pattern": pattern,
                    "matched": m.group(0),
                    "context": line.strip()[:120],
                    "note": note,
                    "source": source,
                }))
    # 同一行内被更长命中完全包含的短命中去重（如 "worth noting that" ⊂ "it's worth noting"）
    hits = []
    for lineno, start, end, hit in raw_hits:
        contained = any(
            l2 == lineno and (s2, e2) != (start, end) and s2 <= start and end <= e2
            for l2, s2, e2, _ in raw_hits
        )
        if not contained:
            hits.append(hit)
    hits.sort(key=lambda h: (h["line"], h["category"]))
    return hits


def main():
    ap = argparse.ArgumentParser(description="扫描文本中的 AI 味标记")
    ap.add_argument("file", help="目标文件路径，'-' 表示标准输入")
    ap.add_argument("--json", action="store_true", help="输出 JSON 格式")
    args = ap.parse_args()

    if args.file == "-":
        text = sys.stdin.read()
    else:
        text = Path(args.file).read_text(encoding="utf-8")

    entries = load_entries()
    hits = scan(text, entries)

    if args.json:
        print(json.dumps({"total": len(hits), "hits": hits}, ensure_ascii=False, indent=2))
        return

    if not hits:
        print("未命中任何 AI 味标记。注意：词表只覆盖确定性信号，")
        print("空泛判断、缺少具体信息、作者声音等维度仍需通读判断。")
        return

    for h in hits:
        note = f"  # {h['note']}" if h["note"] else ""
        print(f"[{h['category']}] 第{h['line']}行: \"{h['matched']}\"{note}")
        print(f"    上下文: {h['context']}")

    print("\n---- 分类统计 ----")
    for category, count in Counter(h["category"] for h in hits).most_common():
        print(f"{category}: {count}")
    print(f"\n共 {len(hits)} 处候选命中。命中 ≠ 错误：请区分 AI 痕迹与文体偏好，")
    print("并继续检查扫描覆盖不到的维度（空泛判断、缺少具体信息、作者声音一致性）。")


if __name__ == "__main__":
    main()
