"""derive_metrics 契约测试：合成标注 fixture 保护
三态出现状态、inclusive What unresolved、顺序共现/tie、缺失值 null 与 [] 的区分、
quote 定位失败率 >5% 停用占比。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import derive_metrics as dm  # noqa: E402
from textnorm import normalize_abstract, split_sentences, word_count_v1  # noqa: E402


def make_rec(aid: str, text: str) -> dict:
    norm, _ = normalize_abstract(text)
    sents = split_sentences(norm)
    wc, _ = word_count_v1(norm)
    return {"article_id": aid, "abstract_normalized": norm, "word_count_v1": wc,
            "sentences": sents, "journal_code": "SYNTH", "year": 2020,
            "included": True, "availability": "available", "selected": True}


def _fn(label, quote, focus=None, aspects=None):
    return {"label": label, "evidence": [
        {"quote": quote, "finding_focus": focus, "how_aspects": aspects or []}]}


def _sa(sid, functions=None, other=None, uncertain=None, connective=False):
    return {"sentence_id": sid, "functions": functions or [],
            "other_content": other or [], "uncertain_content": uncertain or [],
            "connective_only": connective}


@pytest.fixture()
def synth(tmp_path: Path):
    """五篇合成文章 + 合成标注（agent 格式）。"""
    t1 = "We study X using Y data. We find Z. These results matter."
    t2 = "Topic A is important. We compute B from administrative records."
    t3 = "We estimate effects. Effects are large."
    t4 = "Unannotated article text here. More text follows."
    t5 = "In sum, the paper proceeds as follows."

    corpus = {a: make_rec(a, t) for a, t in
              [("A1", t1), ("A2", t2), ("A3", t3), ("A4", t4), ("A5", t5)]}

    anns = {
        # A1: what+how 同句（共现 tie），findings central（→ inclusive What 并入 s2）
        "A1": {"article_id": "A1", "annotator": "test", "paper_type": {
            "primary_type": "empirical", "evidence": []},
            "sentence_annotations": [
                _sa(1, [_fn("what", "We study X"),
                        _fn("how", "using Y data", None, ["data"])]),
                _sa(2, [_fn("findings", "We find Z.", "central")]),
                _sa(3, [_fn("why_it_matters", "These results matter.")]),
            ]},
        # A2: 无 what 功能，但 s1 有 what 候选 uncertain → what=unclear；inclusive 同样 unresolved
        "A2": {"article_id": "A2", "annotator": "test", "paper_type": {
            "primary_type": "empirical", "evidence": []},
            "sentence_annotations": [
                _sa(1, other=[{"quote": "Topic A is important",
                               "function_description": "topic background"}],
                    uncertain=[{"quote": "Topic A is important",
                                "candidate_functions": ["what"],
                                "reason": "could frame research object"}]),
                _sa(2, [_fn("how", "compute B from administrative records", None, ["data"])]),
            ]},
        # A3: findings 仅 finding_focus=unclear → 窄 What absent、inclusive What unresolved
        "A3": {"article_id": "A3", "annotator": "test", "paper_type": {
            "primary_type": "unclear", "evidence": []},
            "sentence_annotations": [
                _sa(1, [_fn("how", "estimate effects", None, ["design"])]),
                _sa(2, [_fn("findings", "Effects are large.", "unclear")]),
            ]},
        # A5: 全部 connective_only → 功能列表为 []（明确缺失，不是 null）
        "A5": {"article_id": "A5", "annotator": "test", "paper_type": {
            "primary_type": "unclear", "evidence": []},
            "sentence_annotations": [_sa(1, connective=True)]},
        # A4: 不标注（模拟模型失败）→ null
    }

    corpus_path = tmp_path / "corpus.jsonl"
    corpus_path.write_text("\n".join(json.dumps(r) for r in corpus.values()) + "\n",
                           encoding="utf-8")
    sample_path = tmp_path / "sample.jsonl"
    sample_path.write_text("\n".join(
        json.dumps({"article_id": a, "anon_id": f"anon_{a}"})
        for a in ("A1", "A2", "A3", "A4", "A5")) + "\n", encoding="utf-8")
    ann_path = tmp_path / "ann.jsonl"
    ann_path.write_text("\n".join(json.dumps(a) for a in anns.values()) + "\n",
                        encoding="utf-8")
    return corpus_path, sample_path, ann_path, tmp_path / "out.json"


def test_three_state_presence(synth):
    corpus_path, sample_path, ann_path, out = synth
    result = dm.run(corpus_path, [ann_path], sample_path, out)
    src = next(iter(result["sources"].values()))
    pa = {r["article_id"]: r for r in src["per_article"]}
    assert pa["A1"]["presence"]["what"] == "present"
    assert pa["A2"]["presence"]["what"] == "unclear"   # 仅有 uncertain 候选
    assert pa["A3"]["presence"]["what"] == "absent"    # 窄口径无证据也无候选
    assert pa["A5"]["presence"]["what"] == "absent"


def test_inclusive_what_unresolved(synth):
    corpus_path, sample_path, ann_path, out = synth
    result = dm.run(corpus_path, [ann_path], sample_path, out)
    src = next(iter(result["sources"].values()))
    pa = {r["article_id"]: r for r in src["per_article"]}
    # A1: central findings 句并入 inclusive What
    assert pa["A1"]["function_lists"]["what_inclusive"] == [1, 2]
    assert pa["A1"]["presence"]["what_inclusive"] == "present"
    # A3: 仅 unclear findings → inclusive unresolved，不按 absent 处理
    assert pa["A3"]["presence"]["what_inclusive"] == "unresolved"
    assert pa["A3"]["function_lists"]["what_inclusive"] == []
    assert pa["A3"]["what_inclusive_unresolved_sents"] == [2]
    # A2: uncertain 候选 what → inclusive unresolved
    assert pa["A2"]["presence"]["what_inclusive"] == "unresolved"


def test_null_vs_empty_list(synth):
    corpus_path, sample_path, ann_path, out = synth
    result = dm.run(corpus_path, [ann_path], sample_path, out)
    src = next(iter(result["sources"].values()))
    pa = {r["article_id"]: r for r in src["per_article"]}
    assert pa["A4"]["function_lists"] is None       # 模型失败 = 缺失值
    assert pa["A5"]["function_lists"]["what"] == []  # 明确缺失 = []
    assert src["n_missing_annotation"] == 1
    assert src["missing_annotation_article_ids"] == ["A4"]


def test_order_tie_is_cooccurrence(synth):
    corpus_path, sample_path, ann_path, out = synth
    result = dm.run(corpus_path, [ann_path], sample_path, out)
    src = next(iter(result["sources"].values()))
    pairs = src["order"]["narrow"]["pairwise_first_occurrence"]
    # A1 的 what 与 how 同句 → 共现 "="，不当严格 "<"
    assert pairs["what~how"].get("=", 0) == 1
    assert pairs["what~how"].get("<", 0) == 0


def test_coverage_lower_upper(synth):
    corpus_path, sample_path, ann_path, out = synth
    result = dm.run(corpus_path, [ann_path], sample_path, out)
    src = next(iter(result["sources"].values()))
    cov = src["coverage"]["narrow"]["core3"]
    # 4 篇已标注：仅 A1 core3 齐（what/how/findings 均 present）
    assert cov["lower"] == 1
    assert cov["n"] == 4
    # A2 findings 为 absent（无证据也无候选），A3 窄 what absent → 上界也是 1
    assert cov["upper"] == 1
    assert cov["unresolved"] == 0
    # inclusive：A3 的 what_inclusive unresolved 计入上界 → 2（A1、A3）；
    # A2 findings 仍 absent 不计
    assert src["coverage"]["inclusive"]["core3"]["lower"] == 1
    assert src["coverage"]["inclusive"]["core3"]["upper"] == 2


def test_sentence_count_rules_denominators(synth):
    corpus_path, sample_path, ann_path, out = synth
    result = dm.run(corpus_path, [ann_path], sample_path, out)
    rules = src_rules = next(iter(result["sources"].values()))["sentence_counts"]["rules"]
    # what 1–2：总体分母含 absent 的 A2/A3/A5
    assert rules["what"]["n_overall"] == 4
    assert rules["what"]["satisfied_overall"] == 1   # 仅 A1
    assert rules["what"]["n_present"] == 1           # 条件分母只含 A1
    assert rules["what"]["satisfied_if_present"] == 1


def test_quote_failure_disables_share(synth, tmp_path: Path):
    corpus_path, sample_path, ann_path, out = synth
    bad = {"article_id": "A1", "annotator": "test", "paper_type": {
        "primary_type": "empirical", "evidence": []},
        "sentence_annotations": [
            _sa(1, [_fn("what", "不存在的引文"), _fn("how", "也没有", None, ["data"])]),
            _sa(2, [_fn("findings", " still wrong ", "central")]),
            _sa(3, [_fn("why_it_matters", "nope")]),
        ]}
    bad_path = tmp_path / "bad_ann.jsonl"
    bad_path.write_text(json.dumps(bad) + "\n", encoding="utf-8")
    result = dm.run(corpus_path, [bad_path], sample_path, tmp_path / "out2.json")
    src = next(iter(result["sources"].values()))
    assert src["text_share"]["disabled"] is True
    assert "停用" in src["text_share"]["note"]


def test_length_bins_and_missing(synth):
    corpus_path, sample_path, ann_path, out = synth
    result = dm.run(corpus_path, [ann_path], sample_path, out)
    lo = result["length"]["overall"]
    assert lo["n"] == 5
    assert lo["n_missing_word_count"] == 0
    assert sum(lo["bins"][k] for k in ("<100", "=100", "101-150", ">150")) == 5
    assert "SYNTH" in result["length"]["by_journal"]
    # 类型分层标明标签来源
    strata = result["length"]["by_type"]
    assert strata and next(iter(strata.values()))["label_source"] == "test"


def test_framework_out(synth):
    corpus_path, sample_path, ann_path, out = synth
    result = dm.run(corpus_path, [ann_path], sample_path, out)
    fo = next(iter(result["sources"].values()))["framework_out"]
    assert fo["articles_with_other"] == 1          # A2
    assert fo["articles_with_uncertain"] == 1      # A2（不计作确定新功能）
    assert any(w == "background" for w, _ in fo["description_word_freq_top30"])
