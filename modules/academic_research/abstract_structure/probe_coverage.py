"""覆盖普查：遍历五刊 2015–2026 全部期目录，按期统计文章数与摘要可得性。

输出（默认 data/processed/abstract_structure/probe_coverage_20260908/）：
- coverage_issues.csv   每行一期
- coverage_summary.json 分刊汇总 + 总计
- 控制台汇总表

摘要可得性按各刊抽取路径实际尝试（复用 extract_abstracts 的适配器），
不是只看字段是否存在。
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_abstracts import (  # noqa: E402
    EXCLUDED_ISSUES,
    EXTRACTORS,
    JOURNALS,
    OUTPUT_ROOT,
    UPSTREAM_ROOT,
    YEAR_MAX,
    YEAR_MIN,
    classify_type,
    iter_issue_dirs,
)

DEFAULT_OUT_DIRNAME = "probe_coverage_20260908"


def probe(upstream_root: Path, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []

    for journal in JOURNALS:
        for issue_name, issue_path, year, month in iter_issue_dirs(upstream_root, journal):
            row = {
                "journal": journal,
                "issue_dir": issue_name,
                "year": year,
                "month": month,
                "n_articles_total": "",
                "n_front_matter": "",
                "n_excluded_type": "",
                "n_with_abstract": "",
                "n_missing_abstract": "",
                "anomalies": "",
            }
            anomaly_flags: list[str] = []

            if issue_name in EXCLUDED_ISSUES:
                reason = EXCLUDED_ISSUES[issue_name]
                is_pp = "Papers & Proceedings" in reason
                anomaly_flags.append("pp_issue_excluded" if is_pp else "duplicate_dir_excluded")
                # 仍尝试读取期级元数据以报告文章数（AER201804_4-5 无该文件）
                meta = issue_path / "article_metadata.json"
                if meta.exists():
                    try:
                        arts, ext_anom = EXTRACTORS[journal](issue_name, issue_path, upstream_root)
                        row["n_articles_total"] = len(arts)
                        row["n_excluded_type"] = len(arts)  # 整期排除
                        anomaly_flags.extend(ext_anom)
                    except Exception as e:  # 普查不因单期失败中断，显式记录
                        anomaly_flags.append(f"issue_read_error:{type(e).__name__}:{e}")
                else:
                    anomaly_flags.append("missing_issue_file:article_metadata.json")
                row["anomalies"] = ";".join(anomaly_flags)
                rows.append(row)
                continue

            meta = issue_path / "article_metadata.json"
            if not meta.exists():
                row["anomalies"] = "missing_issue_file:article_metadata.json"
                rows.append(row)
                continue

            try:
                arts, ext_anom = EXTRACTORS[journal](issue_name, issue_path, upstream_root)
                anomaly_flags.extend(ext_anom)
            except Exception as e:
                row["anomalies"] = f"issue_read_error:{type(e).__name__}:{e}"
                rows.append(row)
                continue

            n_front = 0
            n_excluded = 0
            n_with_abs = 0
            n_missing = 0
            for a in arts:
                exclusion, _signals = classify_type(a["title"], a.get("is_front_matter"))
                if exclusion and exclusion.startswith("front_matter"):
                    n_front += 1
                if exclusion:
                    n_excluded += 1
                if a["extraction_status"] == "ok":
                    n_with_abs += 1
                else:
                    n_missing += 1
                    if a["extraction_status"] == "extraction_error":
                        anomaly_flags.append(
                            f"extraction_error:{a.get('source_stable_id')}"
                        )
            row.update(
                n_articles_total=len(arts),
                n_front_matter=n_front,
                n_excluded_type=n_excluded,
                n_with_abstract=n_with_abs,
                n_missing_abstract=n_missing,
                anomalies=";".join(anomaly_flags),
            )
            rows.append(row)

    csv_path = out_dir / "coverage_issues.csv"
    fieldnames = ["journal", "issue_dir", "year", "month", "n_articles_total",
                  "n_front_matter", "n_excluded_type", "n_with_abstract",
                  "n_missing_abstract", "anomalies"]
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    # 汇总
    def _sum(rs, key):
        return sum(r[key] for r in rs if isinstance(r[key], int))

    summary: dict = {"year_window": [YEAR_MIN, YEAR_MAX], "journals": {}, "total": {}}
    for journal in JOURNALS:
        rs = [r for r in rows if r["journal"] == journal]
        summary["journals"][journal] = {
            "n_issues": len(rs),
            "n_issues_missing_metadata": sum(
                1 for r in rs if "missing_issue_file" in str(r["anomalies"])
            ),
            "n_issues_excluded_whole": sum(
                1 for r in rs if "excluded" in str(r["anomalies"])
                and ("pp_issue_excluded" in str(r["anomalies"])
                     or "duplicate_dir_excluded" in str(r["anomalies"]))
            ),
            "n_articles_total": _sum(rs, "n_articles_total"),
            "n_front_matter": _sum(rs, "n_front_matter"),
            "n_excluded_type": _sum(rs, "n_excluded_type"),
            "n_with_abstract": _sum(rs, "n_with_abstract"),
            "n_missing_abstract": _sum(rs, "n_missing_abstract"),
        }
    allj = summary["journals"].values()
    summary["total"] = {
        k: sum(s[k] for s in allj)
        for k in ("n_issues", "n_issues_missing_metadata", "n_issues_excluded_whole",
                  "n_articles_total", "n_front_matter", "n_excluded_type",
                  "n_with_abstract", "n_missing_abstract")
    }
    with open(out_dir / "coverage_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    return summary


def print_summary(summary: dict) -> None:
    header = (f"{'期刊':<8}{'期数':>5}{'缺元数据':>8}{'整期排除':>8}{'文章数':>7}"
              f"{'前置页':>7}{'排除类型':>8}{'有摘要':>7}{'缺摘要':>7}")
    print(header)
    print("-" * len(header))
    for j, s in summary["journals"].items():
        print(f"{j:<8}{s['n_issues']:>5}{s['n_issues_missing_metadata']:>8}"
              f"{s['n_issues_excluded_whole']:>8}{s['n_articles_total']:>7}"
              f"{s['n_front_matter']:>7}{s['n_excluded_type']:>8}"
              f"{s['n_with_abstract']:>7}{s['n_missing_abstract']:>7}")
    t = summary["total"]
    print("-" * len(header))
    print(f"{'TOTAL':<8}{t['n_issues']:>5}{t['n_issues_missing_metadata']:>8}"
          f"{t['n_issues_excluded_whole']:>8}{t['n_articles_total']:>7}"
          f"{t['n_front_matter']:>7}{t['n_excluded_type']:>8}"
          f"{t['n_with_abstract']:>7}{t['n_missing_abstract']:>7}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="五刊摘要覆盖普查")
    ap.add_argument("--upstream-root", type=Path, default=UPSTREAM_ROOT)
    ap.add_argument("--out-dir", type=Path, default=OUTPUT_ROOT / DEFAULT_OUT_DIRNAME)
    args = ap.parse_args(argv)
    if args.upstream_root is None:
        ap.error("需要 --upstream-root 或环境变量 ABSTRACT_STRUCTURE_UPSTREAM_ROOT")
    summary = probe(args.upstream_root, args.out_dir)
    print_summary(summary)
    print(f"\n输出目录: {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
