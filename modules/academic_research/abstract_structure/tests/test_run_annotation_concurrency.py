"""run_annotation 并发执行测试：假客户端（不发起真实 API 调用）。"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import run_annotation as ra  # noqa: E402

VALID_OUTPUT = {
    "schema_version": "abstract_structure_v0.1",
    "article_id": None,  # 运行时替换
    "input_issues": [],
    "paper_type": {
        "primary_type": "empirical",
        "empirical_component": "yes",
        "theory_component": "no",
        "structural_component": "no",
        "evidence": [{"sentence_id": 1, "quote": "We study X"}],
        "note": "synthetic",
    },
    "sentence_annotations": [
        {"sentence_id": 1,
         "functions": [{"label": "what", "evidence": [
             {"quote": "We study X", "finding_focus": None, "how_aspects": []}]}],
         "other_content": [], "uncertain_content": [], "connective_only": False},
    ],
}


class FakeClient:
    def __init__(self, delay: float = 0.05):
        self.delay = delay
        self.model = "deepseek-v4-flash"

    def chat(self, system_prompt, user_payload, norm_text_hash, splitter_version):
        time.sleep(self.delay)
        obj = json.loads(json.dumps(VALID_OUTPUT))
        obj["article_id"] = user_payload["article_id"]
        return {"content": json.dumps(obj), "usage": {"total_tokens": 10},
                "cost_cny": 0.001, "model_returned": "deepseek-v4-flash",
                "cache_key": "fake", "cached": False, "json_object_mode": True}


def _corpus(n: int) -> dict[str, dict]:
    return {f"A{i}": {"selected": True, "included": True,
                      "availability": "available",
                      "sentences": [{"sentence_id": 1, "text": "We study X"}],
                      "abstract_norm_sha256": "h"}
            for i in range(n)}


def test_concurrent_run_matches_serial_results(tmp_path):
    corpus = _corpus(12)
    for concurrency in (1, 4):
        run_dir = tmp_path / f"c{concurrency}"
        run_dir.mkdir()
        stats = ra.run("annotation", list(corpus), corpus, "sys",
                       FakeClient(), run_dir, concurrency=concurrency)
        assert stats["n_total"] == 12
        assert stats["n_success_original"] == 12
        assert stats["n_failed"] == 0 and stats["n_skipped"] == 0
        lines = (run_dir / "annotations.jsonl").read_text(encoding="utf-8").splitlines()
        assert len(lines) == 12
        assert {json.loads(l)["article_id"] for l in lines} == set(corpus)
        assert not (run_dir / "failures.jsonl").read_text(encoding="utf-8")


def test_resume_skips_already_annotated(tmp_path):
    """annotations.jsonl 已有的 article_id 被跳过；残缺行容忍且对应文章重跑。"""
    corpus = _corpus(5)
    run_dir = tmp_path / "r"
    run_dir.mkdir()
    done = json.loads(json.dumps(VALID_OUTPUT))
    done["article_id"] = "A0"
    (run_dir / "annotations.jsonl").write_text(
        json.dumps({"article_id": "A0", "output": done}) + "\n"
        + '{"article_id": "A1", "output": ' + "\n",  # 掐断的残缺行
        encoding="utf-8")
    stats = ra.run("annotation", list(corpus), corpus, "sys",
                   FakeClient(delay=0), run_dir, concurrency=3)
    assert stats["n_resume_skipped"] == 1
    assert stats["n_total"] == 4  # A0 跳过，A1（残缺）与其余正常重跑
    assert stats["n_success_original"] == 4
    ids = {json.loads(l)["article_id"]
           for l in (run_dir / "annotations.jsonl").read_text(encoding="utf-8").splitlines()
           if l.strip() and l.endswith("}")}
    assert ids == set(corpus)


def test_concurrent_run_is_faster_than_serial(tmp_path):
    corpus = _corpus(8)
    (tmp_path / "s").mkdir()
    (tmp_path / "p").mkdir()
    t0 = time.monotonic()
    ra.run("annotation", list(corpus), corpus, "sys",
           FakeClient(delay=0.1), tmp_path / "s", concurrency=1)
    serial = time.monotonic() - t0
    t0 = time.monotonic()
    ra.run("annotation", list(corpus), corpus, "sys",
           FakeClient(delay=0.1), tmp_path / "p", concurrency=8)
    parallel = time.monotonic() - t0
    assert parallel < serial / 2
