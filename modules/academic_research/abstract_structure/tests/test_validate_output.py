"""validate_output 契约测试：两个 prompt 的合法/非法输出判定。合成 fixture。"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from validate_output import (  # noqa: E402
    validate_annotation_output,
    validate_rules_output,
)

SENTENCES = [
    {"sentence_id": 1, "text": "We study how training affects earnings using a randomized experiment."},
    {"sentence_id": 2, "text": "Training raises earnings by 5 percent."},
    {"sentence_id": 3, "text": "These gains suggest that training subsidies can improve workers' economic prospects."},
]
ARTICLE_ID = "synthetic_example_001"


def valid_annotation() -> dict:
    return {
        "schema_version": "abstract_structure_v0.1",
        "article_id": ARTICLE_ID,
        "input_issues": [],
        "paper_type": {
            "primary_type": "empirical",
            "empirical_component": "yes",
            "theory_component": "no",
            "structural_component": "no",
            "evidence": [{"sentence_id": 1, "quote": "using a randomized experiment"}],
            "note": "The abstract reports an experimental earnings result.",
        },
        "sentence_annotations": [
            {"sentence_id": 1,
             "functions": [
                 {"label": "what", "evidence": [
                     {"quote": "We study how training affects earnings",
                      "finding_focus": None, "how_aspects": []}]},
                 {"label": "how", "evidence": [
                     {"quote": "using a randomized experiment",
                      "finding_focus": None, "how_aspects": ["design"]}]},
             ],
             "other_content": [], "uncertain_content": [], "connective_only": False},
            {"sentence_id": 2,
             "functions": [
                 {"label": "findings", "evidence": [
                     {"quote": "Training raises earnings by 5 percent.",
                      "finding_focus": "central", "how_aspects": []}]},
             ],
             "other_content": [], "uncertain_content": [], "connective_only": False},
            {"sentence_id": 3,
             "functions": [
                 {"label": "why_it_matters", "evidence": [
                     {"quote": "These gains suggest that training subsidies can improve workers' economic prospects.",
                      "finding_focus": None, "how_aspects": []}]},
             ],
             "other_content": [], "uncertain_content": [], "connective_only": False},
        ],
    }


def _seven_checks() -> list[dict]:
    return [
        {"check_id": "concrete_findings", "applies": "yes",
         "observed_status": "concrete_result",
         "evidence": [{"sentence_id": 2, "quote": "Training raises earnings by 5 percent."}],
         "note": "Quantitative effect stated."},
        {"check_id": "literature_mentions", "applies": "yes", "observed_status": "none",
         "evidence": [], "note": "No literature cited."},
        {"check_id": "passive_voice", "applies": "yes", "observed_status": "absent",
         "evidence": [], "note": "No passive construction found."},
        {"check_id": "jargon_necessity", "applies": "yes", "observed_status": "no_candidate",
         "evidence": [], "note": "No jargon candidate."},
        {"check_id": "identification_keyword", "applies": "yes",
         "observed_status": "named_strategy",
         "evidence": [{"sentence_id": 1, "quote": "a randomized experiment"}],
         "note": "Named experimental design."},
        {"check_id": "theory_mechanism", "applies": "no",
         "observed_status": "not_applicable", "evidence": [],
         "note": "No theory component."},
        {"check_id": "structural_counterfactual", "applies": "no",
         "observed_status": "not_applicable", "evidence": [],
         "note": "No structural model."},
    ]


def valid_rules() -> dict:
    return {
        "schema_version": "abstract_rules_v0.1",
        "article_id": ARTICLE_ID,
        "input_issues": [],
        "scope_evidence": {
            "empirical_component": "yes", "theory_component": "no",
            "structural_component": "no", "causal_design_relevance": "yes",
            "evidence": [{"sentence_id": 1, "quote": "using a randomized experiment"}],
            "note": "Experimental empirical study.",
        },
        "checks": _seven_checks(),
        "jargon_candidates": [],
    }


# ---------------------------------------------------------------------------
# annotation
# ---------------------------------------------------------------------------
def test_annotation_valid():
    r = validate_annotation_output(valid_annotation(), ARTICLE_ID, SENTENCES)
    assert r.ok, r.errors
    assert not r.needs_review


def test_annotation_rejects_wrong_article_id():
    obj = valid_annotation()
    obj["article_id"] = "other_id"
    r = validate_annotation_output(obj, ARTICLE_ID, SENTENCES)
    assert any("article_id" in e for e in r.errors)


def test_annotation_rejects_missing_sentence():
    obj = valid_annotation()
    obj["sentence_annotations"] = obj["sentence_annotations"][:2]
    r = validate_annotation_output(obj, ARTICLE_ID, SENTENCES)
    assert any("句子覆盖" in e for e in r.errors)


def test_annotation_rejects_duplicate_label_in_sentence():
    obj = valid_annotation()
    dup = copy.deepcopy(obj["sentence_annotations"][0]["functions"][0])
    obj["sentence_annotations"][0]["functions"].append(dup)
    r = validate_annotation_output(obj, ARTICLE_ID, SENTENCES)
    assert any("重复 label" in e for e in r.errors)


def test_annotation_rejects_quote_not_substring():
    obj = valid_annotation()
    obj["sentence_annotations"][1]["functions"][0]["evidence"][0]["quote"] = \
        "Training raises earnings by 6 percent."
    r = validate_annotation_output(obj, ARTICLE_ID, SENTENCES)
    assert any("精确子串" in e for e in r.errors)


def test_annotation_rejects_null_finding_focus_on_findings():
    obj = valid_annotation()
    obj["sentence_annotations"][1]["functions"][0]["evidence"][0]["finding_focus"] = None
    r = validate_annotation_output(obj, ARTICLE_ID, SENTENCES)
    assert any("finding_focus" in e for e in r.errors)


def test_annotation_rejects_finding_focus_on_non_findings():
    obj = valid_annotation()
    obj["sentence_annotations"][0]["functions"][0]["evidence"][0]["finding_focus"] = "central"
    r = validate_annotation_output(obj, ARTICLE_ID, SENTENCES)
    assert any("finding_focus" in e for e in r.errors)


def test_annotation_rejects_empty_how_aspects_on_how():
    obj = valid_annotation()
    obj["sentence_annotations"][0]["functions"][1]["evidence"][0]["how_aspects"] = []
    r = validate_annotation_output(obj, ARTICLE_ID, SENTENCES)
    assert any("how_aspects" in e for e in r.errors)


def test_annotation_v03_rejects_mechanism_aspect():
    obj = valid_annotation()
    obj["sentence_annotations"][0]["functions"][1]["evidence"][0]["how_aspects"] = ["mechanism"]
    r_old = validate_annotation_output(obj, ARTICLE_ID, SENTENCES)  # 默认 v0.1 历史行为
    assert r_old.ok
    r_new = validate_annotation_output(obj, ARTICLE_ID, SENTENCES, prompt_version="v0.3")
    assert any("mechanism" in e for e in r_new.errors)


def test_annotation_v03_accepts_four_aspects():
    obj = valid_annotation()
    r = validate_annotation_output(obj, ARTICLE_ID, SENTENCES, prompt_version="v0.3")
    assert r.ok


def test_annotation_rejects_connective_only_inconsistency():
    obj = valid_annotation()
    obj["sentence_annotations"][0]["connective_only"] = True
    r = validate_annotation_output(obj, ARTICLE_ID, SENTENCES)
    assert any("connective_only" in e for e in r.errors)


def test_annotation_rejects_missing_evidence_for_non_unclear_type():
    obj = valid_annotation()
    obj["paper_type"]["evidence"] = []
    r = validate_annotation_output(obj, ARTICLE_ID, SENTENCES)
    assert any("应有证据" in e for e in r.errors)


def test_annotation_ambiguous_quote_position_goes_needs_review():
    # 同句重复片段导致 quote 位置不唯一：标 needs_review，不报错、不任选
    sents = [{"sentence_id": 1, "text": "We find X. We find X again in detail."}]
    obj = valid_annotation()
    obj["sentence_annotations"] = [
        {"sentence_id": 1,
         "functions": [{"label": "findings", "evidence": [
             {"quote": "We find X", "finding_focus": "central", "how_aspects": []}]}],
         "other_content": [], "uncertain_content": [], "connective_only": False},
    ]
    obj["paper_type"]["evidence"] = [{"sentence_id": 1, "quote": "We find X again"}]
    r = validate_annotation_output(obj, ARTICLE_ID, sents)
    assert r.ok, r.errors
    assert any("位置不唯一" in n for n in r.needs_review)


# ---------------------------------------------------------------------------
# rules
# ---------------------------------------------------------------------------
def test_rules_valid():
    r = validate_rules_output(valid_rules(), ARTICLE_ID, SENTENCES)
    assert r.ok, r.errors


def test_rules_rejects_missing_check():
    obj = valid_rules()
    obj["checks"] = [c for c in obj["checks"] if c["check_id"] != "passive_voice"]
    r = validate_rules_output(obj, ARTICLE_ID, SENTENCES)
    assert any("缺少" in e for e in r.errors)


def test_rules_rejects_duplicate_check():
    obj = valid_rules()
    obj["checks"].append(copy.deepcopy(obj["checks"][0]))
    r = validate_rules_output(obj, ARTICLE_ID, SENTENCES)
    assert any("重复" in e for e in r.errors)


def test_rules_rejects_illegal_status_enum():
    obj = valid_rules()
    obj["checks"][0]["observed_status"] = "very_concrete"
    r = validate_rules_output(obj, ARTICLE_ID, SENTENCES)
    assert any("observed_status" in e for e in r.errors)


def test_rules_applies_no_requires_not_applicable():
    obj = valid_rules()
    for c in obj["checks"]:
        if c["check_id"] == "theory_mechanism":
            c["observed_status"] = "absent"
    r = validate_rules_output(obj, ARTICLE_ID, SENTENCES)
    assert any("not_applicable" in e for e in r.errors)


def test_rules_applies_yes_forbids_not_applicable():
    obj = valid_rules()
    obj["checks"][0]["observed_status"] = "not_applicable"
    r = validate_rules_output(obj, ARTICLE_ID, SENTENCES)
    assert r.errors


def test_rules_applies_unclear_requires_unclear_status_and_reason():
    obj = valid_rules()
    obj["scope_evidence"]["theory_component"] = "unclear"
    for c in obj["checks"]:
        if c["check_id"] == "theory_mechanism":
            c["applies"] = "unclear"
            c["observed_status"] = "absent"  # 非法：必须为 unclear
            c["note"] = ""
    r = validate_rules_output(obj, ARTICLE_ID, SENTENCES)
    assert any("applies=unclear" in e for e in r.errors)


def test_rules_applies_scope_inconsistent():
    obj = valid_rules()
    for c in obj["checks"]:
        if c["check_id"] == "theory_mechanism":
            c["applies"] = "yes"  # scope 里 theory_component=no，不一致
            c["observed_status"] = "named_force"
    r = validate_rules_output(obj, ARTICLE_ID, SENTENCES)
    assert any("不一致" in e for e in r.errors)


def test_rules_jargon_status_candidate_mismatch():
    obj = valid_rules()
    for c in obj["checks"]:
        if c["check_id"] == "jargon_necessity":
            c["observed_status"] = "candidates_only"
    # jargon_candidates 仍为空 → 不合法
    r = validate_rules_output(obj, ARTICLE_ID, SENTENCES)
    assert any("jargon_candidates 必须非空" in e for e in r.errors)


def test_rules_jargon_potentially_avoidable_requires_simpler_yes():
    obj = valid_rules()
    for c in obj["checks"]:
        if c["check_id"] == "jargon_necessity":
            c["observed_status"] = "potentially_avoidable"
    obj["jargon_candidates"] = [
        {"sentence_id": 1, "quote": "randomized experiment",
         "explained_in_abstract": "no", "simpler_expression_possible": "no",
         "note": "Technical term."},
    ]
    r = validate_rules_output(obj, ARTICLE_ID, SENTENCES)
    assert any("simpler_expression_possible" in e for e in r.errors)


def test_rules_rejects_evidence_quote_mismatch():
    obj = valid_rules()
    obj["checks"][0]["evidence"] = [{"sentence_id": 1, "quote": "Training raises earnings"}]
    r = validate_rules_output(obj, ARTICLE_ID, SENTENCES)
    # quote 存在于 sentence 2 而非 sentence 1
    assert any("精确子串" in e for e in r.errors)
