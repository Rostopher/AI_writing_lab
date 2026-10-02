"""extract_table_units.py — 从 layout.json 抽取每篇论文的表单元。

表单元 = {序号, table_caption 表标题, body_head 表格主体(行标签/列头), table_footnote 表注}
供后续 LLM 标注表注职责（roles）、长度、跨表复用策略。

输入：
  - 实证筛选：abstract_structure 标注的 paper_type.primary_type == "empirical"
  - OCR：playwright_crawler top_journal_ocr，经 crosswalk.jsonl 定位（不递归扫目录）
输出：outputs/table_notes/table_units.jsonl，每行一篇论文。

用法：
    python modules/academic_writing/extract_table_units.py [--top5-only] [--year-from 2021] [--year-to 2026] [--limit 50]
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

# ---------- 路径 ----------
LAB_ROOT = Path(__file__).resolve().parents[2]
ANN_PATH = LAB_ROOT / "data/processed/abstract_structure/run_20260909_v03_full/annotation_flash/annotations.jsonl"
CRAWLER_ROOT = Path(r"F:/codeF/llm_projects/playwright_crawler")
OCR_ROOT = CRAWLER_ROOT / "top_journal_ocr"
CROSSWALK = OCR_ROOT / "crosswalk.jsonl"

TOP5 = {"QJE", "AER", "JPE", "ECMA", "REStud"}
MAX_BODY_CELLS = 30  # 表格主体进 prompt 的非空 cell 上限（截断防超长）

# body 之后的 table_caption 基本是 MinerU 误标的表注（probe_layout_table_structure 证实）；
# 但偶尔是混进来的下一个浮动体标题（"FIGURE 1. ..." / "TABLE 4 ..."），这种要丢掉
NEW_FLOAT_TITLE = re.compile(r"^\s*(table|figure|fig\.?|panel|appendix)\s*[\divxlc]", re.I)
TAG_RE = re.compile(r"<[^>]+>")

# 游离注回收（probe_detached_notes 证实）：注被标成 table 块之后的独立 text 块，
# 以 Notes:/Note.—/* Significant 等开头。乱码容错："CONTINUED" 常被 OCR 拆成 "ONTINUE"
NOTE_START = re.compile(
    r"^(notes?\s*[:.—]|\*\s*(significant|p\s*[<≤])|significant\s+at\s+the)", re.I
)
CONTINUED_RE = re.compile(r"ONTINU", re.I)
MAX_NOTE_GAP_PT = 80  # 同页游离注块与表底的纵向间距上限


def load_crosswalk() -> dict[str, dict]:
    """doi -> crosswalk row。"""
    by_doi = {}
    with CROSSWALK.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("doi"):
                by_doi[r["doi"]] = r
    return by_doi


def load_empirical_ids() -> set[str]:
    """abstract_structure 标注里 primary_type=='empirical' 的 article_id 集合。"""
    ids = set()
    with ANN_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            pt = (r.get("output") or {}).get("paper_type") or {}
            if pt.get("primary_type") == "empirical":
                ids.add(r["article_id"])  # e.g. "AER:10.1257/aer.xxx"
    return ids


def cell_texts(html: str) -> list[str]:
    """从 table_body 的 <table> HTML 提取非空 cell 文本（去标签、strip），截断到上限。"""
    cells = re.findall(r"<td[^>]*>(.*?)</td>", html, flags=re.S)
    out = []
    for c in cells:
        t = re.sub(r"<[^>]+>", "", c)
        t = re.sub(r"\s+", " ", t).strip()
        if t:
            out.append(t)
        if len(out) >= MAX_BODY_CELLS:
            break
    return out


def block_text(block: dict) -> str:
    return " ".join(
        sp.get("content", "")
        for ln in block.get("lines", [])
        for sp in ln.get("spans", [])
    ).strip()


def _clean_caption(s: str) -> str:
    return TAG_RE.sub("", s or "").replace(" ", "").upper()


def _parse_table_block(b: dict, page_idx: int, pi: int, bi: int) -> dict:
    """单个 table block -> 原始表单元（caption/footnote 归属规则见 extract_tables docstring）。"""
    subs = b.get("blocks", [])
    body_pos = [i for i, sb in enumerate(subs) if sb.get("type") == "table_body"]
    last_body = body_pos[-1] if body_pos else -1
    caption_parts, footnote_parts, body_cells = [], [], []
    footnote_source = None
    for i, sb in enumerate(subs):
        st = sb.get("type")
        if st == "table_caption":
            txt = block_text(sb)
            if last_body >= 0 and i > last_body:
                if txt and not NEW_FLOAT_TITLE.match(TAG_RE.sub("", txt)):
                    footnote_parts.append(txt)
                    footnote_source = "after_body_caption"
            else:
                caption_parts.append(txt)
        elif st == "table_footnote":
            footnote_parts.append(block_text(sb))
            footnote_source = footnote_source or "inline"
        elif st == "table_body":
            for ln in sb.get("lines", []):
                for sp in ln.get("spans", []):
                    html = sp.get("html")
                    if html:
                        body_cells.extend(cell_texts(html))
    return {
        "page": page_idx,
        "caption": " ".join(p for p in caption_parts if p),
        "body_head": body_cells[:MAX_BODY_CELLS],
        "footnote": " ".join(p for p in footnote_parts if p).strip(),
        "footnote_source": footnote_source,
        "_pi": pi, "_bi": bi,
        "_bbox_bottom": (b.get("bbox") or [0, 0, 0, 0])[3],
    }


def extract_tables(layout: dict) -> list[dict]:
    """从一篇 layout.json 抽所有 table block -> 表单元列表。

    三步（每步都由 probe 证实，见 modules/academic_writing/probe_*.py）：
    1. 块内归属：首个 table_body 之前的 table_caption → 标题；最后一个 body 之后的
       caption → 误标表注（浮动体标题开头的丢弃）；table_footnote → footnote
    2. 碎片合并：同页相邻、后者无 caption 的表块合并（panel 被拆）；caption 含
       "CONTINUED"（含乱码 ONTINUE）的跨页续表并入前一张
    3. 游离注回收：仍无注的表，向后看同页 2 块 + 下页首块，Notes:/Note.— 开头的
       text 块并入并消费（防止两块表抢同一条注）
    """
    pages = layout.get("pdf_info", [])
    raw = []
    for pi, page in enumerate(pages):
        for bi, b in enumerate(page.get("para_blocks", [])):
            if b.get("type") == "table":
                raw.append(_parse_table_block(b, page.get("page_idx"), pi, bi))

    # 第 2 步：碎片合并
    merged: list[dict] = []
    for t in raw:
        if merged:
            prev = merged[-1]
            same_page_split = (
                t["_pi"] == prev["_pi"] and t["_bi"] == prev["_bi"] + 1
                and not t["caption"]
            )
            continued = CONTINUED_RE.search(_clean_caption(t["caption"])) is not None
            if same_page_split or continued:
                prev["body_head"] = (prev["body_head"] + t["body_head"])[:MAX_BODY_CELLS]
                if t["footnote"]:
                    prev["footnote"] = (prev["footnote"] + " " + t["footnote"]).strip()
                    prev["footnote_source"] = prev["footnote_source"] or t["footnote_source"]
                prev["_pi"], prev["_bi"] = t["_pi"], t["_bi"]
                prev["_bbox_bottom"] = t["_bbox_bottom"]
                if continued and not prev["caption"]:
                    prev["caption"] = t["caption"]
                continue
        merged.append(t)

    # 第 3 步：游离注回收
    consumed: set[tuple[int, int]] = set()
    for t in merged:
        if t["footnote"]:
            continue
        pi, bi = t["_pi"], t["_bi"]
        cands = []
        pb = pages[pi].get("para_blocks", [])
        for k in (bi + 1, bi + 2):
            if k < len(pb) and (pi, k) not in consumed:
                cands.append((pi, k, pb[k], True))
        if pi + 1 < len(pages):
            npb = pages[pi + 1].get("para_blocks", [])
            if npb and (pi + 1, 0) not in consumed:
                cands.append((pi + 1, 0, npb[0], False))
        for cpi, cbi, c, same_page in cands:
            if c.get("type") != "text":
                continue
            txt = TAG_RE.sub("", block_text(c)).strip()
            if not NOTE_START.match(txt):
                continue
            if same_page:
                gap = (c.get("bbox") or [0, 0, 0, 0])[1] - t["_bbox_bottom"]
                if gap > MAX_NOTE_GAP_PT:
                    continue
            t["footnote"] = txt
            t["footnote_source"] = "detached_text"
            consumed.add((cpi, cbi))
            break

    for i, t in enumerate(merged):
        t["idx"] = i + 1
        for k in ("_pi", "_bi", "_bbox_bottom"):
            t.pop(k, None)
    return merged


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year-from", type=int, default=2021)
    ap.add_argument("--year-to", type=int, default=2026)
    ap.add_argument("--top5-only", action="store_true", default=True)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    out_path = Path(args.out).resolve() if args.out else (
        Path(__file__).resolve().parent / "outputs" / "table_notes" / "table_units.jsonl"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)

    by_doi = load_crosswalk()
    emp_ids = load_empirical_ids()
    print(f"empirical ids: {len(emp_ids)}; crosswalk doi index: {len(by_doi)}")

    n_written = 0
    n_papers_matched = 0
    with out_path.open("w", encoding="utf-8") as w:
        for article_id in sorted(emp_ids):
            journal, doi = article_id.split(":", 1)
            if args.top5_only and journal not in TOP5:
                continue
            cw = by_doi.get(doi)
            if not cw or not cw.get("year"):
                continue
            if not (args.year_from <= cw["year"] <= args.year_to):
                continue
            rel = cw.get("ocr_layout_json_path")
            if not rel:
                continue
            lj = (OCR_ROOT.parent / rel).resolve()
            if not lj.exists():
                continue
            n_papers_matched += 1
            try:
                layout = json.load(lj.open(encoding="utf-8"))
            except Exception as e:  # noqa: BLE001
                print(f"  ! parse fail {cw['paper_id']}: {e}")
                continue
            tables = extract_tables(layout)
            has_note = any(t["footnote"] for t in tables)
            w.write(json.dumps({
                "paper_id": cw["paper_id"],
                "journal": journal,
                "year": cw["year"],
                "doi": doi,
                "title": cw.get("title", ""),
                "n_tables": len(tables),
                "has_any_note": has_note,
                "tables": tables,
            }, ensure_ascii=False) + "\n")
            n_written += 1
            if args.limit and n_written >= args.limit:
                break

    print(f"papers matched (empirical, top5, {args.year_from}-{args.year_to}): {n_papers_matched}")
    print(f"wrote {n_written} papers -> {out_path}")


if __name__ == "__main__":
    main()
