"""Export classified papers and all detected figure pages without directory scans."""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
import csv
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import shutil
import zipfile

import fitz

LAB_ROOT = Path(__file__).resolve().parents[3]
TOP5 = {"AER", "ECMA", "JPE", "QJE", "REStud"}
VERSION = "3"
PAGE_REVIEW = json.loads(Path(__file__).with_name("reviewed_pages.json").read_text(encoding="utf-8"))
FIGURE_START = re.compile(
    r"^\s*(?:figure\b|fig\.)\s*([a-z]?[-.\s]*\d+[a-z]?|[ivxlcdm]+)(.*)$", re.I
)
TABLE_START = re.compile(r"^\s*table\s*([a-z]?[-.\s]*\d+[a-z]?|[ivxlcdm]+)(.*)$", re.I)
PANEL_START = re.compile(r"^\s*(?:panel\s+[A-Z]|\([A-H]\))\s*[.:]?", re.I)


def json_lines(path: Path):
    with path.open(encoding="utf-8-sig") as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def normalized_doi(value: str | None) -> str:
    return (value or "").strip().lower().removeprefix("https://doi.org/")


def atomic_json(path: Path, data) -> None:
    pending = path.with_suffix(path.suffix + ".part")
    pending.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    pending.replace(path)


def resolve_input(root: Path, relative: str) -> Path:
    result = (root / relative).resolve()
    if not result.is_relative_to(root):
        raise ValueError(f"Input path leaves configured crawler root: {relative}")
    if not result.is_file():
        raise FileNotFoundError(result)
    return result


def select_papers(args):
    empirical = {}
    for record in json_lines(args.annotations):
        paper_type = (record.get("output") or {}).get("paper_type") or {}
        if paper_type.get("primary_type") == "empirical":
            empirical[normalized_doi(record["article_id"].split(":", 1)[1])] = record["article_id"]
    corpus = {}
    for record in json_lines(args.corpus):
        doi = normalized_doi(record.get("doi_normalized") or record.get("doi_raw"))
        if doi in empirical and record.get("selected"):
            corpus[doi] = record
    selected = []
    seen = set()
    for row in json_lines(args.crawler_root / "top_journal_ocr/crosswalk.jsonl"):
        doi = normalized_doi(row.get("doi"))
        if row.get("journal") not in TOP5 or doi not in empirical:
            continue
        if not args.year_from <= int(row.get("year") or 0) <= args.year_to:
            continue
        if args.paper_id and row["paper_id"] not in args.paper_id:
            continue
        if doi in seen:
            raise ValueError(f"Duplicate selected DOI in crosswalk: {doi}")
        seen.add(doi)
        row["article_id"] = empirical[doi]
        row["classification"] = "empirical"
        row["pdf_input"] = str(resolve_input(args.crawler_root, row["l4_pdf_path"]))
        row["layout_input"] = str(resolve_input(args.crawler_root, row["ocr_layout_json_path"]))
        short_title = re.sub(r"[^A-Za-z0-9]+", "_", row.get("title", "")).strip("_")[:55].rstrip("_")
        row["folder"] = row["paper_id"] + "__" + short_title
        selected.append(row)
    if args.paper_id and set(args.paper_id) != {r["paper_id"] for r in selected}:
        raise ValueError("Some requested paper IDs do not satisfy the selected classified/year scope")
    missing = []
    if not args.paper_id:
        for doi, record in corpus.items():
            if doi not in seen and args.year_from <= int(record.get("year") or 0) <= args.year_to:
                missing.append({"article_id": record["article_id"], "title": record["title"],
                                "year": record["year"], "doi": doi})
    return sorted(selected, key=lambda r: (r["journal"], r["year"], r["paper_id"])), missing


def block_text(block):
    return " ".join(span.get("content", "") for line in block.get("lines", [])
                    for span in line.get("spans", []))


def nested_boxes(block):
    if block.get("type", "").endswith("caption") and TABLE_START.match(block_text(block)):
        return
    if block.get("bbox"):
        yield block["bbox"]
    for child in block.get("blocks", []):
        yield from nested_boxes(child)


def graphic_blocks(block):
    if block.get("type") in {"image", "chart", "image_body", "chart_body", "table"}:
        yield block
    else:
        for child in block.get("blocks", []):
            yield from graphic_blocks(child)


def strong_figure_label(text, pattern=FIGURE_START):
    match = pattern.match(text.strip())
    if not match:
        return None
    tail = match.group(2).strip()
    # A numbered heading, not a running-text sentence such as "Figure 1 shows ...".
    if not tail or tail[0] in ".:—–-" or text.strip().isupper():
        return re.sub(r"\s+", "", match.group(1)).upper()
    return None


def pdf_caption_lines(page):
    figures, tables, panels = [], [], []
    text = page.get_text("dict", flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES)
    for block in text["blocks"]:
        for line_index, line in enumerate(block.get("lines", [])):
            value = "".join(span.get("text", "") for span in line.get("spans", []))
            label = strong_figure_label(value)
            table_label = strong_figure_label(value, TABLE_START)
            if label and line_index == 0:
                figures.append({"label": label, "bbox": line["bbox"], "text": value})
            elif table_label and line_index == 0:
                tables.append({"label": table_label, "bbox": line["bbox"], "text": value})
            elif PANEL_START.match(value):
                panels.append(line["bbox"])
    return figures, tables, panels


def caption_kinds(block):
    kinds = set()
    for child in block.get("blocks", []):
        if child.get("type", "").endswith("caption"):
            value = block_text(child).strip()
            if FIGURE_START.match(value):
                kinds.add("figure")
            if TABLE_START.match(value):
                kinds.add("table")
        kinds.update(caption_kinds(child))
    return kinds


def valid_box(box):
    return len(box) == 4 and all(math.isfinite(float(v)) for v in box) and box[2] > box[0] and box[3] > box[1]


def export_one(row, output_root, dpi, refresh=False):
    folder = Path(output_root) / row["folder"]
    info_path = folder / "paper_info.json"
    pdf_source = Path(row["pdf_input"])
    previous_images = []
    if info_path.is_file():
        info = json.loads(info_path.read_text(encoding="utf-8"))
        if (info.get("export_version") == VERSION and info.get("dpi") == dpi
                and info.get("paper_id") == row["paper_id"]
                and (folder / "paper.pdf").is_file()
                and (folder / "paper.pdf").stat().st_size == pdf_source.stat().st_size
                and all((folder / image["file"]).is_file()
                        and (folder / image["file"]).stat().st_size == image["bytes"]
                        for image in info.get("images", []))):
            return info
        if not (refresh and info.get("paper_id") == row["paper_id"]
                and info.get("export_version") in {"2", VERSION}):
            raise RuntimeError(f"Incomplete or incompatible existing export: {folder}")
        previous_images = info.get("images", [])
    images_dir = folder / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    layout_path = Path(row["layout_input"])
    if layout_path.stat().st_size > 12_000_000:
        raise ValueError(f"Layout exceeds inspected size range: {layout_path}")
    layout = json.loads(layout_path.read_text(encoding="utf-8-sig"))
    by_page = {int(p["page_idx"]): p for p in layout.get("pdf_info", [])}
    images = []
    total_graphics = 0
    recovered_tables = []
    excluded_tables = []
    reviewed_pages = PAGE_REVIEW.get(row["paper_id"], [])
    omitted_pages = {r["pdf_page"] for r in reviewed_pages}
    with fitz.open(pdf_source) as pdf:
        if set(by_page) != set(range(len(pdf))):
            raise ValueError(f"PDF/layout page mismatch: {row['paper_id']}")
        page_count = len(pdf)
        for page_idx, page in enumerate(pdf):
            if page_idx + 1 in omitted_pages:
                continue
            layout_page = by_page[page_idx]
            possible = []
            seen_boxes = set()
            for block in layout_page.get("para_blocks", []) + layout_page.get("discarded_blocks", []):
                for item in graphic_blocks(block):
                    key = (item.get("type"), tuple(item.get("bbox", [])))
                    if key not in seen_boxes:
                        seen_boxes.add(key)
                        possible.append(item)
            captions, table_captions, panels = pdf_caption_lines(page)
            candidates = []
            page_has_figure = bool(captions) or any("figure" in caption_kinds(b) for b in possible)
            for item in possible:
                kinds = caption_kinds(item)
                if item.get("type") == "table":
                    if "figure" in kinds and "table" not in kinds:
                        candidates.append(item)
                        recovered_tables.append({"pdf_page": page_idx + 1, "bbox": item.get("bbox"),
                                                 "reason": "OCR table block has a Figure caption"})
                    continue
                if ("table" in kinds and "figure" not in kinds) or (table_captions and not page_has_figure):
                    excluded_tables.append({"pdf_page": page_idx + 1, "bbox": item.get("bbox"),
                                            "type": item.get("type"),
                                            "reason": "Table caption on block" if "table" in kinds else "Table page without Figure heading",
                                            "table_labels": [t["label"] for t in table_captions]})
                    continue
                candidates.append(item)
            if not candidates and not captions:
                continue
            total_graphics += len(candidates)
            reasons = []
            if not candidates:
                reasons.append("PDF figure heading found without OCR graphic block; full page retained")
            lw, lh = layout_page["page_size"]
            if abs(page.rect.width - lw) > 2 or abs(page.rect.height - lh) > 2 or page.rotation:
                reasons.append("Page coordinate difference or rotation; full page retained")
            raw_boxes = [box for block in candidates for box in nested_boxes(block)]
            if any(not valid_box(box) for box in raw_boxes):
                reasons.append("Invalid OCR box; full page retained")
            if reasons:
                clip = page.rect
            else:
                sx, sy = page.rect.width / lw, page.rect.height / lh
                rectangles = [fitz.Rect(b[0] * sx, b[1] * sy, b[2] * sx, b[3] * sy) for b in raw_boxes]
                rectangles += [fitz.Rect(c["bbox"]) for c in captions]
                clip = fitz.Rect(rectangles[0])
                for rect in rectangles[1:]:
                    clip |= rect
                for panel_box in panels:
                    rect = fitz.Rect(panel_box)
                    if rect.y1 >= clip.y0 - 25 and rect.y0 <= clip.y1 + 25:
                        clip |= rect
                clip = fitz.Rect(clip.x0 - 6, clip.y0 - 6, clip.x1 + 6, clip.y1 + 6) & page.rect
                if clip.is_empty:
                    raise ValueError(f"Empty figure region: {row['paper_id']} page {page_idx + 1}")
            filename = f"images/page_{page_idx + 1:03d}.png"
            destination = folder / filename
            temporary = destination.with_name(destination.stem + ".part.png")
            pixmap = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72), clip=clip, alpha=False)
            pixmap.set_dpi(dpi, dpi)
            pixmap.save(temporary)
            temporary.replace(destination)
            images.append({"file": filename, "pdf_page": page_idx + 1,
                           "graphic_blocks": len(candidates), "width": pixmap.width, "height": pixmap.height,
                           "bytes": destination.stat().st_size, "crop_pdf_points": list(clip),
                           "figure_labels": sorted({c["label"] for c in captions}),
                           "full_page_reasons": reasons})
    temporary_pdf = folder / "paper.pdf.part"
    shutil.copyfile(pdf_source, temporary_pdf)
    temporary_pdf.replace(folder / "paper.pdf")
    info = {"paper_id": row["paper_id"], "article_id": row["article_id"], "title": row["title"],
            "journal": row["journal"], "year": row["year"], "doi": row["doi"],
            "doi_url": "https://doi.org/" + row["doi"], "classification": "empirical",
            "classification_source": "abstract_structure/run_20260909_v03_full/annotation_flash",
            "export_version": VERSION, "dpi": dpi, "folder": row["folder"],
            "pdf_pages": page_count, "pdf_bytes": pdf_source.stat().st_size,
            "graphic_blocks": total_graphics, "image_unit": "All detected figures on one PDF page",
            "recovered_figure_table_blocks": recovered_tables,
            "excluded_table_graphic_blocks": excluded_tables,
            "reviewed_pages_without_figure_body": reviewed_pages,
            "images": images, "status": "exported" if images else "no_figures_detected"}
    current_files = {i["file"] for i in images}
    for old in previous_images:
        if old["file"] not in current_files:
            stale = (folder / old["file"]).resolve()
            if stale.parent != images_dir.resolve() or stale.suffix != ".png":
                raise ValueError(f"Unexpected old generated image path: {stale}")
            stale.unlink(missing_ok=True)
    atomic_json(info_path, info)
    return info


def write_package_index(output, infos, missing, args):
    columns = ["folder", "journal", "year", "title", "doi", "classification", "image_count", "status"]
    with (output / "papers.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for info in infos:
            writer.writerow({**{k: info[k] for k in columns if k != "image_count"},
                             "image_count": len(info["images"])})
    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(), "export_version": VERSION,
        "year_from": args.year_from, "year_to": args.year_to, "paper_type": "empirical",
        "selection": "Top5 AI-classified empirical papers matched to OCR crosswalk; no field/figure selection",
        "papers": len(infos), "by_journal": dict(Counter(p["journal"] for p in infos)),
        "png_images": sum(len(p["images"]) for p in infos),
        "graphic_blocks": sum(p["graphic_blocks"] for p in infos),
        "full_page_images": sum(bool(i["full_page_reasons"]) for p in infos for i in p["images"]),
        "recovered_figure_table_blocks": sum(len(p["recovered_figure_table_blocks"]) for p in infos),
        "excluded_table_graphic_blocks": sum(len(p["excluded_table_graphic_blocks"]) for p in infos),
        "reviewed_pages_without_figure_body": [dict(paper_id=p["paper_id"], **r)
             for p in infos for r in p.get("reviewed_pages_without_figure_body", [])],
        "papers_without_detected_figures": [p["paper_id"] for p in infos if not p["images"]],
        "pdf_bytes": sum(p["pdf_bytes"] for p in infos),
        "png_bytes": sum(i["bytes"] for p in infos for i in p["images"]),
        "classified_in_period_not_matched_to_ocr": missing,
    }
    atomic_json(output / "summary.json", summary)
    text = f"""# Top5 实证论文与图片资料包

范围：{args.year_from}–{args.year_to} 年，现有 AI 分类为 empirical，且能匹配现有 OCR 索引的 Top5 论文。
共 {len(infos)} 篇论文，{summary['png_images']} 张 PNG，覆盖 {summary['graphic_blocks']} 个 OCR 图块。
没有按研究领域、图形类型或图形质量进一步筛选。

每篇论文一个文件夹：
- `paper.pdf`：原始 PDF，内容未改动。
- `images/page_NNN.png`：该 PDF 第 NNN 页的图片，{args.dpi} dpi。
- `paper_info.json`：标题、期刊、年份、DOI、AI 分类，以及图片和 PDF 页码的对应关系。

图片按原 PDF 页汇集，保留多面板的原始排列；同页有多张图时一起保存在一张 PNG 中。
按论文的 Figure/Table 标题区分：回收误标为 table 的 Figure，排除明确编号为 Table 的图块。
图片周围可能保留标题、注释或少量正文。若只发现图题、OCR 未识别出图块，或坐标异常，
保留整页图片，具体原因记在 paper_info.json。PNG 数量不等于论文中的 Figure 数量。
PDF 内的正文图和附录图均在导出范围内；独立 online appendix 未另行收集。

`papers.csv` 可用 Excel 打开，查看全部论文与图片数量。
{len(summary['papers_without_detected_figures'])} 篇未检测到 Figure 的论文仍保留原 PDF；详见 summary.json。
图片来自 OCR 定位与 PDF 图题检查，原 PDF 保留完整内容以便核对。
逐页核查了 OCR 未识别图块的补漏候选；正文 Figure 引用和仅有续页图注的页面不另导出 PNG。
核查记录见 paper_info.json 的 reviewed_pages_without_figure_body。
已发现 qje_2026_qjaf051 的 PDF 第 45 页有 Figure XI 标题，但该页图形区域为空；
这处源 PDF 缺图未补造，也未将其图注页算作图片。

已有 AI 标注但未匹配 OCR 的同期记录不在此次已确认的匹配子集内，清单保存在 summary.json。
本包没有重新运行论文分类，也没有生成绘图代码。
"""
    (output / "README.md").write_text(text, encoding="utf-8")
    return summary


def create_archive(output, infos):
    archive = output.parent / (output.name + ".zip")
    pending = archive.with_suffix(".zip.part")
    files = [output / "README.md", output / "papers.csv", output / "summary.json"]
    for info in infos:
        folder = output / info["folder"]
        files += [folder / "paper.pdf", folder / "paper_info.json"]
        files += [folder / i["file"] for i in info["images"]]
    with zipfile.ZipFile(pending, "w", allowZip64=True, compression=zipfile.ZIP_DEFLATED, compresslevel=1) as zipped:
        for index, path in enumerate(files, start=1):
            zipped.write(path, arcname=output.name + "/" + path.relative_to(output).as_posix(),
                         compress_type=zipfile.ZIP_STORED if path.suffix == ".png" else zipfile.ZIP_DEFLATED,
                         compresslevel=1)
            if index % 500 == 0:
                print(json.dumps({"archive_files_written": index, "total_files": len(files)}), flush=True)
        for info in infos:
            if not info["images"]:
                zipped.writestr(output.name + "/" + info["folder"] + "/images/", b"")
    print("Checking ZIP CRC for all archived files", flush=True)
    with zipfile.ZipFile(pending) as zipped:
        bad = zipped.testzip()
        if bad:
            raise RuntimeError(f"ZIP CRC failed: {bad}")
        regular = [entry for entry in zipped.infolist() if not entry.is_dir()]
        if len(regular) != len(files):
            raise RuntimeError("ZIP file count mismatch")
    pending.replace(archive)
    return {"archive": str(archive), "bytes": archive.stat().st_size,
            "files": len(files), "crc_checked": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--crawler-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, default=LAB_ROOT / "data/processed/abstract_structure/run_20260909_v03_full/annotation_flash/annotations.jsonl")
    parser.add_argument("--corpus", type=Path, default=LAB_ROOT / "data/processed/abstract_structure/run_20260908_a/corpus_manifest.jsonl")
    parser.add_argument("--year-from", type=int, default=2021)
    parser.add_argument("--year-to", type=int, default=2026)
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--paper-id", action="append", default=[])
    parser.add_argument("--zip", action="store_true")
    parser.add_argument("--refresh-generated", action="store_true",
                        help="Regenerate this export's recognized old output; input PDFs remain read-only")
    args = parser.parse_args()
    args.crawler_root = args.crawler_root.resolve()
    args.output_root = args.output_root.resolve()
    if args.output_root.is_relative_to(args.crawler_root):
        raise ValueError("Output must be outside the upstream crawler repository")
    if args.year_from > args.year_to or not 72 <= args.dpi <= 600 or not 1 <= args.workers <= 16:
        raise ValueError("Invalid year, dpi or workers argument")
    selected, missing = select_papers(args)
    if not selected:
        raise ValueError("No papers satisfy selection")
    args.output_root.mkdir(parents=True, exist_ok=True)
    print(json.dumps({"selected_papers": len(selected), "by_journal": dict(Counter(r['journal'] for r in selected)),
                      "classified_not_in_ocr": len(missing), "output": str(args.output_root)}), flush=True)
    infos, failures = [], []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        tasks = {pool.submit(export_one, row, str(args.output_root), args.dpi, args.refresh_generated): row for row in selected}
        for future in as_completed(tasks):
            row = tasks[future]
            try:
                infos.append(future.result())
            except Exception as exc:
                failures.append({"paper_id": row["paper_id"], "error": repr(exc)})
                print(json.dumps({"failure": failures[-1]}), flush=True)
            if (len(infos) + len(failures)) % 20 == 0 or len(selected) < 20:
                print(json.dumps({"completed": len(infos), "failed": len(failures), "total": len(selected),
                                  "images": sum(len(p['images']) for p in infos)}), flush=True)
    if failures:
        failure_path = args.output_root.parent / (args.output_root.name + "_failures.json")
        atomic_json(failure_path, failures)
        raise RuntimeError(f"{len(failures)} paper exports failed; archive not created; see {failure_path}")
    infos.sort(key=lambda p: (p["journal"], p["year"], p["paper_id"]))
    summary = write_package_index(args.output_root, infos, missing, args)
    print(json.dumps({"summary": {k: v for k, v in summary.items() if k != 'classified_in_period_not_matched_to_ocr'}}, ensure_ascii=False), flush=True)
    if args.zip:
        print(json.dumps(create_archive(args.output_root, infos)), flush=True)


if __name__ == "__main__":
    main()
