---
layer: detail
update_mode: append
line_budget: 200
role: "决策注册表与档案 —— 当前结论、生命周期，以及为什么选 A 不选 B"
read_when: "做设计选择、回看旧决策、想理解某东西为什么是这样时"
not_for: "操作规则（-> CONVENTIONS），未定论的讨论（-> SHORT_MEMORY/），演变叙事（-> HISTORY）"
---

# Decisions

> 用紧凑 registry 快速找到当前结论，再按需读取详细理由或 archive。
>
> - `DECISIONS.md` 是**决策查找表**：registry 回答当前结论和生命周期，
>   detail 保留来由和取舍。
> - `HISTORY.md` 是**叙事线**：把多条决策串成项目演变的故事。两者互补。

## Registry

| ID | Status | Topic | Current conclusion | Keywords | Detail |
|---|---|---|---|---|---|
| `DEC-001` | `governing` | 项目研究边界 | 同时研究整体论证、修辞功能和词句表达；项目不是单纯的语法润色器 | paper writing, narrative, rhetorical move, wording | [details](#dec-001) |
| `DEC-002` | `governing` | Evaluation 架构 | 先做不可被平均掉的 validity gate，再分维度评价质量、效用和可靠性；具体 rubric 仍须 pilot 验证 | evaluation, validity gate, hard negative, reliability | [details](#dec-002) |

Status 使用：

- `active`：稳定选择正在执行或验证，尚未形成长期默认；
- `governing`：当前规则、默认或设计边界；
- `closed`：路线已明确停止；
- `superseded`：已由另一 ID 替代；
- `historical`：只为解释历史保留，不再约束当前工作。

`Current conclusion` 必须能脱离详细记录独立理解，`Keywords` 使用未来读者会自然搜索的词。

## 更新契约

为兼容既有工具，frontmatter 仍为 `update_mode: append`。文件内部采用以下混合契约：

- **Registry 可 patch**：状态、当前结论、关键词和 detail 指针应随生命周期更新；
  不删除旧 ID，也不把旧 ID 分配给新含义。
- **Detail 正常 append**：新增决策追加独立记录；已有 rationale 不静默改写。
  被替代时追加新决策或带日期的 closure note，并从 registry 互相链接。
- **受控 rollover**：接近 `line_budget` 时，可在先更新 registry 后，把
  `closed` / `superseded` 的完整 rationale 移入 archive；registry 行和可用 detail
  指针必须保留。

ID 一经发布永不复用。迁入旧账若与本项目 ID 冲突，使用稳定 namespace，例如
`legacy-2024-06/DEC-001`，不要让同一个裸 ID 指向两个决定。

计划默认只是 proposal，不能据此断言当前状态。计划完成、停止或被替代时，必须留下
明确的 `closure` / `superseded` 指针，连接计划、registry 当前行以及确认它的
代码、产物、实验记录或 archive manifest。

## Details

### DEC-001

- 标题：论文写作项目采用跨层研究边界
- 日期：2026-09-01
- 状态：`governing`
- 背景：用户希望同时研究论文的整体思路与文献比较，以及 Introduction、Data 等部分中每句话的用词、句式、语法和论证强弱。
- 决策：研究单位覆盖 paper、section、paragraph、sentence 和 lexico-grammar；局部表达必须服务上层论证。
- 理由：只优化语法或流畅度无法判断 gap、贡献、证据边界和整体 narrative 是否成立。
- 影响：参考仓库研究、数据 schema、benchmark 和应用都必须保留多层上下文与 rhetorical function。
- 证据 / 验证：用户项目目标；`ideas/project_charter.md`；`notes/concepts/paper_writing_analysis_framework.md`。
- 生命周期：用户确认项目范围后直接 governing；候选 taxonomy 的具体标签仍待文献与 pilot 验证。
- 演变关联：见 `memory-docs/HISTORY.md`

### DEC-002

- 标题：Evaluation 采用 validity-first 的多维架构
- 日期：2026-09-01
- 状态：`governing`
- 背景：论文写作的 evaluation 很难；流畅改写可能同时造成意义漂移、删除限定或过度宣称。两个参考项目也没有提供可直接采用的文本写作可靠性证据。
- 决策：先检查事实、数字、引用、claim strength 和作者意图保持；通过后再分别报告局部语言、discourse、人类效用与 reliability。生成和审核角色分离，aggregate 只作次要摘要。
- 理由：真实性和证据边界属于合格性条件，不能被其他质量分数抵消；多维与分组结果才能诊断失败来源。
- 影响：benchmark 必须包含 hard negatives，自动 judge 必须与人类标注校准，具体 rubric 在验证前留在 `ideas/`。
- 证据 / 验证：`ideas/evaluation_design.md`；`notes/pipelines/reference_repo_comparison.md`。当前只有设计证据，尚无人类一致性或模型实验结果。
- 生命周期：评价架构为 governing 设计边界；rubric、阈值、权重和 schema 仍处 proposal，待 pilot confirmation。
- 演变关联：见 `memory-docs/HISTORY.md`
