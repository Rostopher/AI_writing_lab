---
layer: framework
update_mode: append
role: "项目是怎么走到今天的 —— 时间线叙事，把决策 / 转折 / 重构串成有因果的故事"
read_when: "想知道'我们为什么是现在这个样子'、复盘演变、新人 / 新 Agent 建立历史认知时"
not_for: "单条决策的来由（-> DECISIONS），当前状态（-> STATUS），日期型流水账（-> archive/）"
---

# Project History

> 这是项目的**叙事线**，不是流水账，也不是决策档案。
> `detail_mem/DECISIONS.md` 是查找表（每条独立、记取舍）；本文件把决策串成
> 有因果的故事。

---

## 2026-09 — 项目成立与形态决策

在讨论学术写作、商业写作与写作工具项目如何组织时，曾考虑按方向拆成多个平级仓库
（`academic_paper_writing` / `business_writing` / `writing_pipeline`）。随后意识到三者
层次不同：学术与商业是**应用方向**，写作 pipeline 是**可能被两者共用的实现**；过早
各自开发会造成两套起草/修订/审核机制，过早抽公共 pipeline 则会把未验证的相似性写死。

最终确定：总项目 `AI_writing_lab`，一个仓库，多方向共存，**先允许差异、从实际复用中
提取通用逻辑**；拆仓库只发生在明确触发条件出现时（DEC-001）。学术方向内区分
**研究内容定位**（academic_research）与**论文表达组织认识**（academic_writing）两类产出
（DEC-003）。

同期完成仓库初始化：research scaffold 目录、vibe-memory-system 的 memory-docs 模板、
AGENTS.md 与 README 体系。期刊数据继续由姊妹仓库 `playwright_crawler` 维护。

- 相关决策：DEC-001、DEC-002、DEC-003
- 相关文档：`memory-docs/OVERVIEW.md`、`memory-docs/STATUS.md`

## 2026-09-08 — 接续原学术论文写作项目

核查姊妹仓库时发现，`research/projects/academic_paper_writing/` 已在 2026-09-01
形成分层写作框架、参考仓库研究和评价 proposal。新仓库初始化时的“尚无笔记”只描述
本地目录，并不代表此前没有相关研究。用户随后授权派子智能体将该项目内容移动过来。

研究笔记与方案进入 notes/ideas，六个参考快照进入 repos；原项目说明与记忆原文
归档，源路径保留迁移入口。原项目的 Introduction rubric pilot 仍为待执行方案，
本次工作没有产生实验结果或重新确认研究优先级。学术研究主线与通用模块预留边界保持生效。

来源、文件映射与完整性证据见[迁移档案](archive/20260908_academic_paper_writing_migration/manifest.md)。
