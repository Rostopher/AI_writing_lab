"""摘要确定性文本处理：清洗、计词、切句。

规则版本（规则变化必须升版本并重算受影响样本）：
- WORD_COUNT_VERSION = "v1"
- SENTENCE_SPLITTER    = "pysbd 0.3.4"
- NORMALIZE_VERSION    = "v1"

所有函数只做可追踪的格式处理；疑似正文内容一律保留。
"""
from __future__ import annotations

import hashlib
import html
import re
import unicodedata

NORMALIZE_VERSION = "v1"
WORD_COUNT_VERSION = "v1"

import pysbd

SENTENCE_SPLITTER = f"pysbd {pysbd.__version__}"

# ---------------------------------------------------------------------------
# 计词
# ---------------------------------------------------------------------------
# word_count_v1 口径（v1）：
# - 英文单词（含 Unicode 字母）与数字表达式各计一个 token；
# - 词内撇号 / 连字符保留为一个 token：don't、difference-in-differences、COVID-19；
# - 数字表达式内部的小数点与千分位逗号不拆词：3.5、1,000 各计一个；
# - 尾随百分号附在数字上不独立计词：86% 计一个；独立 "%" 不计词；
# - 独立标点、数学符号（≤、→ 等）不计词；
# - "e.g." 之类缩写按字母段拆分（e、g 两个 token），属已知简化，不声称等同出版社口径。
_NUM_TOKEN = r"\d+(?:[.,]\d+)*%?"
_WORD_TOKEN = r"[^\W_]+(?:['’\-\u2010][^\W_]+)*%?"
WORD_TOKEN_RE = re.compile(rf"{_NUM_TOKEN}|{_WORD_TOKEN}", re.UNICODE)


def word_count_v1(text: str) -> tuple[int, list[str]]:
    """主计词口径。返回 (count, tokens)，tokens 供抽查。"""
    tokens = WORD_TOKEN_RE.findall(text)
    return len(tokens), tokens


def whitespace_count(text: str) -> int:
    """辅助口径：空白切分计数，仅作敏感性检查。"""
    return len(text.split())


# ---------------------------------------------------------------------------
# 清洗
# ---------------------------------------------------------------------------
_HTML_TAG_RE = re.compile(r"<[^>]+>")
# 尾部 JEL / Keywords 栏目：仅当出现在末尾（独立行或末尾行内模式）才剥除。
_TRAILING_LINE_RE = re.compile(
    r"^\s*(?:JEL(?:\s+[Cc]lassification(?:s)?)?|[Kk]eywords?)\s*[:：]"
)
_TRAILING_INLINE_RE = re.compile(
    r"\s(?:JEL(?:\s+[Cc]lassification(?:s)?)?\s*[:：]|[Kk]eywords?\s*[:：])[^\n]*\s*$"
)
_JPE_PREFIX_RE = re.compile(r"^\s*Abstract(?:\s*[:：])?\s+")
_WORD_TOKEN_FULL = re.compile(r"[^\W_]{2,}", re.UNICODE)


def _strip_html(raw: str) -> tuple[str, list[str]]:
    log: list[str] = []
    text = raw
    if _HTML_TAG_RE.search(text):
        text = _HTML_TAG_RE.sub(" ", text)
        log.append("html_tags_removed")
    unescaped = html.unescape(text)
    if unescaped != text:
        log.append("html_entities_unescaped")
        text = unescaped
    return text, log


def _strip_trailing_jel_keywords(text: str) -> tuple[str, list[str]]:
    """剥除尾部 JEL / Keywords 栏目（仅模式明确时）。"""
    lines = text.split("\n")
    cut = None
    for i, line in enumerate(lines):
        if _TRAILING_LINE_RE.match(line):
            cut = i
            break
    if cut is not None:
        # 仅当该行之后不再有实质正文行时才剥除，避免误删正文中的 "Keywords" 字样
        rest = [l for l in lines[cut + 1:] if l.strip()]
        if not rest or all(_TRAILING_LINE_RE.match(l) or not _WORD_TOKEN_FULL.search(l) for l in rest):
            return "\n".join(lines[:cut]), ["strip_trailing_jel_keywords"]
    m = _TRAILING_INLINE_RE.search(text)
    if m:
        return text[: m.start()], ["strip_trailing_jel_keywords"]
    return text, []


def normalize_abstract(raw: str) -> tuple[str, list[str]]:
    """清洗摘要原文。返回 (normalized, cleaning_log)。

    步骤：HTML 标签/实体 → Unicode NFC → JPE "Abstract " 站点包装前缀
    → 尾部 JEL/Keywords 栏目 → 布局换行与空白折叠。幂等。
    """
    if raw is None:
        raise ValueError("normalize_abstract: raw is None")
    cleaning_log: list[str] = []

    text, log = _strip_html(raw)
    cleaning_log.extend(log)

    nfc = unicodedata.normalize("NFC", text)
    if nfc != text:
        cleaning_log.append("unicode_nfc")
        text = nfc

    m = _JPE_PREFIX_RE.match(text)
    if m:
        text = text[m.end():]
        cleaning_log.append("strip_abstract_prefix")

    text, log = _strip_trailing_jel_keywords(text)
    cleaning_log.extend(log)

    collapsed = re.sub(r"\s+", " ", text).strip()
    if collapsed != text:
        cleaning_log.append("whitespace_collapsed")
        text = collapsed

    return text, cleaning_log


# ---------------------------------------------------------------------------
# 切句
# ---------------------------------------------------------------------------
_SEGMENTER = pysbd.Segmenter(language="en", clean=False)


def split_sentences(text: str) -> list[dict]:
    """用 pysbd 切句并返回 normalized 文本上的 [start, end) Python 字符偏移。

    偏移回切保证：text[start:end] == sentence["text"]（strip 后偏移对齐）。
    pysbd 输出可能带首尾空白，此处通过顺序子串定位恢复精确偏移；
    定位失败显式抛错，不静默兜底。
    """
    segments = _SEGMENTER.segment(text)
    sentences: list[dict] = []
    cursor = 0
    for i, seg in enumerate(segments, start=1):
        core = seg.strip()
        if not core:
            continue
        pos = text.find(core, cursor)
        if pos == -1:
            # 顺序定位失败时允许全文定位一次（pysbd 偶发重排），仍失败则抛错
            pos = text.find(core)
        if pos == -1:
            raise ValueError(
                f"split_sentences: 无法在原文定位第 {i} 句: {core[:80]!r}"
            )
        start, end = pos, pos + len(core)
        assert text[start:end] == core, "偏移回切不等于句文本"
        sentences.append(
            {"sentence_id": len(sentences) + 1, "text": core, "start": start, "end": end}
        )
        cursor = end
    return sentences


# ---------------------------------------------------------------------------
# 工具
# ---------------------------------------------------------------------------
def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
