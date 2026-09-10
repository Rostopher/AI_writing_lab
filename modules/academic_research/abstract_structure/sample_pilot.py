# pilot 抽样：每刊 20 篇，seed 20260908，合格框架（included & available）内随机抽取，
# 与开发集去重；另每刊随机 5 篇（共 25）预留给（agent）审核子集。
# 保存抽样前排序键与入选清单（设计 §3）。
import json
import random
from pathlib import Path

RUN = Path(__file__).resolve().parents[3] / "data/processed/abstract_structure/run_20260908_a"
SEED = 20260908
PER_JOURNAL = 20
REVIEW_PER_JOURNAL = 5

corpus = [json.loads(l) for l in (RUN / "corpus_manifest.jsonl").open(encoding="utf-8")]
dev_ids = {json.loads(l)["article_id"] for l in (RUN / "dev_set_manifest.jsonl").open(encoding="utf-8")}

eligible = [r for r in corpus
            if r["included"] and r["availability"] == "available" and r["article_id"] not in dev_ids]

pilot, review = [], []
report = {}
for j in ["AER", "ECMA", "JPE", "QJE", "REStud"]:
    pool = sorted((r for r in eligible if r["journal_code"] == j),
                  key=lambda r: r["article_id"])  # 抽样前排序键
    rng = random.Random(f"{SEED}:{j}")
    picked = rng.sample(pool, PER_JOURNAL)
    pilot.extend(picked)
    # 审核子集必须来自 pilot 内部（设计 §9C：审核的是 pilot 文章的模型标注）
    review.extend(random.Random(f"{SEED}:review:{j}").sample(picked, REVIEW_PER_JOURNAL))
    years = sorted({r["year"] for r in picked})
    report[j] = {"pool": len(pool), "picked": len(picked), "year_range": [years[0], years[-1]]}

with (RUN / "pilot_sample_manifest.jsonl").open("w", encoding="utf-8") as f:
    for i, r in enumerate(pilot, 1):
        f.write(json.dumps({
            "article_id": r["article_id"], "anon_id": f"pilot_{i:03d}",
            "journal_code": r["journal_code"], "year": r["year"], "title": r["title"],
            "seed": SEED, "sort_key": "article_id", "word_count_v1": r["word_count_v1"],
            "sentence_count": r["sentence_count"], "sentences": r["sentences"],
        }, ensure_ascii=False) + "\n")
with (RUN / "pilot_review_subset.jsonl").open("w", encoding="utf-8") as f:
    for r in review:
        f.write(json.dumps({"article_id": r["article_id"], "journal_code": r["journal_code"],
                            "year": r["year"], "seed": SEED, "sort_key": "article_id",
                            "selection": "random_review_subset"},
                           ensure_ascii=False) + "\n")
print(json.dumps(report, indent=2))
print(f"pilot: {len(pilot)}, review subset: {len(review)}")
