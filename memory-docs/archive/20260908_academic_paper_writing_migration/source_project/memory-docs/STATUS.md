---
layer: framework
update_mode: rewrite
role: "现在在做什么 —— 当前焦点 + 最近 3-5 条里程碑（快照，非流水账）"
read_when: "进入项目、规划工作、问当前状态时"
not_for: "模块级细节（-> PROGRESS），历史演变（-> HISTORY），决策来由（-> DECISIONS）"
line_budget: 160
stale_after_days: 14
---

# Project Status

> 更新时间：2026-09-01

## Current Focus

- 项目处于研究设计阶段：先验证写作 taxonomy 与评价 rubric，再考虑自动 evaluator 或应用实现。
- 当前主线是设计最小 rubric pilot，并确定可公开或明确授权的 Introduction 修订样本。
- taxonomy、benchmark schema 与评价协议仍是 proposal，模块级边界见 `detail_mem/PROGRESS.md`。

## Done（最近 3-5 条）

- [x] 建立标准研究项目 scaffold（2026-09-01）——八个核心目录和项目级 memory-docs 已就位。
- [x] 完成两个参考仓库的第一轮审计（2026-09-01）——固定快照、许可、pipeline 与评价边界均已记录。
- [x] 写出首版分层分析框架和 evaluation proposal（2026-09-01）——明确 validity gate、hard negatives 和多维报告原则。

## In Progress

- Rubric pilot 与最小标注协议尚待设计和执行，当前没有实验结果 → 细节见 `detail_mem/PROGRESS.md`。
- 六个参考仓库的 writing skills 已完成逐 skill 调研，综述表与 skill 评价维度草案（proposal）见 `ideas/writing_skills_survey.md`。

## Backlog

- P0：定义最小标注单位、维度、validity failure 和评审流程，并做专家一致性 pilot。
- P1：建立论文写作与 rhetorical move 文献工作区，获取许可明确的真实修订对。
- P2：在 rubric 可复现后实现 evaluator、benchmark schema 和可审计 AI assistant 原型。

## 当前必须遵守的约束（快照）

- 自动修改不得制造或改变事实、数字、引用、结果、贡献和作者意图。
- validity failure 不能被流畅度或 aggregate score 抵消；生成和审核必须保留独立证据。
- 外部参考仓库默认只读，复用时遵守固定快照对应的许可。

## 相关文档

- 模块实现清单：`memory-docs/detail_mem/PROGRESS.md`
- 项目演变：`memory-docs/HISTORY.md`
- 决策：`memory-docs/detail_mem/DECISIONS.md`
- 约定：`memory-docs/CONVENTIONS.md`
