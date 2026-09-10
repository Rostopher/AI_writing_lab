# NaturePanelForge Pipeline

## What It Is

NaturePanelForge 是科学论文图表到可执行绘图代码的数据与 benchmark pipeline，不是文本写作工具。它的价值在于展示如何把高判断任务拆成可恢复阶段、固定 artifact contract、独立 review loop 和分维度 evaluation。

## Main Pipeline

```text
开放获取论文/完整 figure
  -> full figure manifest
  -> Codex panel split + independent review
  -> Qwen panel scoring
  -> Codex code reproduction + render + review
  -> final refine + audit
  -> clean benchmark manifest
  -> model generation -> sandbox execution -> metrics -> summaries/breakdowns
```

每个阶段读取窄输入并写新目录，失败后可从落盘 artifact 恢复。生成者负责执行，review/audit agent 负责检查，失败触发下一轮代码修改与重新渲染。

## Canonical Artifacts

- Target：`target.png`/`target.pdf` 和 metadata。
- Candidate：`candidate.py`、rendered PNG/PDF。
- Evidence：prompt、raw model output、execution status、review notes、result JSON。
- Aggregate：summary CSV/JSON 与按 complexity/domain/subtype 的 breakdown。

## Evaluation Design

- Execution 是 gate：代码不执行时视觉内容分数归零。
- P0 是主要 leaderboard 维度，P1 用于诊断与分组，P2 是辅助 proxy。
- 协议明确要求维度分别报告，weighted score 只能作为次要摘要。
- invalidity 单独检查直接依赖目标图、pixel painting 或 raster tracing，防止模型绕过任务。
- 必须按复杂度、领域和图表 subtype 分组。

## Important Limitation

当前代码中的大量高层指标并不是已验证的人类/VLM rubric，而是图像、代码 API 和 metadata 的 deterministic proxy。`caption_consistency`、`judge_agreement` 等字段仍是 pending/not configured。这个诚实的 schema 设计值得学习，但不能把字段存在误认为指标已经有效。

## How To Migrate

- 写作任务也应建立 input/candidate/evidence/result 的固定 bundle。
- 生成与审核分离，失败必须留下可审计原因并可恢复。
- validity failure 单列，不被流畅度或整体分数抵消。
- 按 section、领域、任务类型、修改风险和语言背景做 breakdown。
- 先固定输出 schema，再逐步用人类实验替换 proxy judge。

## Evidence

- `repos/NaturePanelForge/docs/architecture.md`
- `repos/NaturePanelForge/SciFigure2Code/benchmark_ready/benchmark_protocol.md`
- `repos/NaturePanelForge/SciFigure2Code/evaluation/metrics.py`
- `repos/NaturePanelForge/SciFigure2Code/evaluation/pipeline.py`
- 快照：`0ca0c91267b9e8260b959bfa4be659030dd9a5b7`
