# Reference Repository Comparison

## 对比矩阵

| 维度 | revise-paper | NaturePanelForge | 本项目应吸收 |
|---|---|---|---|
| 任务对象 | 完整 LaTeX 论文 | 科学图表到代码 | 完整论文与局部写作单位并存 |
| Authority | source 可编辑，PDF 视觉权威 | target、code、render、review artifacts | 原文/证据/作者意图与候选修订分层 |
| 流程 | 全项目审查清单 | 多阶段可恢复 pipeline | 分层诊断 -> 修改 -> 独立审核 -> 结果落盘 |
| 判断权限 | automatic / suggested / comment | generator / reviewer / auditor | 权限由风险与证据决定 |
| Output contract | 修改后项目 + 定位报告 | 每样本代码、渲染、review、result JSON | 原文、候选、约束、finding、rubric、judge evidence |
| Evaluation | 没有实证 evaluator | P0/P1/P2、多维、gate、breakdown | validity gate + 多维质量 + 人类效用 + reliability |
| 防作弊/失真 | 禁止虚构 claim/citation/result | 禁直接加载目标图和 raster tracing | 禁意义漂移、过度宣称、引用装饰和 style-only shortcut |
| 当前局限 | 规则细但未操作化可靠性 | 多数高层指标仍是 proxy，领域是图表 | 必须做真实修订数据与专家一致性实验 |

## 提取出的共性

1. 先定义任务 authority，再允许自动修改。
2. 高质量流程依赖完整上下文，不应只输入孤立句子。
3. 生成和审核应角色分离，并留下可追溯 artifact。
4. validity 是 gate，不是可以被其他维度平均掉的一项普通分数。
5. 输出 schema 和分组维度应先固定，judge 可以逐步替换。
6. 评价应服务错误诊断，而不只是排行榜。

## 尚缺的关键证据

- 什么样的写作 taxonomy 能跨领域复用。
- 专家对 claim strength、gap 和 contribution 的一致性上限。
- 作者接受修改是否能作为 gold，以及接受行为受时间和权威关系影响多大。
- 自动 judge 是否偏好更长、更自信或更模板化的表达。
- 句子级改善如何传导到段落、section 和整篇论文质量。
