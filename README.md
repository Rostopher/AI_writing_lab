# AI Writing Lab

研究「AI 如何理解和完成写作任务」的研究与工具项目：把期刊语料、写作案例与
写作方法研究转化为文献认识、研究定位与写作支持。当前首个推进方向是**学术研究与写作**。

## 使用写作 Skills

**[经济学英文摘要写作 · econ-abstract-writing](skills/econ-abstract-writing/README.md)**：
在研究结果、完整故事和 Introduction 已经形成之后，回答一个核心问题、一个关键方法和三个主要发现，
再按 WHFFF 起草、检查或修改英文摘要。支持从研究材料起草、从全文提炼、检查已有摘要。
安装方式、使用示例和研究依据见链接中的说明。

[English guide: Economics Abstract Writing](skills/econ-abstract-writing/README.en.md).

## 项目定位

AI 辅助写作不只是「生成文本」，核心问题是：怎样让 AI 理解写作目的、受众、材料与
作者声音，并完成**规划 → 起草 → 修改 → 审核**的完整过程。本仓库研究这一问题，分三个层次：

| 层次 | 核心问题 | 状态 |
|---|---|---|
| 通用写作方法与流程 | 规划、起草、修改、审核机制中哪些跨场景成立 | 规划中，从实际任务中逐步提取 |
| 学术研究与写作 | 文献调研、问题定位、贡献与论证如何组织成论文 | **当前主线** |
| 商业写作 | 面向读者、决策、行动目标的表达机制 | 有具体任务后再建立 |

## 目录职责

| 路径 | 用途 |
|---|---|
| `memory-docs/` | 项目记忆层：总体方向、模块关系、稳定决策（Agent 入口） |
| `notes/` | 研究笔记：跨场景写作研究、文献阅读、方法拆解、参考工具分析 |
| `ideas/` | 未定型想法与研究设计孵化：claim、证据需求、最小验证、失败条件 |
| `papers/` | 论文工作区：PDF、元数据、全文文本（由 paper-workspace 物化，生成物勿手改） |
| `repos/` | 外部参考仓库（只读，除非明确要求修改） |
| `data/` | 数据层：原始 / 中间 / 处理结果 / 数据字典 |
| `modules/` | 可执行研究工程模块（见下），逐步形成的通用写作流程也在其下 |
| `skills/` | 可分享的 Agent skills 源码、使用说明与随包参考材料 |
| `manuscripts/` | 正式写作区：本项目自身产出的论文、报告、章节草稿 |

## 模块规划

| 模块 | 职责 | 状态 |
|---|---|---|
| `modules/writing_pipeline/` | 逐步形成的通用写作流程（规划—起草—修改—审核） | 预留，从实际复用中提取，暂不预建 |
| `modules/academic_research/` | 文献调研、问题定位、期刊案例分析 | **首个推进方向** |
| `modules/academic_writing/` | 论文规划、起草、修订与审核的学术侧实现 | 待 academic_research 启动后跟进 |
| `modules/evaluation/` | 评价实现，保留领域专属标准 | 预留 |
| `modules/business_writing/` | 商业写作方向 | 有具体任务后再建立 |

## 姊妹仓库

- `playwright_crawler`：期刊数据采集与维护（本仓库消费其数据，不重复采集）。
- 期刊数据经 `paper-workspace` 物化为本仓库 `papers/` 下的可检索全文工作区。

## 当前可接续的材料

2026-09-08，原 `playwright_crawler/research/projects/academic_paper_writing/` 的研究材料
迁入本仓库。此后已完成 4250 篇摘要的结构标注与描述分析，并整理出首版摘要写作 skill；
写作效果评价和论文工作区接入仍待推进。

- [摘要结构全量报告](notes/data/abstract_structure_full_report_v03.md)：语料、分析方法、结构分布与局限。
- [写作分层分析框架](notes/concepts/paper_writing_analysis_framework.md)：整篇论证到词句表达。
- [研究问题](ideas/project_charter.md)与[评价设计 proposal](ideas/evaluation_design.md)：事实保持、论证质量与评审一致性。
- [六仓 writing skills 调研](ideas/writing_skills_survey.md)与[参考仓库入口](repos/README.md)：静态研究，不代表实测效果排名。
- [迁移档案](memory-docs/archive/20260908_academic_paper_writing_migration/manifest.md)：源文件映射、完整性证据和旧项目历史。

## 设计原则

- **先允许差异，后提取共性**：学术写作与商业写作先各有实现，只有当同一逻辑
  （如受众分析、结构规划）在两个方向都被需要时，才上移为通用 `writing_pipeline`。
- **观察 ≠ 因果**：从已发表论文中观察到的写作特征只能用于提出/检验写作假设，
  不能据此断定某种写法就是期刊青睐它的原因。
- 文档语言：中文（含代码注释与 commit message）；内存记忆遵循 `memory-docs/` 协议。
