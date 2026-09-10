---
layer: framework
update_mode: patch
role: "项目术语 —— 当我说 X，我指的是什么（定义，不讲位置）"
read_when: "遇到不熟悉的术语、问命名 / 数据字段含义时"
not_for: "代码位置（-> MAP），硬规则（-> CONVENTIONS）"
---

# Glossary

> 定义项目里反复出现的术语、变量、标签、展示名。
> 这里讲"**是什么**"，不讲"**在哪里**"（位置去 `detail_mem/MAP.md`）。

## 项目术语

### Rhetorical move

- 定义：一句、一个段落或一个 section 在当前论证中承担的功能，如 context、gap、claim、evidence、qualification 或 implication。
- 易混淆点：它描述“这段话在做什么”，不是仅按关键词划分的主题类别。

### Claim strength

- 定义：文本对结论确定性、因果性、普遍性和新颖性的承诺强度。
- 易混淆点：更自信不等于更好；强度必须与证据和研究设计相称。

### Validity gate

- 定义：在评价语言质量前检查事实、数字、引用、术语、证据边界和作者意图是否保持的硬门槛。
- 易混淆点：validity 不是可被流畅度高分抵消的普通加权维度。

### Hard negative

- 定义：表面更流畅或形式更像论文，但存在过度宣称、意义漂移、错误修辞功能或引用不支持等关键缺陷的候选。
- 为什么重要：用于阻止 benchmark 奖励风格捷径。

### Human utility

- 定义：修改对作者或评审者的实际帮助，包括接受率、节省时间、返工量和解释可用性。
- 易混淆点：它不同于脱离工作流的文本偏好分数。

### Reliability

- 定义：人—人、人—自动 judge、judge 重复运行之间的一致性及其不确定性。

### Authority

- 定义：对某类事实或修改拥有最终解释权的来源，例如 LaTeX source、渲染 PDF、原始证据或作者意图。

## 相关文档

- 代码位置：`memory-docs/detail_mem/MAP.md`
- 约定：`memory-docs/CONVENTIONS.md`
