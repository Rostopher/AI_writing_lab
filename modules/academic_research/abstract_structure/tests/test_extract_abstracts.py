"""extract_abstracts 契约测试：合成上游树保护五刊适配、类型排除、去重版本冲突。
真实上游仅作 smoke（根目录不存在时 skip）。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import extract_abstracts as ea  # noqa: E402


def _write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")


@pytest.fixture()
def synthetic_upstream(tmp_path: Path) -> Path:
    root = tmp_path / "top_journal_dataset"

    # --- AER：期级 list，含 front matter、comment、普通文章 ---
    aer = root / "AER" / "AER202001_1"
    _write_json(aer / "article_metadata.json", [
        {"index": 1, "title": "Front Matter", "authors": [], "is_front_matter": True,
         "abstract": "", "doi": "10.1257/aer.110.1.i", "journal": "American Economic Review",
         "publication_date": "2020/01", "volume": "110", "issue": "1", "pages": "i-vi"},
        {"index": 2, "title": "Real Research Paper", "authors": ["Doe, J"],
         "is_front_matter": False, "abstract": "We study X. We find Y.", 
         "doi": "https://doi.org/10.1257/aer.20190001 ", "journal": "American Economic Review",
         "publication_date": "2020/01", "volume": "110", "issue": "1", "pages": "1-30"},
        {"index": 3, "title": "Real Research Paper: Comment", "authors": ["Roe, K"],
         "is_front_matter": False, "abstract": "This comment argues Z.",
         "doi": "10.1257/aer.20190002", "journal": "American Economic Review",
         "publication_date": "2020/01", "volume": "110", "issue": "1", "pages": "31-40"},
    ])
    # AER 重复 DOI 的另一期（版本冲突）
    aer2 = root / "AER" / "AER202002_2"
    _write_json(aer2 / "article_metadata.json", [
        {"index": 1, "title": "Real Research Paper", "authors": ["Doe, J"],
         "is_front_matter": False, "abstract": "We study X. We find Y.",
         "doi": "10.1257/AER.20190001", "journal": "American Economic Review",
         "publication_date": "2020/02", "volume": "110", "issue": "2", "pages": "1-30"},
    ])
    # P&P 整期排除目录（应不出现在台账）
    pp = root / "AER" / "AER201505_5"
    _write_json(pp / "article_metadata.json", [
        {"index": 1, "title": "Some P&P Paper", "is_front_matter": False,
         "abstract": "Short.", "doi": "10.1257/aer.p2015", "journal": "AER"},
    ])

    # --- ECMA：期级 dict（带重复条目），篇级 page.html ---
    ecma = root / "ECMA" / "ECMA202001_1"
    _write_json(ecma / "article_metadata.json", {
        "kind": "article_metadata",
        "articles": [
            {"title": "Networks Paper", "authors": ["A"], "doi": "", "href": "h1",
             "volume": "88", "issue": "1", "year": "2020", "month": "01", "pages": "1-32"},
            {"title": "Networks Paper", "authors": ["A"], "doi": "", "href": "h1",
             "volume": "88", "issue": "1", "year": "2020", "month": "01", "pages": "1-32"},
            {"title": "Forthcoming Papers", "authors": [], "doi": "", "href": "h2",
             "volume": "88", "issue": "1", "year": "2020", "month": "01", "pages": "i-ii"},
        ]})
    sub = ecma / "article_metadata" / "ecta00001"
    _write_json(sub / "article_content.json", {
        "title": "Networks Paper", "doi": "10.3982/ECTA00001", "authors": ["A"],
        "publication_date": "2020/01/01", "online_date": "2019-06-01",
        "volume": "88", "issue": "1"})
    (sub / "page.html").write_text(
        '<html><head><meta name="description" content="We model networks. We find contagion...'
        '"></head><body><section class="article-section__abstract main">'
        '<h2 class="article-section__header">Abstract</h2>'
        '<div><p>We model networks. We find contagion.</p></div></section></body></html>',
        encoding="utf-8")

    # --- JPE：doi 后缀即目录名，abstract 带 "Abstract " 前缀 ---
    jpe = root / "JPE" / "JPE202002_2"
    _write_json(jpe / "article_metadata.json", {"articles": [
        {"title": "Gravity Paper", "doi": "10.1086/704385", "abstract": "We study gravity.",
         "volume": "128", "issue": "2", "year": "2020", "month": "February", "pages": "1-30"},
        {"title": "Masthead", "doi": "10.1086/708480", "abstract": "",
         "volume": "128", "issue": "2", "year": "2020", "month": "February", "pages": "i-ii"},
    ]})
    _write_json(jpe / "article_metadata" / "704385" / "article_content.json", {
        "kind": "article_content",
        "abstract": "Abstract We study gravity. We find it matters."})

    # --- QJE：article_metadata_dir 字段，sections 中 kind=abstract ---
    qje = root / "QJE" / "QJE202002_1"
    _write_json(qje / "article_metadata.json", {"articles": [
        {"title": "Demonetization Paper", "doi": "10.1093/qje/qjz027",
         "article_metadata_dir": str(qje / "article_metadata" / "qjz027"),
         "volume": "135", "issue": "1", "year": "2020", "month": "February",
         "pages": "57-103"},
    ]})
    _write_json(qje / "article_metadata" / "qjz027" / "article_content.json", {
        "kind": "article_content",
        "sections": [
            {"kind": "abstract", "text": "We analyze demonetization. We find large effects."},
            {"kind": "body", "text": "1. Introduction"},
        ]})
    # --- REStud：同 QJE 形态 ---
    res = root / "REStud" / "REStud202001_1"
    _write_json(res / "article_metadata.json", {"articles": [
        {"title": "Carbon Tax Paper", "doi": "10.1093/restud/rdz055",
         "article_metadata_dir": str(res / "article_metadata" / "rdz055"),
         "volume": "87", "issue": "1", "year": "2020", "month": "January",
         "pages": "1-40"},
    ]})
    _write_json(res / "article_metadata" / "rdz055" / "article_content.json", {
        "kind": "article_content",
        "sections": [
            {"kind": "abstract", "text": "How should carbon be taxed? We derive optimal taxes."},
        ]})
    return root


def test_run_synthetic(synthetic_upstream: Path, tmp_path: Path):
    out_root = tmp_path / "out"
    stats = ea.run(synthetic_upstream, out_root, "run_test")
    manifest = out_root / "run_test" / "corpus_manifest.jsonl"
    assert manifest.exists()
    records = [json.loads(l) for l in manifest.read_text(encoding="utf-8").splitlines()]

    # P&P 期目录不进入台账
    assert all(r["issue_dir"] != "AER201505_5" for r in records)
    # 期刊数
    assert {r["journal_code"] for r in records} == {"AER", "ECMA", "JPE", "QJE", "REStud"}

    by_id = {r["article_id"]: r for r in records}

    # DOI 规范化：去 URL 前缀、去首尾空白、小写
    assert "AER:10.1257/aer.20190001" in by_id
    # 版本冲突：两条记录，仅一条 selected
    dup = [r for r in records if r["doi_normalized"] == "10.1257/aer.20190001"]
    assert len(dup) == 2
    assert sum(1 for r in dup if r["selected"]) == 1
    assert all(r["version_conflict"] for r in dup)
    assert stats["n_doi_conflict_groups"] == 1

    # 类型排除
    assert "front_matter" in by_id["AER:10.1257/aer.110.1.i"]["exclusion_reason"]
    assert by_id["AER:10.1257/aer.20190002"]["exclusion_reason"] == "excluded_type:comment_reply"
    assert "front_matter" in by_id["JPE:10.1086/708480"]["exclusion_reason"]
    ecma_forth = [r for r in records if r["journal_code"] == "ECMA"
                  and r["title"] == "Forthcoming Papers"]
    assert ecma_forth and ecma_forth[0]["exclusion_reason"] == "excluded_type:forthcoming_papers"

    # ECMA：期级重复条目已去重（Networks Paper 只出现一次）
    ecma_net = [r for r in records if r["journal_code"] == "ECMA"
                and r["title"] == "Networks Paper"]
    assert len(ecma_net) == 1
    rec = ecma_net[0]
    assert rec["availability"] == "available"
    assert rec["abstract_normalized"] == "We model networks. We find contagion."
    assert "html_tags_removed" in rec["cleaning_log"]
    assert "strip_abstract_prefix" in rec["cleaning_log"]
    assert rec["online_date"] == "2019-06-01"
    assert rec["sentence_count"] == 2
    norm = rec["abstract_normalized"]
    for s in rec["sentences"]:
        assert norm[s["start"]:s["end"]] == s["text"]

    # JPE：前缀剥除并记录
    jpe_rec = by_id["JPE:10.1086/704385"]
    assert jpe_rec["abstract_raw"].startswith("Abstract ")
    assert jpe_rec["abstract_normalized"] == "We study gravity. We find it matters."
    assert "strip_abstract_prefix" in jpe_rec["cleaning_log"]

    # QJE：sections 抽取
    qje_rec = by_id["QJE:10.1093/qje/qjz027"]
    assert qje_rec["availability"] == "available"
    assert qje_rec["word_count_v1"] == 7

    # 来源 hash 齐全
    for r in records:
        assert set(r["source_sha256"]) == set(r["source_files"])

    # run_manifest 写出
    rm = json.loads((out_root / "run_test" / "run_manifest.json").read_text(encoding="utf-8"))
    assert rm["versions"]["word_count"] == "v1"
    assert any(e["status"] == "excluded_issue" for e in rm["issue_log"])


def test_oup_subscription_boilerplate_truncated(tmp_path: Path):
    """OUP 订阅样板截断：boilerplate 在中段、后接卷首语等内容时，截断处之前才是摘要。"""
    root = tmp_path / "top_journal_dataset"
    qje = root / "QJE" / "QJE202002_1"
    _write_json(qje / "article_metadata.json", {"articles": [
        {"title": "Boilerplate Case", "doi": "10.1093/qje/qjz999",
         "article_metadata_dir": str(qje / "article_metadata" / "qjz999"),
         "volume": "135", "issue": "1", "year": "2020", "month": "February",
         "pages": "1-20"},
    ]})
    _write_json(qje / "article_metadata" / "qjz999" / "article_content.json", {
        "kind": "article_content",
        "sections": [
            {"kind": "abstract",
             "text": "We study X. We find Y. "
                     "As a benefit of your subscription, you can share temporary access "
                     "to restricted articles. Front Matter Editor's note and more body text."},
        ]})
    stats = ea.run(root, tmp_path / "out", "run_bp", journals=["QJE"])
    rec = json.loads((tmp_path / "out" / "run_bp" / "corpus_manifest.jsonl")
                     .read_text(encoding="utf-8").strip())
    assert rec["abstract_normalized"] == "We study X. We find Y."
    assert "oup_subscription_boilerplate_removed" in rec["anomalies"]
    assert rec["availability"] == "available"


def test_bad_issue_json_recorded_not_silent(synthetic_upstream: Path, tmp_path: Path):
    (synthetic_upstream / "QJE" / "QJE202002_1" / "article_metadata.json").write_text(
        "{bad json", encoding="utf-8")
    stats = ea.run(synthetic_upstream, tmp_path / "out", "run_bad")
    assert stats["n_issues_error"] >= 1


@pytest.mark.skipif(ea.UPSTREAM_ROOT is None or not ea.UPSTREAM_ROOT.is_dir(),
                    reason="上游数据根目录未配置或不存在")
def test_real_upstream_smoke():
    """真实上游 smoke：每刊抽一期验证适配器不抛错。"""
    for journal, extractor in ea.EXTRACTORS.items():
        issue = next(ea.iter_issue_dirs(ea.UPSTREAM_ROOT, journal))
        if issue[0] in ea.EXCLUDED_ISSUES:
            continue
        arts, _anom = extractor(issue[0], issue[1], ea.UPSTREAM_ROOT)
        assert isinstance(arts, list)
