"""派生摘要台账：遍历五刊上游数据，抽取作者摘要，产出 corpus_manifest.jsonl。

上游（只读）：姊妹仓库 playwright_crawler 的 top_journal_dataset/<JOURNAL>/<ISSUE_DIR>/
（路径经环境变量 ABSTRACT_STRUCTURE_UPSTREAM_ROOT 或 --upstream-root 指定）
输出：data/processed/abstract_structure/<run_id>/corpus_manifest.jsonl + run_manifest.json

已探明上游事实（2026-09-08 核验）：
- AER：期级 article_metadata.json 为 list[dict]，含 abstract / doi / is_front_matter。
- ECMA/JPE/QJE/REStud：期级为 dict 含 'articles'（可能带 BOM，统一 utf-8-sig 读取）。
- ECMA 摘要在 article_metadata/<ectaID>/page.html 的 article-section__abstract section；
  meta name="description" 被截断，仅用于前缀交叉核对。
- JPE 摘要在 article_metadata/<数字ID>/article_content.json 顶层 'abstract'，
  带站点包装前缀 "Abstract "（在 textnorm 清洗阶段剥除并记录）。
- QJE/REStud 摘要在 article_content.json 'sections' 中 kind=='abstract' 的 'text'。
- ECMA 期级文章列表含重复条目（同一文章大小写不同标题出现两次），按规范化标题去重。
- JPE 期级文章带 abstract 字段（与篇级一致的前缀），仅作交叉核对，不作为摘要来源。

遇到与上述不符的形态：记录 anomaly 并继续处理其他记录，不静默兜底。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from textnorm import (  # noqa: E402
    NORMALIZE_VERSION,
    SENTENCE_SPLITTER,
    WORD_COUNT_VERSION,
    normalize_abstract,
    sha256_text,
    split_sentences,
    whitespace_count,
    word_count_v1,
)

# ---------------------------------------------------------------------------
# 配置（可用 CLI 参数覆盖）
# ---------------------------------------------------------------------------
# 上游数据根不设私有默认路径：用环境变量 ABSTRACT_STRUCTURE_UPSTREAM_ROOT
# 或 --upstream-root 指定（playwright_crawler 的 top_journal_dataset 目录）。
_upstream_env = os.environ.get("ABSTRACT_STRUCTURE_UPSTREAM_ROOT")
UPSTREAM_ROOT = Path(_upstream_env) if _upstream_env else None
REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_ROOT = REPO_ROOT / "data" / "processed" / "abstract_structure"
DEFAULT_RUN_ID = "run_20260908_a"

JOURNALS = {
    "AER": "American Economic Review",
    "ECMA": "Econometrica",
    "JPE": "Journal of Political Economy",
    "QJE": "Quarterly Journal of Economics",
    "REStud": "Review of Economic Studies",
}
YEAR_MIN, YEAR_MAX = 2015, 2026

# 整期排除（记录原因，不进入文章级台账）
EXCLUDED_ISSUES = {
    "AER201505_5": "AER Papers & Proceedings 年会专辑（2015 年 5 月号），整期排除",
    "AER201605_5": "AER Papers & Proceedings 年会专辑（2016 年 5 月号），整期排除",
    "AER201705_5": "AER Papers & Proceedings 年会专辑（2017 年 5 月号），整期排除",
    "AER201804_4-5": "与 AER201804_4 为同一期（Vol 108 No. 4-5 合刊）的重复目录，无 article_metadata.json",
}

ISSUE_DIR_RE = {j: re.compile(rf"^{j}(\d{{4}})(\d{{2}})_(\S+)$") for j in JOURNALS}

# 文章类型排除（标题模式，保守处理；模糊者走 NEEDS_REVIEW_PATTERNS）
EXCLUDE_TITLE_PATTERNS: list[tuple[str, str]] = [
    ("front_matter", r"^(front\s?matter|frontmatter\b|backmatter\b|masthead|table of contents|volume contents|annual index|index$)"),
    ("forthcoming_papers", r"^forthcoming papers"),
    ("submissions_info", r"^((jpe )?submissions\b|submission of manuscripts\b)"),
    ("society_reports", r"\bannual reports?\b"),
    ("erratum", r"\b(erratum|errata|corrigendum)\b"),
    ("correction", r"^correction\b"),
    ("obituary", r"\b(obituary|in memoriam)\b"),
    ("book_review", r"^book reviews?\b"),
    ("comment_reply", r"(:\s*(comment|reply)\b|^(a )?comments? (on|to)\b|^(a )?reply (to|on)\b)"),
    ("lecture_address", r"\b(presidential address|nobel lecture|ely lecture|fisher-schultz lecture)\b"),
    ("foreword", r"^foreword\b"),
    ("editorial", r"^editorial\b"),
]
NEEDS_REVIEW_PATTERNS: list[tuple[str, str]] = [
    ("title_mentions_comment_reply", r"\b(comment|reply|rejoinder)\b"),
    ("editorial_like", r"^(editorial|editor'?s note)\b|^announcements?$"),
]

ECMA_ABSTRACT_SECTION_RE = re.compile(
    r'(?is)<section[^>]*class="[^"]*article-section__abstract[^"]*"[^>]*>(.*?)</section>'
)
# OUP（QJE/REStud）摘要尾部混入的固定订阅提示文案；其后可能还有卷首语等正文内容。
OUP_SUBSCRIPTION_BOILERPLATE = "As a benefit of your subscription"
ECMA_META_DESC_RE = re.compile(
    r'(?is)<meta[^>]*name="description"[^>]*content="([^"]*)"'
)
DOI_PREFIX_RE = re.compile(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", re.IGNORECASE)
TRUNCATED_TAIL_RE = re.compile(r"(\.\.\.|…)\s*$")

AVAILABILITY = (
    "available",
    "missing",
    "suspected_truncated",
    "extraction_error",
    "non_english",
    "needs_review",
)


# ---------------------------------------------------------------------------
# 基础工具
# ---------------------------------------------------------------------------
def load_json(path: Path) -> object:
    """读取 JSON（utf-8-sig 兼容 BOM）；坏 JSON 显式抛错。"""
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_doi(doi: str | None) -> str:
    if not doi:
        return ""
    d = DOI_PREFIX_RE.sub("", doi.strip()).strip().lower()
    return d


def iter_issue_dirs(upstream_root: Path, journal: str):
    """产出窗口内全部期目录 (issue_name, path, year, month)，按名称排序。"""
    jdir = upstream_root / journal
    if not jdir.is_dir():
        raise FileNotFoundError(f"期刊目录不存在: {jdir}")
    rx = ISSUE_DIR_RE[journal]
    for child in sorted(jdir.iterdir()):
        if not child.is_dir():
            continue
        m = rx.match(child.name)
        if not m:
            continue
        year, month = int(m.group(1)), int(m.group(2))
        if YEAR_MIN <= year <= YEAR_MAX:
            yield child.name, child, year, month


def classify_type(title: str, is_front_matter: bool | None) -> tuple[str | None, list[str]]:
    """返回 (exclusion_reason|None, type_signals)。模糊情形标 needs_review 信号。"""
    signals: list[str] = []
    if is_front_matter is True:
        return "front_matter(is_front_matter=true)", ["is_front_matter"]
    t = (title or "").strip()
    for name, pat in EXCLUDE_TITLE_PATTERNS:
        if re.search(pat, t, re.IGNORECASE):
            return f"excluded_type:{name}", [f"title_pattern:{name}"]
    for name, pat in NEEDS_REVIEW_PATTERNS:
        if re.search(pat, t, re.IGNORECASE):
            signals.append(f"needs_review:{name}")
    return None, signals


# ---------------------------------------------------------------------------
# 各刊抽取适配器
# ---------------------------------------------------------------------------
def extract_aer(issue_name: str, issue_path: Path, upstream_root: Path):
    """AER：期级 list[dict]，摘要即字段。产出 RawArticle dict list + issue anomalies。"""
    meta_path = issue_path / "article_metadata.json"
    anomalies: list[str] = []
    if not meta_path.exists():
        return [], [f"missing_issue_file:{meta_path.name}"]
    data = load_json(meta_path)
    if not isinstance(data, list):
        raise TypeError(f"AER 期级元数据应为 list，实际 {type(data).__name__}: {meta_path}")
    rel = str(meta_path.relative_to(upstream_root))
    articles = []
    for a in data:
        abstract = (a.get("abstract") or "").strip()
        articles.append(
            {
                "source_stable_id": f"aer_{issue_name}_{a.get('index')}",
                "title": a.get("title") or "",
                "authors": a.get("authors") or [],
                "doi_raw": a.get("doi") or "",
                "journal_raw": a.get("journal") or JOURNALS["AER"],
                "volume": a.get("volume"),
                "issue": a.get("issue"),
                "pages": a.get("pages"),
                "year": None,  # 由期目录年填充
                "online_date": a.get("online_date"),
                "is_front_matter": a.get("is_front_matter"),
                "abstract_raw": abstract if abstract else None,
                "extraction_status": "ok" if abstract else "missing",
                "abstract_source": "issue_field" if abstract else None,
                "anomalies": [],
                "source_files": [rel],
            }
        )
    return articles, anomalies


def _norm_title(t: str) -> str:
    return re.sub(r"\s+", " ", (t or "").strip()).casefold()


def extract_ecma(issue_name: str, issue_path: Path, upstream_root: Path):
    """ECMA：期级 dict['articles']（含重复条目，按规范化标题去重）；
    摘要在 article_metadata/<ectaID>/page.html。"""
    meta_path = issue_path / "article_metadata.json"
    anomalies: list[str] = []
    if not meta_path.exists():
        return [], [f"missing_issue_file:{meta_path.name}"]
    data = load_json(meta_path)
    if isinstance(data, dict) and "articles" in data:
        entries = data["articles"]
    elif isinstance(data, list):
        entries = data
        anomalies.append("unexpected_issue_schema:list")
    else:
        raise TypeError(f"ECMA 期级元数据形态不符: {meta_path}")

    # 期级去重（上游存在同文大小写不同标题的重复条目）
    seen: dict[str, dict] = {}
    n_dup = 0
    for a in entries:
        key = _norm_title(a.get("title", ""))
        if key in seen:
            n_dup += 1
            continue
        seen[key] = a
    if n_dup:
        anomalies.append(f"issue_level_duplicates:{n_dup}")

    # 篇级目录：title -> dir
    am_dir = issue_path / "article_metadata"
    dir_by_title: dict[str, Path] = {}
    if am_dir.is_dir():
        for sub in sorted(am_dir.iterdir()):
            if not sub.is_dir():
                continue
            ac = sub / "article_content.json"
            if not ac.exists():
                anomalies.append(f"missing_article_content:{sub.name}")
                continue
            try:
                content = load_json(ac)
            except json.JSONDecodeError as e:
                anomalies.append(f"bad_article_content_json:{sub.name}:{e}")
                continue
            dir_by_title[_norm_title(content.get("title", ""))] = sub

    rel_meta = str(meta_path.relative_to(upstream_root))
    articles = []
    matched_dirs: set[Path] = set()
    for key, a in seen.items():
        sub = dir_by_title.get(key)
        title = a.get("title") or ""
        base = {
            "title": title,
            "authors": a.get("authors") or [],
            "journal_raw": JOURNALS["ECMA"],
            "volume": a.get("volume"),
            "issue": a.get("issue"),
            "pages": a.get("pages"),
            "year": int(a["year"]) if str(a.get("year") or "").isdigit() else None,
            "is_front_matter": None,
            "source_files": [rel_meta],
            "anomalies": [],
        }
        if sub is None:
            base.update(
                source_stable_id=f"ecma_{issue_name}_{_norm_title(title)[:40]}",
                doi_raw="",
                online_date=None,
                abstract_raw=None,
                extraction_status="missing",
            )
            base["anomalies"].append("no_article_metadata_dir")
            articles.append(base)
            continue
        matched_dirs.add(sub)
        ac = sub / "article_content.json"
        content = load_json(ac)
        rel_ac = str(ac.relative_to(upstream_root))
        base["source_files"].append(rel_ac)
        base.update(
            source_stable_id=sub.name,
            doi_raw=content.get("doi") or "",
            online_date=content.get("online_date"),
            title=content.get("title") or title,
            authors=content.get("authors") or base["authors"],
        )
        page = sub / "page.html"
        if not page.exists():
            base.update(abstract_raw=None, extraction_status="extraction_error")
            base["anomalies"].append("missing_page_html")
            articles.append(base)
            continue
        base["source_files"].append(str(page.relative_to(upstream_root)))
        html_text = page.read_text(encoding="utf-8-sig", errors="replace")
        m = ECMA_ABSTRACT_SECTION_RE.search(html_text)
        if not m:
            base.update(abstract_raw=None, extraction_status="extraction_error")
            base["anomalies"].append("abstract_section_not_found")
            articles.append(base)
            continue
        base.update(abstract_raw=m.group(1), extraction_status="ok",
                    abstract_source="page_html_section")
        # meta description 前缀交叉核对（meta 被截断，仅作核对不作来源）
        md = ECMA_META_DESC_RE.search(html_text)
        if md:
            prefix = re.sub(r"(\.\.\.|…)\s*$", "", md.group(1)).strip()
            stripped = re.sub(r"<[^>]+>", " ", m.group(1))
            stripped = re.sub(r"\s+", " ", stripped).strip()
            stripped = re.sub(r"^Abstract(?:\s*[:：])?\s+", "", stripped)  # 剥 section 内 h2 标题
            if prefix and not stripped.startswith(prefix[:40]):
                base["anomalies"].append("meta_description_prefix_mismatch")
        articles.append(base)

    orphan = [p.name for p in dir_by_title.values() if p not in matched_dirs]
    if orphan:
        anomalies.append(f"orphan_article_dirs:{','.join(sorted(orphan))}")
    return articles, anomalies


def extract_jpe(issue_name: str, issue_path: Path, upstream_root: Path):
    """JPE：期级 dict['articles']（doi 后缀即篇级数字目录名）；
    摘要在 article_metadata/<num>/article_content.json 顶层 'abstract'。"""
    meta_path = issue_path / "article_metadata.json"
    anomalies: list[str] = []
    if not meta_path.exists():
        return [], [f"missing_issue_file:{meta_path.name}"]
    data = load_json(meta_path)
    if isinstance(data, dict) and "articles" in data:
        entries = data["articles"]
    elif isinstance(data, list):
        entries = data
        anomalies.append("unexpected_issue_schema:list")
    else:
        raise TypeError(f"JPE 期级元数据形态不符: {meta_path}")

    rel_meta = str(meta_path.relative_to(upstream_root))
    articles = []
    for a in entries:
        doi = a.get("doi") or ""
        num = doi.split("/")[-1] if doi else ""
        base = {
            "source_stable_id": num or f"jpe_{issue_name}_{_norm_title(a.get('title',''))[:40]}",
            "title": a.get("title") or "",
            "authors": a.get("authors") or [],
            "doi_raw": doi,
            "journal_raw": JOURNALS["JPE"],
            "volume": a.get("volume"),
            "issue": a.get("issue"),
            "pages": a.get("pages"),
            "year": int(a["year"]) if str(a.get("year") or "").isdigit() else None,
            "online_date": None,
            "is_front_matter": None,
            "source_files": [rel_meta],
            "anomalies": [],
        }
        if not num:
            base.update(abstract_raw=None, extraction_status="extraction_error")
            base["anomalies"].append("no_doi_no_article_dir")
            articles.append(base)
            continue
        ac = issue_path / "article_metadata" / num / "article_content.json"
        issue_abs = (a.get("abstract") or "").strip()
        if not ac.exists():
            # 篇级文件缺失：回退到期级 abstract 字段（已核验二者在均有值时 32/33 等价）
            if issue_abs:
                base.update(abstract_raw=issue_abs, extraction_status="ok",
                            abstract_source="issue_field_fallback")
                base["anomalies"].append("missing_article_content_json")
            else:
                base.update(abstract_raw=None, extraction_status="missing")
                base["anomalies"].append("missing_article_content_json")
            articles.append(base)
            continue
        base["source_files"].append(str(ac.relative_to(upstream_root)))
        content = load_json(ac)
        abstract = content.get("abstract")
        if abstract and str(abstract).strip():
            base.update(abstract_raw=str(abstract), extraction_status="ok",
                        abstract_source="article_content_abstract")
            # 期级 abstract 前缀交叉核对（期级仅作核对不作来源）
            stripped = re.sub(r"^Abstract\s+", "", str(abstract)).strip()
            if issue_abs and not stripped.startswith(issue_abs[:40]):
                base["anomalies"].append("issue_abstract_prefix_mismatch")
        elif issue_abs:
            # 篇级 abstract 为空（2023–2025 年上游篇级抓取大量如此）：回退期级字段
            base.update(abstract_raw=issue_abs, extraction_status="ok",
                        abstract_source="issue_field_fallback")
            base["anomalies"].append("empty_article_level_abstract")
        else:
            base.update(abstract_raw=None, extraction_status="missing")
        articles.append(base)
    return articles, anomalies


def _extract_oxford(issue_name: str, issue_path: Path, upstream_root: Path, journal: str):
    """QJE/REStud：期级 dict['articles'] 含 article_metadata_dir；
    摘要在 article_content.json 'sections' 中 kind=='abstract' 的 'text'。"""
    meta_path = issue_path / "article_metadata.json"
    anomalies: list[str] = []
    if not meta_path.exists():
        return [], [f"missing_issue_file:{meta_path.name}"]
    data = load_json(meta_path)
    if isinstance(data, dict) and "articles" in data:
        entries = data["articles"]
    elif isinstance(data, list):
        entries = data
        anomalies.append("unexpected_issue_schema:list")
    else:
        raise TypeError(f"{journal} 期级元数据形态不符: {meta_path}")

    rel_meta = str(meta_path.relative_to(upstream_root))
    articles = []
    for a in entries:
        dir_field = a.get("article_metadata_dir") or ""
        code = Path(dir_field).name if dir_field else ""
        base = {
            "source_stable_id": code
            or f"{journal.lower()}_{issue_name}_{_norm_title(a.get('title',''))[:40]}",
            "title": a.get("title") or "",
            "authors": a.get("authors") or [],
            "doi_raw": a.get("doi") or "",
            "journal_raw": JOURNALS[journal],
            "volume": a.get("volume"),
            "issue": a.get("issue"),
            "pages": a.get("pages"),
            "year": int(a["year"]) if str(a.get("year") or "").isdigit() else None,
            "online_date": None,
            "is_front_matter": None,
            "source_files": [rel_meta],
            "anomalies": [],
        }
        if not code:
            base.update(abstract_raw=None, extraction_status="extraction_error")
            base["anomalies"].append("no_article_metadata_dir_field")
            articles.append(base)
            continue
        ac = issue_path / "article_metadata" / code / "article_content.json"
        if not ac.exists():
            base.update(abstract_raw=None, extraction_status="missing")
            base["anomalies"].append("missing_article_content_json")
            articles.append(base)
            continue
        base["source_files"].append(str(ac.relative_to(upstream_root)))
        content = load_json(ac)
        sections = content.get("sections")
        if not isinstance(sections, list):
            base.update(abstract_raw=None, extraction_status="extraction_error")
            base["anomalies"].append("no_sections_list")
            articles.append(base)
            continue
        abs_secs = [s for s in sections if isinstance(s, dict) and s.get("kind") == "abstract"]
        if not abs_secs:
            base.update(abstract_raw=None, extraction_status="missing")
            base["anomalies"].append("no_abstract_section")
            articles.append(base)
            continue
        if len(abs_secs) > 1:
            base["anomalies"].append(f"multiple_abstract_sections:{len(abs_secs)}")
        text = (abs_secs[0].get("text") or "").strip()
        # 上游部分文章 abstract section 的 text 混入整篇正文（QJE/REStud 共 373 篇，
        # 均已核验 paragraphs[0] 是 text 前缀）；此时取 paragraphs[0] 并记录。
        paras = abs_secs[0].get("paragraphs") or []
        if len(text) > 4000 and paras:
            p0_raw = paras[0].strip()
            p0 = p0_raw.strip('"').strip()
            if p0 and text.startswith(p0_raw[:100].strip('"').strip()):
                base["anomalies"].append(
                    f"abstract_section_oversized:{len(text)}:used_paragraph0")
                text = p0
            else:
                base.update(abstract_raw=None, extraction_status="extraction_error")
                base["anomalies"].append(
                    f"abstract_section_oversized:{len(text)}:paragraph0_not_prefix")
                articles.append(base)
                continue
        if text:
            # OUP 站点包装：摘要尾部（或中段）混入订阅提示及之后的卷首语等正文，
            # 已核验 800 条均为该固定文案，截断处之前的才是摘要本体。
            cut = text.find(OUP_SUBSCRIPTION_BOILERPLATE)
            if cut != -1:
                base["anomalies"].append("oup_subscription_boilerplate_removed")
                text = text[:cut].strip()
        if text:
            base.update(abstract_raw=text, extraction_status="ok",
                        abstract_source="article_content_sections")
        else:
            base.update(abstract_raw=None, extraction_status="missing")
            base["anomalies"].append("empty_abstract_section_text")
        articles.append(base)
    return articles, anomalies


EXTRACTORS = {
    "AER": extract_aer,
    "ECMA": extract_ecma,
    "JPE": extract_jpe,
    "QJE": lambda n, p, r: _extract_oxford(n, p, r, "QJE"),
    "REStud": lambda n, p, r: _extract_oxford(n, p, r, "REStud"),
}


# ---------------------------------------------------------------------------
# 记录构建
# ---------------------------------------------------------------------------
def build_record(journal: str, issue_name: str, issue_year: int, issue_month: int,
                 raw: dict, upstream_root: Path) -> dict:
    exclusion_reason, type_signals = classify_type(raw["title"], raw.get("is_front_matter"))
    anomalies = list(raw.get("anomalies") or [])

    doi_raw = raw.get("doi_raw") or ""
    doi_norm = normalize_doi(doi_raw)
    article_id = f"{journal}:{doi_norm}" if doi_norm else f"{journal}:{raw['source_stable_id']}"

    abstract_raw = raw.get("abstract_raw")
    cleaning_log: list[str] = []
    normalized = None
    sentences: list[dict] = []
    wc = ws = sc = None

    if abstract_raw is not None:
        normalized, cleaning_log = normalize_abstract(abstract_raw)
        if not normalized:
            anomalies.append("normalized_empty")
            normalized = None

    _REVIEW_ANOMALIES = {
        "meta_description_prefix_mismatch",
        "issue_abstract_prefix_mismatch",
        "normalized_empty",
    }
    needs_review = (
        any(s.startswith("needs_review:") for s in type_signals)
        or any(a in _REVIEW_ANOMALIES or a.startswith("multiple_abstract_sections")
               for a in anomalies)
    )

    if normalized is None:
        availability = "extraction_error" if raw["extraction_status"] == "extraction_error" else "missing"
    elif TRUNCATED_TAIL_RE.search(normalized):
        availability = "suspected_truncated"
    elif needs_review:
        availability = "needs_review"
    else:
        availability = "available"

    if normalized is not None:
        sentences = split_sentences(normalized)
        sc = len(sentences)
        wc, _tokens = word_count_v1(normalized)
        ws = whitespace_count(normalized)

    source_sha256: dict[str, str] = {}
    for rel in raw["source_files"]:
        try:
            source_sha256[rel] = sha256_file(upstream_root / rel)
        except OSError as e:
            anomalies.append(f"source_hash_error:{rel}:{e}")

    return {
        "article_id": article_id,
        "doi_raw": doi_raw,
        "doi_normalized": doi_norm,
        "journal_raw": raw.get("journal_raw") or JOURNALS[journal],
        "journal_code": journal,
        "title": raw["title"],
        "issue_dir": issue_name,
        "year": raw.get("year") or issue_year,
        "month": issue_month,
        "volume": raw.get("volume"),
        "issue": raw.get("issue"),
        "pages": raw.get("pages"),
        "online_date": raw.get("online_date"),
        "type_signals": type_signals,
        "included": exclusion_reason is None,
        "exclusion_reason": exclusion_reason,
        "source_stable_id": raw["source_stable_id"],
        "source_files": raw["source_files"],
        "source_sha256": source_sha256,
        "extracted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "abstract_raw": abstract_raw,
        "abstract_source": raw.get("abstract_source"),
        "abstract_raw_sha256": sha256_text(abstract_raw) if abstract_raw is not None else None,
        "abstract_normalized": normalized,
        "abstract_norm_sha256": sha256_text(normalized) if normalized is not None else None,
        "cleaning_log": cleaning_log,
        "availability": availability,
        "sentence_count": sc,
        "word_count_v1": wc,
        "whitespace_count": ws,
        "sentences": sentences,
        "anomalies": anomalies,
    }


# ---------------------------------------------------------------------------
# 去重与版本冲突
# ---------------------------------------------------------------------------
_AVAIL_RANK = {a: i for i, a in enumerate(AVAILABILITY)}


def resolve_duplicates(records: list[dict]) -> dict:
    """同规范化 DOI 多条：保留全部版本并标 selected 及理由。返回统计。"""
    by_doi: dict[str, list[int]] = {}
    for i, r in enumerate(records):
        if r["doi_normalized"]:
            by_doi.setdefault(r["doi_normalized"], []).append(i)
    n_conflict_groups = 0
    for doi, idxs in sorted(by_doi.items()):
        if len(idxs) == 1:
            records[idxs[0]]["selected"] = True
            records[idxs[0]]["selection_reason"] = "unique_doi"
            records[idxs[0]]["version_conflict"] = False
            continue
        n_conflict_groups += 1
        # 选取：availability 最优（available 排前），其次年份靠后者（卷期记录优先）
        def _issue_year(i: int) -> int:
            m = re.search(r"(\d{4})", records[i]["issue_dir"])
            return int(m.group(1)) if m else 0
        best = min(
            idxs,
            key=lambda i: (
                _AVAIL_RANK.get(records[i]["availability"], 99),
                -_issue_year(i),
                records[i]["issue_dir"],
            ),
        )
        same_text = len({records[i]["abstract_norm_sha256"] for i in idxs}) == 1
        for i in idxs:
            records[i]["version_conflict"] = True
            records[i]["selected"] = i == best
            records[i]["selection_reason"] = (
                "duplicate_doi_selected:best_availability" if i == best
                else "duplicate_doi_superseded"
            )
            if not same_text:
                records[i]["anomalies"].append("duplicate_doi_divergent_abstract")
                if records[i]["availability"] == "available":
                    records[i]["availability"] = "needs_review"
    for r in records:
        if "selected" not in r:  # 无 DOI 记录
            r["selected"] = True
            r["selection_reason"] = "no_doi"
            r["version_conflict"] = False
    return {"n_doi_conflict_groups": n_conflict_groups}


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def run(upstream_root: Path, output_root: Path, run_id: str,
        journals: list[str] | None = None) -> dict:
    out_dir = output_root / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc)

    records: list[dict] = []
    issue_log: list[dict] = []
    journals = journals or list(JOURNALS)

    for journal in journals:
        for issue_name, issue_path, year, month in iter_issue_dirs(upstream_root, journal):
            if issue_name in EXCLUDED_ISSUES:
                issue_log.append({
                    "issue_dir": issue_name, "journal": journal,
                    "status": "excluded_issue", "reason": EXCLUDED_ISSUES[issue_name],
                })
                continue
            try:
                raw_articles, anomalies = EXTRACTORS[journal](issue_name, issue_path, upstream_root)
            except (json.JSONDecodeError, TypeError, OSError) as e:
                issue_log.append({
                    "issue_dir": issue_name, "journal": journal,
                    "status": "issue_error", "reason": f"{type(e).__name__}: {e}",
                })
                continue
            for raw in raw_articles:
                records.append(build_record(journal, issue_name, year, month, raw, upstream_root))
            issue_log.append({
                "issue_dir": issue_name, "journal": journal,
                "status": "ok", "n_articles": len(raw_articles), "anomalies": anomalies,
            })

    dedup_stats = resolve_duplicates(records)

    manifest_path = out_dir / "corpus_manifest.jsonl"
    with open(manifest_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    from collections import Counter
    avail_counts = Counter(r["availability"] for r in records)
    per_journal = {}
    for j in journals:
        sub = [r for r in records if r["journal_code"] == j]
        per_journal[j] = {
            "n_records": len(sub),
            "n_included": sum(1 for r in sub if r["included"]),
            "n_selected": sum(1 for r in sub if r["selected"]),
            "availability": dict(Counter(r["availability"] for r in sub)),
        }

    finished = datetime.now(timezone.utc)
    stats = {
        "run_id": run_id,
        "started_at": started.isoformat(timespec="seconds"),
        "finished_at": finished.isoformat(timespec="seconds"),
        "upstream_root": str(upstream_root),
        "n_records": len(records),
        "n_included": sum(1 for r in records if r["included"]),
        "n_selected": sum(1 for r in records if r["selected"]),
        "availability": dict(avail_counts),
        "per_journal": per_journal,
        "n_issues_ok": sum(1 for e in issue_log if e["status"] == "ok"),
        "n_issues_excluded": sum(1 for e in issue_log if e["status"] == "excluded_issue"),
        "n_issues_error": sum(1 for e in issue_log if e["status"] == "issue_error"),
        **dedup_stats,
    }
    run_manifest = {
        **stats,
        "versions": {
            "normalize": NORMALIZE_VERSION,
            "word_count": WORD_COUNT_VERSION,
            "sentence_splitter": SENTENCE_SPLITTER,
        },
        "journals": journals,
        "year_window": [YEAR_MIN, YEAR_MAX],
        "excluded_issues": EXCLUDED_ISSUES,
        "issue_log": issue_log,
    }
    with open(out_dir / "run_manifest.json", "w", encoding="utf-8") as f:
        json.dump(run_manifest, f, ensure_ascii=False, indent=2)
    return stats


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="抽取五刊摘要，生成 corpus_manifest.jsonl")
    ap.add_argument("--upstream-root", type=Path, default=UPSTREAM_ROOT)
    ap.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    ap.add_argument("--run-id", default=DEFAULT_RUN_ID)
    ap.add_argument("--journals", nargs="*", choices=list(JOURNALS), default=None)
    args = ap.parse_args(argv)
    if args.upstream_root is None:
        ap.error("需要 --upstream-root 或环境变量 ABSTRACT_STRUCTURE_UPSTREAM_ROOT")

    stats = run(args.upstream_root, args.output_root, args.run_id, args.journals)
    print(f"run_id: {stats['run_id']}")
    print(f"records: {stats['n_records']}  included: {stats['n_included']}  "
          f"selected: {stats['n_selected']}")
    print(f"availability: {stats['availability']}")
    for j, s in stats["per_journal"].items():
        print(f"  {j}: records={s['n_records']} included={s['n_included']} {s['availability']}")
    print(f"issues ok/excluded/error: {stats['n_issues_ok']}/{stats['n_issues_excluded']}"
          f"/{stats['n_issues_error']}  doi_conflict_groups: {stats['n_doi_conflict_groups']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
