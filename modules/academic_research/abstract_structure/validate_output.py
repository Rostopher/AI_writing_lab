"""LLM 输出校验器：JSON Schema 结构校验 + 语义校验。

覆盖两个 prompt 的完整契约：
- validate_annotation_output：abstract_structure_v0.1（结构标注）
- validate_rules_output：abstract_rules_v0.1（规则审查）

返回 ValidationResult(errors, needs_review)。
errors 非空即契约失败；needs_review 列出需人工复核但不构成契约失败的情形
（如 quote 在同句内位置不唯一）。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import jsonschema

SCHEMA_VERSION_ANNOTATION = "abstract_structure_v0.1"
SCHEMA_VERSION_RULES = "abstract_rules_v0.1"

FUNCTION_LABELS = {"what", "how", "findings", "why_it_matters"}
FINDING_FOCUS = {"central", "secondary", "unclear"}
HOW_ASPECTS = {"data", "design", "model", "mechanism", "other_method"}
# v0.3 起 how_aspects 收窄为四项：机制性答案归 findings，不再是 how 的 aspect。
# 历史枚举保留在 JSON Schema 中（旧 v0.1/v0.2 结果仍可读），版本化语义检查在
# validate_annotation_output 的 prompt_version 参数中实现。
HOW_ASPECTS_V03 = {"data", "design", "model", "other_method"}
PRIMARY_TYPES = {"empirical", "theory", "mixed_or_structural", "methods", "unclear"}
COMPONENT_STATUS = {"yes", "no", "unclear"}
APPLIES = {"yes", "no", "unclear"}

CHECK_STATUSES: dict[str, set[str]] = {
    "concrete_findings": {"concrete_result", "vague_result_only", "purpose_only",
                          "no_result_statement", "unclear"},
    "literature_mentions": {"none", "brief_prior_finding_for_puzzle_only",
                            "other_literature_mention", "unclear"},
    "passive_voice": {"present", "absent", "unclear"},
    "jargon_necessity": {"no_candidate", "candidates_only", "potentially_avoidable", "unclear"},
    "identification_keyword": {"named_strategy", "design_described_without_name",
                               "absent", "unclear", "not_applicable"},
    "theory_mechanism": {"named_force", "mechanism_described", "absent", "unclear",
                         "not_applicable"},
    "structural_counterfactual": {"explicit_counterfactual_result",
                                  "counterfactual_planned_only", "absent", "unclear",
                                  "not_applicable"},
}
# 类型依赖检查 → 对应 scope component
CHECK_SCOPE_COMPONENT = {
    "identification_keyword": "empirical_component",
    "theory_mechanism": "theory_component",
    "structural_counterfactual": "structural_component",
}
ALWAYS_APPLY_CHECKS = {"concrete_findings", "literature_mentions", "passive_voice",
                       "jargon_necessity"}

_EVIDENCE_ITEM = {
    "type": "object",
    "required": ["sentence_id", "quote"],
    "properties": {
        "sentence_id": {"type": "integer"},
        "quote": {"type": "string", "minLength": 1},
    },
    "additionalProperties": False,
}

ANNOTATION_SCHEMA: dict = {
    "type": "object",
    "required": ["schema_version", "article_id", "input_issues", "paper_type",
                 "sentence_annotations"],
    "properties": {
        "schema_version": {"const": SCHEMA_VERSION_ANNOTATION},
        "article_id": {"type": "string", "minLength": 1},
        "input_issues": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["sentence_id", "issue"],
                "properties": {
                    "sentence_id": {"type": ["integer", "null"]},
                    "issue": {"type": "string", "minLength": 1},
                },
                "additionalProperties": False,
            },
        },
        "paper_type": {
            "type": "object",
            "required": ["primary_type", "empirical_component", "theory_component",
                         "structural_component", "evidence", "note"],
            "properties": {
                "primary_type": {"enum": sorted(PRIMARY_TYPES)},
                "empirical_component": {"enum": sorted(COMPONENT_STATUS)},
                "theory_component": {"enum": sorted(COMPONENT_STATUS)},
                "structural_component": {"enum": sorted(COMPONENT_STATUS)},
                "evidence": {"type": "array", "items": _EVIDENCE_ITEM},
                "note": {"type": "string"},
            },
            "additionalProperties": False,
        },
        "sentence_annotations": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["sentence_id", "functions", "other_content",
                             "uncertain_content", "connective_only"],
                "properties": {
                    "sentence_id": {"type": "integer"},
                    "functions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["label", "evidence"],
                            "properties": {
                                "label": {"enum": sorted(FUNCTION_LABELS)},
                                "evidence": {
                                    "type": "array",
                                    "minItems": 1,
                                    "items": {
                                        "type": "object",
                                        "required": ["quote", "finding_focus", "how_aspects"],
                                        "properties": {
                                            "quote": {"type": "string", "minLength": 1},
                                            "finding_focus": {
                                                "enum": sorted(FINDING_FOCUS) + [None]
                                            },
                                            "how_aspects": {
                                                "type": "array",
                                                "items": {"enum": sorted(HOW_ASPECTS)},
                                                "uniqueItems": True,
                                            },
                                        },
                                        "additionalProperties": False,
                                    },
                                },
                            },
                            "additionalProperties": False,
                        },
                    },
                    "other_content": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["quote", "function_description"],
                            "properties": {
                                "quote": {"type": "string", "minLength": 1},
                                "function_description": {"type": "string", "minLength": 1},
                            },
                            "additionalProperties": False,
                        },
                    },
                    "uncertain_content": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["quote", "candidate_functions", "reason"],
                            "properties": {
                                "quote": {"type": "string", "minLength": 1},
                                "candidate_functions": {
                                    "type": "array",
                                    "minItems": 1,
                                    "items": {"enum": sorted(FUNCTION_LABELS | {"other"})},
                                },
                                "reason": {"type": "string", "minLength": 1},
                            },
                            "additionalProperties": False,
                        },
                    },
                    "connective_only": {"type": "boolean"},
                },
                "additionalProperties": False,
            },
        },
    },
    "additionalProperties": False,
}

RULES_SCHEMA: dict = {
    "type": "object",
    "required": ["schema_version", "article_id", "input_issues", "scope_evidence",
                 "checks", "jargon_candidates"],
    "properties": {
        "schema_version": {"const": SCHEMA_VERSION_RULES},
        "article_id": {"type": "string", "minLength": 1},
        "input_issues": ANNOTATION_SCHEMA["properties"]["input_issues"],
        "scope_evidence": {
            "type": "object",
            "required": ["empirical_component", "theory_component",
                         "structural_component", "causal_design_relevance",
                         "evidence", "note"],
            "properties": {
                "empirical_component": {"enum": sorted(COMPONENT_STATUS)},
                "theory_component": {"enum": sorted(COMPONENT_STATUS)},
                "structural_component": {"enum": sorted(COMPONENT_STATUS)},
                "causal_design_relevance": {"enum": sorted(COMPONENT_STATUS)},
                "evidence": {"type": "array", "items": _EVIDENCE_ITEM},
                "note": {"type": "string"},
            },
            "additionalProperties": False,
        },
        "checks": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["check_id", "applies", "observed_status", "evidence", "note"],
                "properties": {
                    "check_id": {"enum": sorted(CHECK_STATUSES)},
                    "applies": {"enum": sorted(APPLIES)},
                    "observed_status": {"type": "string"},
                    "evidence": {"type": "array", "items": _EVIDENCE_ITEM},
                    "note": {"type": "string"},
                },
                "additionalProperties": False,
            },
        },
        "jargon_candidates": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["sentence_id", "quote", "explained_in_abstract",
                             "simpler_expression_possible", "note"],
                "properties": {
                    "sentence_id": {"type": "integer"},
                    "quote": {"type": "string", "minLength": 1},
                    "explained_in_abstract": {"enum": sorted(COMPONENT_STATUS)},
                    "simpler_expression_possible": {"enum": sorted(COMPONENT_STATUS)},
                    "note": {"type": "string"},
                },
                "additionalProperties": False,
            },
        },
    },
    "additionalProperties": False,
}


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    needs_review: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _schema_errors(obj: object, schema: dict) -> list[str]:
    v = jsonschema.Draft202012Validator(schema)
    return [f"schema: {e.json_path}: {e.message}" for e in v.iter_errors(obj)]


def _check_quote(result: ValidationResult, quote: str, sentence_text: str, where: str) -> None:
    """quote 必须是对应句的非空精确子串；同句多次出现导致位置不唯一时标 needs_review。"""
    if not quote:
        result.errors.append(f"{where}: 空 quote")
        return
    n = sentence_text.count(quote)
    if n == 0:
        result.errors.append(f"{where}: quote 不是对应句的精确子串: {quote[:60]!r}")
    elif n > 1:
        result.needs_review.append(
            f"{where}: quote 在同句内出现 {n} 次，位置不唯一: {quote[:60]!r}"
        )


def _version_tuple(prompt_version: str) -> tuple[int, ...]:
    m = re.match(r"v?(\d+(?:\.\d+)*)", prompt_version)
    if not m:
        raise ValueError(f"无法解析 prompt 版本: {prompt_version!r}")
    return tuple(int(x) for x in m.group(1).split("."))


def validate_annotation_output(obj: object, article_id: str,
                               sentences: list[dict],
                               prompt_version: str = "v0.1") -> ValidationResult:
    """结构标注输出校验。sentences 为输入的 [{sentence_id, text, ...}]。

    prompt_version >= v0.3 时 how_aspects 不允许 mechanism（v0.3 口径：
    机制性答案归 findings）；默认 v0.1 保持历史行为，旧结果可读。"""
    result = ValidationResult()
    result.errors.extend(_schema_errors(obj, ANNOTATION_SCHEMA))
    if result.errors:
        return result
    assert isinstance(obj, dict)

    if obj["article_id"] != article_id:
        result.errors.append(
            f"article_id 回显不符: 输入 {article_id!r} 输出 {obj['article_id']!r}")

    sent_by_id = {s["sentence_id"]: s["text"] for s in sentences}
    anns = obj["sentence_annotations"]
    out_ids = [a["sentence_id"] for a in anns]
    in_ids = [s["sentence_id"] for s in sentences]
    if out_ids != in_ids:
        result.errors.append(
            f"句子覆盖不符（需全覆盖、不重复、按输入顺序）: 输入 {in_ids} 输出 {out_ids}")
        return result  # 句子对不齐时后续定位无意义

    for ann in anns:
        sid = ann["sentence_id"]
        text = sent_by_id[sid]
        labels = [f["label"] for f in ann["functions"]]
        if len(labels) != len(set(labels)):
            result.errors.append(f"sentence {sid}: 同句重复 label")

        for fobj in ann["functions"]:
            label = fobj["label"]
            for ev in fobj["evidence"]:
                where = f"sentence {sid} function {label}"
                _check_quote(result, ev["quote"], text, where)
                if label == "findings":
                    if ev["finding_focus"] not in FINDING_FOCUS:
                        result.errors.append(f"{where}: findings 证据必须有非 null finding_focus")
                    if ev["how_aspects"]:
                        result.errors.append(f"{where}: 非 how 证据 how_aspects 必须为 []")
                elif label == "how":
                    if ev["finding_focus"] is not None:
                        result.errors.append(f"{where}: 非 findings 证据 finding_focus 必须为 null")
                    if not ev["how_aspects"]:
                        result.errors.append(f"{where}: how 证据必须有非空 how_aspects")
                    if (_version_tuple(prompt_version) >= (0, 3)
                            and "mechanism" in ev["how_aspects"]):
                        result.errors.append(
                            f"{where}: {prompt_version} 起 how_aspects 不含 mechanism"
                            "（机制性答案归 findings；仅作为模型设定出现的机制归 aspect model）")
                else:
                    if ev["finding_focus"] is not None:
                        result.errors.append(f"{where}: 非 findings 证据 finding_focus 必须为 null")
                    if ev["how_aspects"]:
                        result.errors.append(f"{where}: 非 how 证据 how_aspects 必须为 []")

        for oc in ann["other_content"]:
            _check_quote(result, oc["quote"], text, f"sentence {sid} other_content")
        for uc in ann["uncertain_content"]:
            _check_quote(result, uc["quote"], text, f"sentence {sid} uncertain_content")

        n_items = len(ann["functions"]) + len(ann["other_content"]) + len(ann["uncertain_content"])
        if ann["connective_only"] and n_items > 0:
            result.errors.append(
                f"sentence {sid}: connective_only=true 时三个标注列表必须均为空")
        if not ann["connective_only"] and n_items == 0:
            result.errors.append(
                f"sentence {sid}: connective_only=false 时至少需一个标注项")

    pt = obj["paper_type"]
    for ev in pt["evidence"]:
        if ev["sentence_id"] not in sent_by_id:
            result.errors.append(f"paper_type 证据 sentence_id 不存在: {ev['sentence_id']}")
        else:
            _check_quote(result, ev["quote"], sent_by_id[ev["sentence_id"]],
                         "paper_type evidence")
    if pt["primary_type"] != "unclear" and not pt["evidence"]:
        result.errors.append("非 unclear 的 primary_type 应有证据")

    return result


def validate_rules_output(obj: object, article_id: str,
                          sentences: list[dict]) -> ValidationResult:
    """规则审查输出校验。"""
    result = ValidationResult()
    result.errors.extend(_schema_errors(obj, RULES_SCHEMA))
    if result.errors:
        return result
    assert isinstance(obj, dict)

    if obj["article_id"] != article_id:
        result.errors.append(
            f"article_id 回显不符: 输入 {article_id!r} 输出 {obj['article_id']!r}")

    sent_by_id = {s["sentence_id"]: s["text"] for s in sentences}

    scope = obj["scope_evidence"]
    for ev in scope["evidence"]:
        if ev["sentence_id"] not in sent_by_id:
            result.errors.append(f"scope_evidence 证据 sentence_id 不存在: {ev['sentence_id']}")
        else:
            _check_quote(result, ev["quote"], sent_by_id[ev["sentence_id"]],
                         "scope_evidence")

    checks = obj["checks"]
    ids = [c["check_id"] for c in checks]
    if len(ids) != len(set(ids)):
        result.errors.append(f"checks 存在重复 check_id: {sorted(ids)}")
    missing = set(CHECK_STATUSES) - set(ids)
    extra = set(ids) - set(CHECK_STATUSES)
    if missing:
        result.errors.append(f"checks 缺少: {sorted(missing)}")
    if extra:
        result.errors.append(f"checks 多出未知 check_id: {sorted(extra)}")

    jargon_status = None
    for c in checks:
        cid = c["check_id"]
        if c["observed_status"] not in CHECK_STATUSES.get(cid, set()):
            result.errors.append(
                f"check {cid}: observed_status 非法: {c['observed_status']!r}")
        applies, status = c["applies"], c["observed_status"]
        if applies == "no" and status != "not_applicable":
            result.errors.append(f"check {cid}: applies=no 时状态必须为 not_applicable")
        if applies == "unclear":
            if status != "unclear":
                result.errors.append(f"check {cid}: applies=unclear 时状态必须为 unclear")
            if not c["note"].strip():
                result.errors.append(f"check {cid}: applies=unclear 必须给出 reason(note)")
        if applies == "yes" and status == "not_applicable":
            result.errors.append(f"check {cid}: applies=yes 禁止 not_applicable")
        # applies 与 scope_evidence 一致
        if cid in CHECK_SCOPE_COMPONENT:
            comp = scope[CHECK_SCOPE_COMPONENT[cid]]
            expected = {"yes": "yes", "no": "no", "unclear": "unclear"}[comp]
            if applies != expected:
                result.errors.append(
                    f"check {cid}: applies={applies} 与 "
                    f"{CHECK_SCOPE_COMPONENT[cid]}={comp} 不一致")
        if cid in ALWAYS_APPLY_CHECKS and applies != "yes":
            result.errors.append(f"check {cid}: 该检查 applies 恒为 yes，实际 {applies}")
        for ev in c["evidence"]:
            if ev["sentence_id"] not in sent_by_id:
                result.errors.append(f"check {cid} 证据 sentence_id 不存在: {ev['sentence_id']}")
            else:
                _check_quote(result, ev["quote"], sent_by_id[ev["sentence_id"]],
                             f"check {cid} evidence")
        if cid == "jargon_necessity":
            jargon_status = c["observed_status"]

    jc = obj["jargon_candidates"]
    for cand in jc:
        if cand["sentence_id"] not in sent_by_id:
            result.errors.append(
                f"jargon_candidates sentence_id 不存在: {cand['sentence_id']}")
        else:
            _check_quote(result, cand["quote"], sent_by_id[cand["sentence_id"]],
                         "jargon_candidates")
    if jargon_status == "no_candidate" and jc:
        result.errors.append("jargon_necessity=no_candidate 时 jargon_candidates 必须为空")
    if jargon_status in ("candidates_only", "potentially_avoidable") and not jc:
        result.errors.append(
            f"jargon_necessity={jargon_status} 时 jargon_candidates 必须非空")
    if jargon_status == "potentially_avoidable" and not any(
            c["simpler_expression_possible"] == "yes" for c in jc):
        result.errors.append(
            "jargon_necessity=potentially_avoidable 需至少一个 simpler_expression_possible=yes")

    return result
