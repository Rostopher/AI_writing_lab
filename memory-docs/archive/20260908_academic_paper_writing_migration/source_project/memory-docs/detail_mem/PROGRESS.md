---
layer: detail
update_mode: patch
role: "模块 / 功能级实现清单 —— 各模块做到什么程度（清单，非流水账）"
read_when: "要看模块完成度、做多模块工作、查某模块是否实现时"
not_for: "高层状态（-> STATUS），决策来由（-> DECISIONS），带日期的变更流水（-> archive/）"
---

# Progress — 模块级实现清单

> 这是**清单**，不是**流水账**。
>
> - 高层状态（最近做了什么）→ `STATUS.md`
> - 带日期的变更流水 → 沉淀进 `archive/` 或 `HISTORY.md`
> - 本文件只回答：**每个模块 / 功能现在实现到什么程度**
> - 模块级当前状态、卡点和下一步只在这里详细维护；`STATUS.md` 只保留项目级影响和链接

## 主线

- 主路径：参考研究 -> taxonomy / rubric pilot -> reliability 验证 -> benchmark / 应用。
- 主入口：`README.md`、`ideas/project_charter.md`。
- 当前权威状态：研究设计与第一轮参考仓库审计；尚无生产实现或实验结果。

## 已实现

### 项目 scaffold 与边界

- 入口：`README.md`、`AGENTS.md`。
- 产物：八个核心目录、项目级 memory-docs、忽略规则。
- 备注：已建立，后续结构变化按 research scaffold 维护。

### 参考仓库研究

- 入口：`modules/repository_studies/README.md`。
- 产物：两个固定快照及三份 pipeline / 对比笔记。
- 备注：已完成第一轮静态审计；未验证这些方法对论文文本任务的实证效果。

### 写作分析框架

- 入口：`notes/concepts/paper_writing_analysis_framework.md`。
- 产物：paper、section、paragraph、sentence、lexico-grammar 五层候选框架。
- 备注：这是待文献与标注实验验证的候选 taxonomy，不是已确认标准。

## 进行中

### Evaluation 与 rubric pilot

- 当前状态：`ideas/evaluation_design.md` 已定义 validity gate、五类报告维度和候选任务族。
- 卡点：缺少经专家验证的 rubric、许可明确的真实修订对和 inter-rater agreement 数据。
- 下一步：用少量 Introduction 样本编写最小标注协议，加入 fluent overclaim 与意义漂移 hard negatives，先测人—人一致性。

## 未开始 / 缺口

- 论文写作与 rhetorical move 文献工作区及证据综述。
- 授权数据、修订对、标注 schema 和版本化数据集。
- 自动 evaluator、分组报告和可靠性诊断实现。
- Benchmark 发布协议与可审计 AI writing assistant。
- 项目 manuscript、方法论文和附录。

## 相关文档

- 高层状态：`memory-docs/STATUS.md`
- 决策：`memory-docs/detail_mem/DECISIONS.md`
- 代码导航：`memory-docs/detail_mem/MAP.md`
