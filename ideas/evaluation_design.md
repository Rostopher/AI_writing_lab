# Evaluation Design — Proposal

## 核心判断

论文写作质量不能可靠地压成一个总分。Evaluation 应先做 validity gate，再按层级和维度报告，最后才允许给出辅助 aggregate。

## Evaluation Unit

候选基本单位不是孤立句子，而是：

```text
task context
  + section / paragraph / neighboring sentences
  + original text
  + candidate revision
  + intended rhetorical move
  + facts/citations/numbers that must be preserved
  + optional human-accepted revision
```

同一个候选可以在句子级变好，却在段落级破坏逻辑，因此必须保留多层上下文。

## Validity Gate

以下任一失败时，候选不能因流畅而获得高质量评价：

- 编造或改变事实、数字、结果、引用、贡献或作者意图；
- claim strength 超出 evidence；
- 删除必要限定、边界或不确定性；
- 改变术语含义、因果方向、比较对象或时间范围；
- 引入语法错误、歧义或无法解析的引用/LaTeX。

## 分层维度

| 优先级 | 维度 | 示例 |
|---|---|---|
| P0 | validity / preservation | 事实保持、引用保持、claim-evidence 对齐、无虚构 |
| P1 | local writing quality | 准确、清晰、简洁、语法、术语、句式、强度校准 |
| P2 | discourse quality | rhetorical move、段落功能、section coherence、文献定位、贡献叙事 |
| P3 | human utility | 专家偏好、作者接受率、修改时间、后续返工、解释是否有用 |
| R | reliability | 人—人、人—judge、judge—judge 一致性和置信区间 |

## Task Families

1. Diagnosis：定位问题并分类，不直接改写。
2. Minimal Revision：在 preservation constraints 下做最小修改。
3. Pairwise Ranking：比较两个候选，必须给维度化理由。
4. Rhetorical Move Classification：识别句子/段落在当前 section 中的功能。
5. Claim Strength Calibration：判断 hedging/boosting 是否与证据相称。
6. Reverse Outline：从段落首句与功能恢复 section 的论证链。
7. Literature Positioning：比较当前 claim 与既有文献，识别真实 gap 与过度 novelty。

## Gold 与 Hard Negatives

- Gold 不应只有单一 reference sentence；同一意图可能有多种合格表达。
- 优先记录作者接受的修订、专家可接受集合和禁止改变项。
- Hard negatives 应包括：更流畅但过度宣称、同义改写但意义漂移、语法正确但段落功能错误、引用存在但并不支持 claim。

## Judge Design

- 确定性检查负责数字、引用键、术语、LaTeX 和显式 constraint。
- LLM/VLM judge 只负责需要语义判断的维度，并输出证据位置和不确定性。
- 专家 pairwise 判断用于校准高层论证和领域内容。
- 必须测 inter-rater agreement，并按 section、领域、任务难度和错误类型分组报告。

## 不采用的捷径

- 不把 grammar checker 分数当整体写作质量。
- 不把与单一 reference 的 BLEU/embedding similarity 当主要指标。
- 不让同一个 agent 既生成又无独立证据地宣布自己通过。
- 不因一个 weighted score 上升而隐藏 validity failure 或分组退化。

## 下一步

先写 rubric pilot 和最小标注协议，验证人类评审是否一致；只有 rubric 可复现后，才实现自动 evaluator 或正式 benchmark schema。
