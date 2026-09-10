# Academic Paper Writing

研究高质量学术论文如何形成，并探索如何把论文写作中的整体论证、段落组织、句子级表达和评价机制转化为可复现的知识、实验、benchmark 与 AI 应用。

## 核心问题

1. 一篇论文如何建立问题、研究缺口、贡献、文献定位和完整叙事，而不是只把句子润色得更流畅？
2. Introduction、Data、Methods、Results、Discussion 等 section 中，每个段落和句子承担什么 rhetorical function？
3. 用词、句式、语法、术语一致性、hedging/boosting 和论证强弱如何与证据边界对齐？
4. 如何评价一个修改是真正改善了论文，而不是只提高表面流畅度或引入意义漂移、过度宣称和虚构证据？
5. 哪些规则可以自动执行，哪些只能建议，哪些必须保留给作者或专家判断？

## 研究层级

| 层级 | 研究对象 | 典型问题 |
|---|---|---|
| Paper | 问题、gap、贡献、文献对比、整体 narrative | 论文为何值得读，贡献是否被证据支持 |
| Section/paragraph | rhetorical move、信息顺序、段落衔接 | 每段是否完成明确功能，论证是否逐步推进 |
| Sentence | claim、evidence、qualification、transition | 句子在做什么，强度是否合适 |
| Lexico-grammar | 用词、句式、语法、术语、时态 | 是否准确、清晰、一致且符合领域语体 |
| Evaluation | validity、quality、preference、utility | 如何形成可靠 rubric、gold data 和一致性测量 |

## 工作流

```text
参考仓库与写作研究
  -> pipeline 拆解与共性提取
  -> 写作层级 / rhetorical move / failure taxonomy
  -> 人工标注与修订对数据
  -> 分维度 evaluation 与专家一致性实验
  -> benchmark / AI writing assistant / 方法论文
```

## 当前参考仓库

| 仓库 | 当前用途 | 边界 |
|---|---|---|
| `repos/revise-paper/` | 学习完整 LaTeX 项目审查、判断权限分层和 source/PDF 双 authority | 有详细检查协议，但没有实证 benchmark 或评价可靠性实现 |
| `repos/NaturePanelForge/` | 学习执行/审核 agent loop、阶段产物、可恢复 pipeline 和多维 benchmark | 领域是科学图表复现，不能直接作为文本写作指标 |

两个仓库均为只读参考。前者为 CC BY-NC-SA 4.0，后者为 MIT；复用内容时必须遵守各自许可。

## 当前阶段

项目刚完成 scaffold 和第一轮参考仓库审计。写作 taxonomy、benchmark schema 和 evaluation protocol 均为 proposal，尚无已验证模型、数据集或结果。

## 目录

| 目录 | 职责 |
|---|---|
| `memory-docs/` | 项目级状态、导航、约定和稳定决策 |
| `notes/` | 写作概念、参考仓库 pipeline、文献和实验理解 |
| `ideas/` | 项目 charter、evaluation proposal、benchmark 假设 |
| `papers/` | 论文、修订版本、OCR/metadata 等文献工作区 |
| `repos/` | 外部参考仓库，默认只读且不纳入主仓库 |
| `data/` | 经授权的写作样本、修订对、标注、rubric 与派生数据 |
| `modules/` | 后续可执行的仓库审计、标注、evaluation 和实验模块 |
| `manuscripts/` | 本项目形成的论文、报告与附录 |
