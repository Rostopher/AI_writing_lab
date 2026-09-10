# Prompt 优化评判材料：how[mechanism] 的「释义 vs 机制」边界

> 2026-09-09 后续：用户已确认改按研究功能区分，方法归 How，机制性答案归 Findings；不采纳本文候选的“可分述性”判据。Why 定为可选、启发式 brief implications，涵盖学术与现实应用。见[当前 prompt v0.3](abstract_structure_annotation_prompt.md)与[设计](abstract_structure_study_design.md)。下文保留提出问题时的原始材料；其 v0.2 引文对应[冻结快照](abstract_structure_annotation_prompt_v02.md)，不代表当前定义或已验证真值。

> 用途：请 GPT 6 Astra 评判如何修改 `abstract_structure_annotation_prompt.md`
> 中 mechanism 相关条款。你（GPT）是该 prompt v0.1 的起草者；v0.2 在执行方
> 开发集测试后做了三处无关修订（why 过标、场景设定句、connective_only），
> mechanism 条款保持你的原文未动。以下争议在 100 篇 pilot 后暴露。
>
> 本文档只做评判输入，不代表修改决定。标注口径背景见设计文档
> `abstract_structure_study_design.md`（一句话可有多个功能标签，每个标签须由
> 原文 quote 支撑；how 细分 aspects：data / design / model / mechanism /
> other_method）。

## 1. 争议条款（prompt v0.2 原文，即你的 v0.1 原文）

how 定义节（第 33–41 行）：

```text
how:
  The data, research design, analytical method, model setup, or explanatory mechanism
  used by this paper. The text must provide substantive information about the approach.
  "We study X" alone is not how. Do not infer an identification strategy from a result.
  A named or described economic mechanism may be how even if it appears in a result sentence.
  Scene-setting descriptions of the economic or decision environment (agents, choices,
  timing; e.g., "Consider a policy maker who must ...") are substantive model setup:
  label them how with aspect model. A sentence that only reports a result, without
  naming or describing the approach or a mechanism as content, is not how.
```

多标签规则节（第 61–65 行）：

```text
- Do not force a single dominant function or require all functions to be present.
- A sentence can express a task and a method, or a result and an implication.
  Assign both only if their meanings are explicitly supported.
- A mechanism can be both part of the approach and an established result; support both
  labels with evidence. The presence of the word "model" alone proves neither.
```

aspects 定义（第 78 行）：

```text
  mechanism names or describes an economic force or explanatory process.
```

## 2. 暴露的问题

条款给了「结果句里的机制描述可以是 how」的许可，但没有区分两种结构：

- **释义型**：机制描述是让本句结论成立/可理解的定义性展开（去掉它，结论本身表述不完整）；
- **解释型**：机制内容解释了另一个可以独立陈述的结果（它是结论之外的额外贡献）。

两个被测模型（deepseek-v4-flash / pro）都把释义型也双标了，且行为一致——
说明是 prompt 的引导，不是模型偶发错误。

## 3. 争议案例 A：QJE 2021, "Rational Groupthink"（10.1093/qje/qjaa026）

完整摘要（仅 4 句）：

> **S1** We study how long-lived rational agents learn from repeatedly observing a private signal and each others' actions.
> **S2** With normal signals, a group of any size learns more slowly than just four agents who directly observe each others' private signals in each period.
> **S3** Similar results apply to general signal structures.
> **S4** We identify rational groupthink—in which agents ignore their private signals and choose the same action for long periods of time—as the cause of this failure of information aggregation.

实际标注：

| 句 | flash | pro |
|---|---|---|
| S1 | what + how[model] | what |
| S4 | findings(central) + how[mechanism] | findings(central) + how[mechanism] |

S4 两模型的 how evidence 均落在破折号插入语上：
flash 取 "rational groupthink—in which agents ignore their private signals…"，
pro 取 "agents ignore their private signals and choose the same action for long periods of time"。

**争议焦点**：破折号部分是对术语 "rational groupthink" 的释义——没有它，
"groupthink is the cause" 这个结论本身就不完整。执行方（用户）认为这属于
对 finding 的 illustrate，应整体标 findings 单标；两模型按条款原文双标。

附带的次级分歧：S1 里 flash 把 "learn from repeatedly observing a private
signal and each others' actions" 标为 how[model]（理论论文的问题陈述由模型
设定构成），pro 只标 what。这与 S4 是同一类问题的另一面：问题/结论陈述中
嵌入的设定细节，到什么程度算交付了 how。

## 4. 对照案例 B：QJE 2022, "The Effects of Joining Multinational Supply Chains"（10.1093/qje/qjac006）S6——解释型，双标似合理

上下文：S5 报告了一个现象（供给商在事件年对其他买家的销售大跌），S6：

> **S6** The dynamics of adjustment in sales to others suggests that firms face short-run capacity constraints that relax over time.

- flash：findings 单标（"dynamics…suggests that firms face short-run capacity constraints…"）；
- pro：findings + how[mechanism]（mechanism evidence = "firms face short-run capacity constraints that relax over time"）；
- agent 审核标注：findings + how[mechanism]，与 pro 相同。

这里的 "short-run capacity constraints" 解释了 S5 那个**可以独立陈述**的经验
现象（销售为何先跌后回升），符合「解释型」判据。注意三方在此仍有分歧
（flash 单标），说明即便判据写清，执行一致性问题也不会完全消失。

## 5. 对照案例 C：QJE 2025, "When Did Growth Begin?"（10.1093/qje/qjae046）——更宽的边界地带

> **S2** Real wages over this period were heavily influenced by plague-induced swings in the population.
> **S8** Much of the increase in output growth during the Industrial Revolution is explained by structural change—the falling importance of land in production—rather than faster productivity growth.
> **S9** Stagnant real wages in the eighteenth and early nineteenth centuries—Engels' Pause—is explained by rapid population growth putting downward pressure on real wages.

- S8/S9：两模型均 findings + how[mechanism]。这两个是「X is explained by Y」
  结构——Y（structural change / population pressure）解释的是可独立陈述的
  结果 X，按解释型判据双标合理。但注意它与案例 A 的 S4 在句法上几乎同构
  （都是破折号嵌入机制名/描述），仅凭句法无法区分，判据必须是语义性的。
- S2：两模型都标 how[mechanism]（"plague-induced swings in the population"），
  但这句更像研究背景中的经济力量陈述（估计要控制的 Malthusian 动态），
  既不是本文结果也不是本文方法。aspects 定义 "names or describes an
  economic force" 的字面口径会把它兜进 how[mechanism]——这是否符合你的
  设计意图？

## 6. 影响面（pilot 100 篇实测）

- how 覆盖率 95/100（两模型），其中混入了多少释义型标注说不清；
- flash vs pro：how 的 F1=0.83 是四功能最低（findings 0.97 / what 0.90 /
  why 0.81），pro 对 how 过标 fp=66；
- vs agent 审核（25 篇，非 gold）：how 的 P=0.90/R=0.81（flash）、
  P=0.80/R=0.96（pro）——pro 偏宽、flash 偏窄，分歧中心就在 mechanism 双标；
- 该条款还放大了「how 寄生句」现象，是「How 恰好 1 句」类句数规则在
  实测中失效（2–5/100）的原因之一。

## 7. 执行方目前的倾向判据（供你评判，非结论）

> 机制内容如果能脱离本句结论独立成立（解释了另一个可分述的结果），才
> findings + how[mechanism] 双标；如果只是让本句结论可理解的释义/展开，
> 归 findings 单标。

按此判据：案例 A 的 S4 → findings 单标；案例 B 的 S6 → 双标；
案例 C 的 S8/S9 → 双标；案例 A 的 S1 与案例 C 的 S2 需要额外规则。

## 8. 请你评判的问题

1. 上述判据本身是否成立？有没有更干净的表述方式（尤其要考虑：标注者
   是 LLM，判据必须能被语言模型稳定执行，「可分述性」是否可判定）？
2. 如果要改，条款怎么改：是收窄第 37 行 "may be how even if it appears
   in a result sentence"，还是给第 64–65 行加判据，还是动 aspects 定义？
   请给出具体的替换文本。
3. 正反例的选择：案例 A（S4 作反例）+ 案例 B（S6 作正例）是否足以让
   LLM 学会边界？需要覆盖案例 C 的 S2 这类「背景经济力量」吗？
4. S1 型（问题陈述嵌入模型设定）是否需要同批处理？它与 mechanism 条款
   是同一个「嵌入信息何时算交付」问题的两个实例。
5. 收窄后 how 覆盖率会下降、narrow 口径 core3 覆盖也会略降——这在研究
   口径上是否可接受（我们的研究目标是描述已发表摘要的真实结构，不是
   证明模板成立）？

## 附：运行环境事实（与评判无关，仅备查）

prompt v0.2 已冻结用于本轮 pilot（hash c29f09b3…8bc5）；任何修改将进入
v0.3 并在下一批样本上重跑，不回改本轮数据。
