---
layer: framework
update_mode: rewrite
role: "项目是什么 —— 一页纸的整体认知（做什么、怎么组织、技术栈）"
read_when: "进入项目、问架构 / 范围 / 技术栈时"
not_for: "当前进度（-> STATUS），项目演变（-> HISTORY），术语（-> GLOSSARY），代码位置（-> MAP）"
---

# Overview — AI Writing Lab

## 一句话定位

AI Writing Lab 是「AI 辅助写作」的研究与工具项目：让 AI 理解写作目的、受众、材料和
作者声音，并完成**规划 → 起草 → 修改 → 审核**的完整写作过程；当前通过**学术写作**方向
（期刊语料研究 + 论文写作支持）落地第一版实现。

## 目标

- 建立写作流程的通用认识：规划、起草、修改、审核中哪些机制跨场景成立、哪些是文体偏好
- 学术方向：从期刊数据形成文献认识、研究问题定位与论文写作支持（当前主线）
- 评价体系：把「写得好 / 摆脱 AI 味」拆成可观察、可检验的维度
- 商业写作方向：有具体任务后再建立

## 分层

| 部分 | 核心问题 | 在项目中的位置 |
|---|---|---|
| 通用写作方法与流程 | 怎样让 AI 理解目的、受众、材料、声音，并完成规划/起草/修改/审核 | 跨场景公共能力：`modules/writing_pipeline/`（预留） |
| 学术研究与写作 | 文献调研、问题定位、贡献论证；把研究证据组织成论文 | 当前主线：`modules/academic_research/` + `modules/academic_writing/` |
| 商业写作 | 面向具体读者、决策与行动组织可信表达 | 未建立：`modules/business_writing/` 待任务出现 |

## 核心链路

```text
playwright_crawler（期刊数据采集）
  -> paper-workspace（物化全文工作区到 papers/）
  -> notes/paper-reading（文献理解）
  -> modules/academic_research（问题定位、期刊案例分析）
  -> modules/academic_writing + manuscripts（论文写作）
  -> evaluation（质量评价）
```

## 核心模块

| 模块 | 角色 | 入口 |
|---|---|---|
| `modules/academic_research/` | 文献调研、问题定位、期刊案例分析（研究内容 + 表达组织认识） | 见 `detail_mem/MAP.md` |
| `modules/academic_writing/` | 论文规划、起草、修订与审核 | 同上 |
| `modules/writing_pipeline/` | 通用写作流程（预留，不提前实现） | 同上 |
| `modules/evaluation/` | 评价实现（预留） | 同上 |

## 技术栈

- 运行时 / 语言：Python（预期；尚未引入工程代码）
- 数据来源：期刊数据来自姊妹仓库 `playwright_crawler`
- 论文工作区：`paper-workspace` 物化为 `papers/`
- 记忆系统：`memory-docs/`（vibe-memory-system 三层结构）

## 已有研究材料

2026-09-08 从姊妹仓库 `research/projects/academic_paper_writing/` 迁入写作分层框架、
参考工具分析、六个参考仓库及评价 proposal。现有研究设计可供学术方向接续，
尚无标注实验、已验证评价器或业务实现；定位见 `detail_mem/MAP.md`，
来源与完整性证据见[迁移档案](archive/20260908_academic_paper_writing_migration/manifest.md)。

## 关键立场

- **单仓库多方向**：先允许差异，从实际复用中提取通用逻辑；拆仓库有明确触发条件（见 DECISIONS DEC-001）。
- **观察 ≠ 因果**：已发表论文的写作特征只用于提出/检验假设，不能确认它是期刊青睐的原因。
- 评价必须拆成可观察问题再比较（见 `modules/evaluation/README.md`）。

## 相关文档

- 当前状态：`memory-docs/STATUS.md`
- 项目演变：`memory-docs/HISTORY.md`
- 术语：`memory-docs/GLOSSARY.md`
- 约定：`memory-docs/CONVENTIONS.md`
- 模块状态：`memory-docs/detail_mem/PROGRESS.md`
- 代码导航：`memory-docs/detail_mem/MAP.md`
- 决策：`memory-docs/detail_mem/DECISIONS.md`
