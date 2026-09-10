# Paper Writing Analysis Framework

## 一句话结论

分析论文写作时，应沿“paper -> section -> paragraph -> sentence -> lexico-grammar”逐层判断；下层表达必须服务上层论证，不能把局部流畅度当作最终目标。

## 五层框架

### 1. Paper-Level Argument

- Research question 是否清楚且重要。
- Gap 是否来自真实文献比较，而非修辞制造。
- Contribution 是否具体、可验证并与结果一致。
- Motivation、approach、evidence、result、implication 是否形成完整 narrative。
- 替代解释、局限和外推边界是否得到处理。

### 2. Section-Level Function

- Introduction：背景 -> puzzle/problem -> gap -> approach -> evidence preview -> contribution。
- Related Work：领域坐标 -> 代表文献 -> 差异 -> 当前项目的位置。
- Data：来源、样本、变量、选择过程、测量和局限。
- Methods：estimand/目标、识别假设、模型、实现、诊断。
- Results：估计对象、主结果、量级、不确定性、机制和稳健性。
- Discussion/Conclusion：回答问题、边界、贡献、局限与下一步。

这些顺序是分析问题的候选框架，不是所有领域都必须套用的固定模板。

### 3. Paragraph-Level Move

每段应能标注主要功能，例如 context、problem、gap、claim、evidence、comparison、qualification、transition 或 implication。段落首句、内部证据和收束句应围绕同一 controlling idea。

### 4. Sentence-Level Move

对每句至少问四个问题：

1. 这句话在当前段落中做什么？
2. 它依赖什么证据或前文？
3. 它的 claim strength 是否与证据相称？
4. 删除或改写后，上下句逻辑会发生什么变化？

### 5. Lexico-Grammar

- 精确用词、术语一致性和搭配。
- 主动/被动、时态、名词化、长 noun stack 和从句复杂度。
- hedging：may、suggest、consistent with、likely 等。
- boosting：demonstrate、establish、clearly、novel 等。
- transition、指代、信息结构和 given-new progression。
- 语法正确只是必要条件，不代表论证有效。

## 跨层错误

- Local improvement / global damage：句子更流畅，但删掉了 gap、限定或逻辑桥。
- Evidence laundering：把相关性、机制提示或 robustness 写成因果证明。
- Citation decoration：有引用，但引用并不支持该句 claim。
- Template overfit：段落形式像论文，却没有真实问题或贡献。
- Style normalization：统一成一种英语风格，抹掉领域、venue 或作者声音。

## 对本项目的影响

未来 benchmark 必须保留上下文和层级标签；未来 AI 应用也应先诊断当前层级，再决定自动修改、建议或评论。
