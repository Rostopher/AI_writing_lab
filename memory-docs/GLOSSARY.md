---
layer: framework
update_mode: patch
role: "项目术语 —— 当我说 X，我指的是什么（定义，不讲位置）"
read_when: "遇到不熟悉的术语、问命名 / 数据字段含义时"
not_for: "代码位置（-> MAP），硬规则（-> CONVENTIONS）"
---

# Glossary — AI Writing Lab

## 项目术语

### 写作流水线（writing pipeline）

- 定义：规划 → 起草 → 修改 → 审核的通用写作过程骨架。本项目中为**预留模块**
  （`modules/writing_pipeline/`），不提前实现，从跨方向真实复用中逐步形成。
- 为什么重要：学术写作与商业写作共享骨架，但判断规则不同；先分别实现再提取共性。
- 易混淆点：它不是"先设计好的管线"，而是"复用出现的产物"。

### 学术方向（academic）

- 定义：包含两类产出——研究内容定位（已有研究解释了什么/争议/证据缺口/贡献位置，
  `modules/academic_research/`）与论文表达组织认识（背景→问题→论证→替代解释→证据，
  `modules/academic_writing/`）。
- 为什么重要：两类产出性质不同，前者影响"研究什么"，后者影响"怎么讲清楚"。
- 易混淆点：不叫 `academic_paper_writing`——范围是研究+写作，不只是写论文。

### 商业方向（business）

- 定义：面向具体读者、决策与行动目标的表达机制（决策建议、执行条件、行动指引）。
- 为什么重要：与学术方向共享写作骨架但拥有自己的判断规则。
- 易混淆点：`modules/business_writing/` **尚未建立**，有具体任务后再创建。

### 观察 vs 证据（observation vs evidence）

- 定义：从已发表论文中观察到的写作特征（反复出现的组织方式）= 观察；
  已验证有效的写作建议 = 证据。两者分开记录。
- 为什么重要：观察只能提出/检验假设，不能确认"某种写法就是期刊青睐它的原因"。
- 易混淆点：研究问题、设计、证据质量与表达方式交织——相关性不等于因果。

### 摆脱 AI 味

- 定义：需要拆成可观察问题的评价目标：套话、空泛判断、重复总结、机械段落结构、
  不必要修饰、缺少具体信息、作者声音不一致。
- 为什么重要：只有可观察才能比较修改前后是否更好，并判断跨场景 vs 文体偏好。
- 易混淆点：不是单一风格偏好，而是一组可独立评估的缺陷。

### 期刊案例分析（journal case analysis）

- 定义：对期刊语料的结构化分析：论文如何建立背景、提出问题、推进论证、回应
  替代解释、安排证据与限定。
- 为什么重要：是学术方向把语料转化为"表达组织认识"的主要方法。

### WHFFF

- 定义：经济学英文摘要的句序骨架 What → How → Findings → Findings → Findings
  （研究内容 → 方法 → 三个主要发现），`econ-abstract-writing` skill 的起草框架。
- 为什么重要：来自 4250 篇 Top5 摘要结构标注的观察共识（摘要 4–6 句、findings 为主场）。
- 易混淆点：是观察到的主流组织方式（DEC-004：观察 ≠ 因果），不是验证过的录用条件；
  也不适用于中文期刊与毕业论文。

## 迁入学术写作研究术语

- **Rhetorical move**：句子、段落或章节在论证中承担的功能，如背景、缺口、主张、证据或限定。
- **Claim strength**：文本对确定性、因果性、普遍性和新颖性的承诺强度，应与证据相称。
- **Validity gate**：先检查事实、数字、引用、证据边界和作者意图保持；失败不能由流畅度抵消。
- **Hard negative**：表面流畅但过度宣称、意义漂移或论证功能错误的候选，用于检验评价能否识别这些缺陷。
- **Reliability**：不同评审者、人类与自动 judge 或多次 judge 运行之间的一致性及其不确定性。

## 变量 / 字段

（暂无结构化数据字段；数据接入后按需补充，例如：期刊 slug、DOI、article_uid、
issue 年份等来自 playwright_crawler 的字段约定。）

## 命名 / 展示

### 目录名

- 内部名：`AI_writing_lab` / `academic_research` / `academic_writing` / `writing_pipeline` /
  `business_writing` / `evaluation` / `manuscripts` / `papers` / `playwright_crawler`
- 展示名：中文对话中使用「学术研究与写作」「写作流水线」等
- 备注：模块目录用英文 snake_case；文档正文中文

## 相关文档

- 代码位置：`memory-docs/detail_mem/MAP.md`
- 约定：`memory-docs/CONVENTIONS.md`
