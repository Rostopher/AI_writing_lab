# v0.3 独立验证抽样：每刊 20 篇，seed 20260909，合格框架（included & available）内随机抽取。
# 独立口径（设计 v0.3 §199/§268）：排除 dev 16 篇与 v0.2 pilot 100 篇
# （25 篇审核子集在 pilot 内部，随 pilot 一并排除）；这些文章是 v0.2/v0.3 的
# 开发/配对诊断材料，不能再当独立验证样本。
import json
import random
from pathlib import Path

CORPUS_RUN = Path(__file__).resolve().parents[3] / "data/processed/abstract_structure/run_20260908_a"
OUT_DIR = Path(__file__).resolve().parents[3] / "data/processed/abstract_structure/run_20260909_v03_validation"
SEED = 20260909
PER_JOURNAL = 20

corpus = [json.loads(l) for l in (CORPUS_RUN / "corpus_manifest.jsonl").open(encoding="utf-8")]
dev_ids = {json.loads(l)["article_id"] for l in (CORPUS_RUN / "dev_set_manifest.jsonl").open(encoding="utf-8")}
pilot_ids = {json.loads(l)["article_id"] for l in (CORPUS_RUN / "pilot_sample_manifest.jsonl").open(encoding="utf-8")}
excluded = dev_ids | pilot_ids

eligible = [r for r in corpus
            if r["included"] and r["availability"] == "available"
            and r["article_id"] not in excluded]

picked_all, report = [], {}
for j in ["AER", "ECMA", "JPE", "QJE", "REStud"]:
    pool = sorted((r for r in eligible if r["journal_code"] == j),
                  key=lambda r: r["article_id"])  # 抽样前排序键
    rng = random.Random(f"{SEED}:{j}")
    picked = rng.sample(pool, PER_JOURNAL)
    picked_all.extend(picked)
    years = sorted({r["year"] for r in picked})
    report[j] = {"pool": len(pool), "picked": len(picked), "year_range": [years[0], years[-1]]}

OUT_DIR.mkdir(parents=True, exist_ok=True)
with (OUT_DIR / "validation_sample_manifest.jsonl").open("w", encoding="utf-8") as f:
    for i, r in enumerate(picked_all, 1):
        f.write(json.dumps({
            "article_id": r["article_id"], "anon_id": f"v03val_{i:03d}",
            "journal_code": r["journal_code"], "year": r["year"], "title": r["title"],
            "seed": SEED, "sort_key": "article_id", "word_count_v1": r["word_count_v1"],
            "sentence_count": r["sentence_count"], "sentences": r["sentences"],
            "excluded_pools": "dev_set_manifest + pilot_sample_manifest (run_20260908_a)",
        }, ensure_ascii=False) + "\n")
print(json.dumps(report, indent=2))
print(f"validation sample: {len(picked_all)}（排除 dev {len(dev_ids)} + pilot {len(pilot_ids)}）")
