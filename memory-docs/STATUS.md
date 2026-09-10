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

> 更新时间：2026-09-08

## Current Focus

- 学术研究与写作为当前主线；已接续姊妹仓库 `academic_paper_writing` 的研究设计、
  分层写作框架、参考工具调研与六个固定参考仓库。
- 当前有研究笔记和 proposal，**尚无业务实现、标注实验结果或论文工作区接入**。
- 下一步仍需选定首个实际研究任务。已有 Introduction rubric pilot 是可接续的方案，
  本次迁移不表示已经选定样本、启动实验或验证了评分规则。

## Done（最近 3-5 条）

- [x] 接续旧学术写作研究（2026-09-08）— 材料进入 notes/ideas/repos；原项目说明与记忆保留在[迁移档案](archive/20260908_academic_paper_writing_migration/manifest.md)，源位置保留重定向。
- [x] 确定总项目形态：单仓库多方向，`AI_writing_lab`（2026-09-07）— 学术/商业/通用写作能力共用一仓，明确拆仓触发条件
- [x] 仓库初始化（2026-09-07）— 建立 research scaffold 目录、`memory-docs/`（vibe-memory-system 模板）、`AGENTS.md`、README 体系
- [x] 定义模块规划（2026-09-07）— academic_research（主线）、academic_writing、writing_pipeline/evaluation（预留）、business_writing（待任务）

## In Progress

- 写作分析与评价处于研究设计阶段：已有五层候选框架、validity-first 评价 proposal 和 skills 调研；尚未执行 rubric pilot。

## Backlog

- 选定期刊或研究问题，开始文献调研与期刊案例分析（`notes/paper-reading/`）。
- 接续候选方案：明确 Introduction 的标注单位、事实保持项与评审流程，获取适用样本，检验评审一致性（`ideas/evaluation_design.md`）。
- 核验、提炼参考 skills 中可迁移的检查项；现有静态调研排序不代表实测效果。
- 评估 `papers/` 物化与数据工作区（依赖 playwright_crawler 数据）。以上任务的执行顺序尚未确认。

## 当前必须遵守的约束（快照）

> 这里只放"当前有效、影响决策"的少数硬约束。完整规则在 `CONVENTIONS.md`。

- 单仓库策略生效中；拆仓仅在触发条件满足时（DEC-001）
- 写作特征观察 ≠ 期刊青睐原因（DEC-004）；评价先拆可观察维度（CONVENTIONS）
- 学术修改先检查事实、引用、证据强度与作者意图保持；历史 rubric、阈值和 taxonomy 仍待验证。
- writing_pipeline / evaluation 为预留模块，不提前实现（DEC-001）

## 相关文档

- 模块实现清单：`memory-docs/detail_mem/PROGRESS.md`
- 项目演变：`memory-docs/HISTORY.md`
- 决策：`memory-docs/detail_mem/DECISIONS.md`
- 约定：`memory-docs/CONVENTIONS.md`
