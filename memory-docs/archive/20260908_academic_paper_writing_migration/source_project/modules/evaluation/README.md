# Evaluation

未来用于实现论文写作 benchmark 的数据校验、validity gate、多维 rubric、pairwise/expert evaluation、judge agreement 和分组报告。

当前只有 proposal：`../../ideas/evaluation_design.md`。在人工 rubric pilot 证明可复现前，不实现单一 leaderboard score，也不把 LLM 自评分当 gold。

预期产物沿本模块保存：

```text
outputs/<run_id>/samples/<sample_id>/result.json
outputs/<run_id>/summary.json
outputs/<run_id>/summary.csv
outputs/<run_id>/agreement.json
logs/
```
