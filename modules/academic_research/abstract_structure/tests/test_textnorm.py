"""textnorm 契约测试：计词边界、切句偏移回切、清洗幂等。全部为合成 fixture。"""
from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from textnorm import (  # noqa: E402
    SENTENCE_SPLITTER,
    WORD_COUNT_VERSION,
    normalize_abstract,
    split_sentences,
    whitespace_count,
    word_count_v1,
)


class TestWordCount:
    def test_apostrophe_word_single_token(self):
        n, tokens = word_count_v1("don't")
        assert n == 1 and tokens == ["don't"]

    def test_hyphenated_word_single_token(self):
        n, tokens = word_count_v1("difference-in-differences")
        assert n == 1 and tokens == ["difference-in-differences"]

    def test_decimal_single_token(self):
        n, tokens = word_count_v1("3.5")
        assert n == 1 and tokens == ["3.5"]

    def test_thousands_separator_single_token(self):
        n, tokens = word_count_v1("1,000")
        assert n == 1 and tokens == ["1,000"]

    def test_percent_attached_counts_once(self):
        n, tokens = word_count_v1("86%")
        assert n == 1 and tokens == ["86%"]

    def test_standalone_percent_not_counted(self):
        n, _ = word_count_v1("%")
        assert n == 0

    def test_standalone_punctuation_and_math_not_counted(self):
        n, _ = word_count_v1("... ≤ → , ;")
        assert n == 0

    def test_mixed_sentence(self):
        n, tokens = word_count_v1("Training raises earnings by 5 percent.")
        assert n == 6
        assert tokens == ["Training", "raises", "earnings", "by", "5", "percent"]

    def test_alnum_hyphen_token(self):
        n, _ = word_count_v1("COVID-19")
        assert n == 1

    def test_version_recorded(self):
        assert WORD_COUNT_VERSION == "v1"
        assert SENTENCE_SPLITTER.startswith("pysbd ")


class TestNormalize:
    def test_html_tags_and_entities(self):
        norm, log = normalize_abstract("<p>Tom &amp; Jerry &lt;3</p>")
        assert norm == "Tom & Jerry <3"
        assert "html_tags_removed" in log
        assert "html_entities_unescaped" in log

    def test_unicode_nfc(self):
        raw = "cafe\u0301"  # e + combining acute
        norm, log = normalize_abstract(raw)
        assert norm == unicodedata.normalize("NFC", raw)
        assert "unicode_nfc" in log

    def test_jpe_abstract_prefix_stripped(self):
        norm, log = normalize_abstract("Abstract We study gravity.")
        assert norm == "We study gravity."
        assert "strip_abstract_prefix" in log

    def test_whitespace_collapse(self):
        norm, log = normalize_abstract("Line one.\n\n   Line\ttwo.")
        assert norm == "Line one. Line two."
        assert "whitespace_collapsed" in log

    def test_trailing_jel_keywords_stripped(self):
        raw = "We study X. We find Y.\nJEL Classification: E22, E24\nKeywords: business cycles"
        norm, log = normalize_abstract(raw)
        assert norm == "We study X. We find Y."
        assert "strip_trailing_jel_keywords" in log

    def test_body_like_content_not_removed(self):
        # 疑似正文但无明确站点包装模式：保留
        raw = "We study X. Keywords are discussed in the text. We find Y."
        norm, log = normalize_abstract(raw)
        assert "Keywords are discussed" in norm
        assert "strip_trailing_jel_keywords" not in log

    def test_idempotent(self):
        raw = "<p>Abstract We study X &amp; Y.\nJEL: E22</p>"
        once, _ = normalize_abstract(raw)
        twice, _ = normalize_abstract(once)
        assert once == twice


class TestSplitSentences:
    def test_offsets_roundtrip(self):
        text = ("We study how training affects earnings using a randomized experiment. "
                "Training raises earnings by 5 percent. These gains matter.")
        sents = split_sentences(text)
        assert [s["sentence_id"] for s in sents] == [1, 2, 3]
        for s in sents:
            assert text[s["start"]:s["end"]] == s["text"]

    def test_abbreviation_not_split(self):
        text = "The U.S. economy grew. China slowed."
        sents = split_sentences(text)
        assert len(sents) == 2
        assert sents[0]["text"] == "The U.S. economy grew."

    def test_decimal_not_split(self):
        text = "The effect is 3.5 percent. It is significant."
        sents = split_sentences(text)
        assert len(sents) == 2

    def test_leading_trailing_whitespace_aligned(self):
        # pysbd 输出可能带首尾空白：偏移须精确指向 strip 后文本
        text = "First sentence here.   Second sentence here."
        sents = split_sentences(text)
        assert len(sents) == 2
        for s in sents:
            assert text[s["start"]:s["end"]] == s["text"]
            assert s["text"] == s["text"].strip()


class TestWhitespaceCount:
    def test_simple(self):
        assert whitespace_count("a b  c\nd") == 4
