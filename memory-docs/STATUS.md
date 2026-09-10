---
layer: framework
update_mode: rewrite
role: "现在在做什么 —— 当前焦点 + 最近 3-5 条里程碑（快照，非流水账）"
read_when: "进入项目、规划工作、问当前状态时"
not_for: "模块级细节（-> PROGRESS），历史演变（-> HISTORY），决策来由（-> DECISIONS）"
line_budget: 160
stale_after_days: 14
---

# Status — AI Writing Lab

> 更新时间：2026-09-10

## Current Focus

- 学术研究与写作为当前主线；首个实现 `modules/academic_research/abstract_structure/`
  已完成摘要结构研究两轮付费运行（pilot + 全量描述），产出两份报告。
- 仓库已建立 Git 版本化并推送 GitHub public（`Rostopher/AI_writing_lab`）。
- 摘要结构研究第二阶段（规则审查 §7/H5、15 篇不一致案例复核、是否跑全量 pro）
  尚未启动；写作检查项落地前需先定目标期刊口径。

## Done（最近 3-5 条）

- [x] Git 首次提交并推送 GitHub public（2026-09-10）— 6 个语义化 commit；私有路径改环境变量配置；含摘要全文产物留本地（DEC-007）
- [x] 摘要结构全量描述 `run_20260909_v03_full`（2026-09-09）— 4250 篇 flash 标注零失败（¥96）；句数分布与位置×功能分析同日补入[全量报告](../notes/data/abstract_structure_full_report_v03.md)
- [x] 摘要结构 pilot `run_20260908_a`（2026-09-08）— 100 篇双模型零失败（约 ¥7）；句数公式证伪；见[pilot 报告](../notes/data/abstract_structure_pilot_report.md)
- [x] 接续旧学术写作研究（2026-09-08）— 材料进入 notes/ideas/repos；见[迁移档案](archive/20260908_academic_paper_writing_migration/manifest.md)
- [x] 确定总项目形态与仓库初始化（2026-09-07）— 单仓库多方向（DEC-001）、research scaffold、memory-docs

## In Progress

- 摘要结构研究：描述阶段完成，可靠性补强与规则审查待启动（见 Backlog 前三条，
  执行顺序未确认）。
- 学术写作评价设计：`ideas/evaluation_design.md` 仍为 proposal；Introduction rubric
  pilot 是未启动的候选方案。

## Backlog

- 15 篇同文标签不一致案例人工复核（全量可靠性证据）。
- 规则审查小样本（设计 §7/H5，套话/术语/识别策略，约 ¥6 量级）。
- 全量 pro（约 ¥150–200）：仅在需要全量尺度双模型证据时运行。
- 把「Why 仅 25%」「理论论文常省 how」「位置×功能倾向」做成写作检查项前，
  先决定目标期刊口径（按本刊风格对齐，不套全刊平均）。
- 评估 `papers/` 物化与数据工作区（依赖 playwright_crawler 数据）。

## 当前必须遵守的约束（快照）

> 这里只放"当前有效、影响决策"的少数硬约束。完整规则在 `CONVENTIONS.md`。

- 单仓库策略生效中；拆仓仅在触发条件满足时（DEC-001）
- 写作特征观察 ≠ 期刊青睐原因（DEC-004）；评价先拆可观察维度（CONVENTIONS）
- 学术修改先检查事实、引用、证据强度与作者意图保持；历史 rubric、阈值和 taxonomy 仍待验证
- writing_pipeline / evaluation 为预留模块，不提前实现（DEC-001）
- public 仓库数据边界：LLM 调用缓存与含摘要全文产物不入库，只入派生层；
  凭据与私有路径走环境变量（DEC-007）

## 相关文档

- 模块实现清单：`memory-docs/detail_mem/PROGRESS.md`
- 项目演变：`memory-docs/HISTORY.md`
- 决策：`memory-docs/detail_mem/DECISIONS.md`
- 约定：`memory-docs/CONVENTIONS.md`
