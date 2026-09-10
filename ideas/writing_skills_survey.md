# Writing Skills 综述与评价维度 — Proposal

> 状态：proposal（2026-09-01）。基于 `repos/` 六个固定快照仓库的逐 skill 调研。
> 用途：为"学术写作 agent skill 从夯到拉"的对比提供文献综述表 + 评价维度草案。
> 尚未经任何实证验证；维度与分档在 pilot 后才可进入稳定层。

> 2026-09-08 后续核验：econ-writing-skill 已完成[首轮精读与来源抽查](../notes/pipelines/econ_writing_skill_review.md)。
> 下方初步档位保留为 2026-09-01 的历史判断；其中对 econ-write 的护栏与验证评价应结合新发现：
> 政策短评分支允许补示意数值，写作 eval 尚无执行结果，部分规则是有取舍的来源改编。不可将原排名视为效果结论。

## 1. 仓库总览表

| 仓库 | 形态 | 学科 | 生命周期覆盖 | 证据基础 | 评价/验证机制 | 初步档位 |
|---|---|---|---|---|---|---|
| `AER-Skills` | 15 skill 栈（workflow 路由） | 经济学 top-5 实证（锁定极死） | 选题→文献→识别→预注册→稳健性→正文→引言→图表→一致性→模拟审稿→复现→投稿→rebuttal | 很强：Crossref 核验文献 + AEA 官方政策 + 真实 exemplars | 很强：脚本化门控 + 272 单测 + verdict 校准 CI + skill 自评协议 | 第一梯队（夯） |
| `econ-writing-skill` | 单 skill（739 行） | 经济学全谱 | 写作/改写/审稿为主，延伸到 response、基金、slides、replication | 很强：50+ 署名权威来源分级（SOURCES_RANKED） | 中：100 分 rubric + 三审稿人 + 18 个 eval 用例，但无自动 runner | 第一梯队（夯） |
| `nature-skills` | 19 skill + 1 共享包 | Nature 系为主，泛化到通用 | 最全：选题/检索/精读/写作/润色/统计/图表/审稿/返修/专利/日志 | 较强：Nature 官方政策存档 + CONSORT 等指南 + 语料蒸馏（分级标注） | 不均：response/proposal 有 rubric+fixture；写作核心多为 Draft，无输出质量 eval | 偏夯（前 20–30%） |
| `revise-paper` | 单 skill（156 行） | CS/图形学倾向 | 写作后期：润色、结构审查、参考文献核验、投稿就绪 | 弱：经验规则 + 少量格式规范 | 弱：编译循环为客观信号；无 evals/rubric | 中等偏上（理念好、实现轻） |
| `anti-defensive-writing` | 单 skill（185 行） | 通用学术 + grant/报告 | 仅风格层改写（去防御性写作） | 无：纯经验规则，无引用 | 无：CI 只查工程一致性 | 中（聚焦干净，无护栏） |
| `NaturePanelForge` | 单 skill + benchmark 仓库 | Nature 系图表（非写作） | 仅图表复现 | 强：8385 panel 真实数据集 | 很强：14 维评分协议 + 执行门 + anti-gaming + 11 模型结果 | 非写作类；评价协议参考=夯 |

## 2. 关键差异点（综述要点）

- **"写作 skill"其实是三类东西**：(a) 风格/语言层改写工具（anti-defensive-writing、econ-write 的 Rewriting、nature-polishing）；(b) 全流程工作流栈（AER-Skills、nature-skills）；(c) 评审/诊断模拟（aer-referee-sim、nature-reviewer、econ-write Auditing）。对比时必须按类分层，不能直接混排。
- **证据基础是第一分水岭**：AER/econ-write 的规则带署名出处（Cochrane、McCloskey、Head、Bellemare）且经 Crossref/官方政策核验；nature-skills 区分"官方政策 vs 语料蒸馏经验"；anti-defensive-writing 和 revise-paper 基本无外部证据。
- **validity 护栏的有无**：多数仓库有"禁止编造引用/数据"条款（revise-paper 最强硬，nature-shared/ethics 有三级风险框架，econ-write 有 AI 披露+核验条款）；**反例**：anti-defensive-writing 的 after 示例演示了"模糊声称→具体数字"的改写，却无任何防虚构机制——正是本项目定义的 validity failure 风险。
- **评价机制普遍是最弱环**：只有 AER-Skills（CI 强制门）和 NaturePanelForge（真实 benchmark）把评价做成可执行工件；econ-write 的 18 个 eval 用例靠人工核对；nature-skills 的 evals.json 只是 prompt→expected 描述；其余为零。
- **权限分流设计值得单独立项**：revise-paper 的 auto/suggest/comment 三级、AER 的 go/no-go gate、nature-proposal-writer 的阈值回退，都是"哪些改动可自动执行"的不同回答——直接对应项目 RQ2。

## 3. 评价维度草案（用于 skill 自身的"从夯到拉"）

注意：这是评价 **skill 本身** 的维度，与 `evaluation_design.md` 中评价 **写作输出** 的 P0–P3/R 维度互补，不混用。

| # | 维度 | 核心问题 | 可核验信号 |
|---|---|---|---|
| D1 | 定位与适用范围 | 学科/环节/用户是否明确声明？ | 有无显式 scope 声明与排除项（AER 最佳实践） |
| D2 | 内容深度与结构 | 规则是否操作化，还是空泛建议？ | workflow/checklist/分类法/示例的密度；可否逐步执行 |
| D3 | 证据基础 | 规则有出处吗？ | 署名来源数、分级清单、官方政策存档、Crossref 核验 |
| D4 | Validity 护栏 | 防编造/防过度宣称/保真有硬约束吗？ | 禁编造条款、占位符机制、claim-evidence 追踪、核验脚本 |
| D5 | 评价与验证机制 | 怎么知道 skill 输出是对的？ | evals 数量与自动化程度、rubric 锚点、CI 门、一致性测试 |
| D6 | 工程化与可复现 | 安装/镜像/契约可靠吗？ | 安装脚本、字节级镜像一致性、产物契约、版本与状态标签 |
| D7 | 诚实边界 | 是否声明能力上限？ | "模拟不能认证 accept"类声明、Draft/Beta/Stable 标注、未验证声明 |
| D8 | 对本项目的可迁移性 | 维度/协议能否借用到我们的 rubric？ | 与 P0 validity gate、hard negatives、分层维度的对接点 |

初步排序（D1–D7 综合）：**AER-Skills ≳ econ-writing-skill > nature-skills > revise-paper > anti-defensive-writing**；NaturePanelForge 单列（非写作 skill，但 D5 维度全场最强）。

## 4. 对本项目评价设计的直接输入

- D4 的护栏清单 → 并入 P0 validity gate 的检查项来源。
- NaturePanelForge 的"执行失败即归零 + 拒绝单一总分 + anti-gaming 指标"→ 可移植为写作 benchmark 的协议骨架。
- revise-paper 三级分流 + AER gate 契约 → RQ2（哪些修改可自动执行）的候选答案空间。
- econ-write 的 evals 无 runner、nature-skills 写作 eval 缺失 → 说明"skill 评价自动化"本身是空白，可成为论文贡献点。

## 5. 下一步建议

1. 把 D1–D8 做成最小打分卡，对 6 仓库各 skill 打一轮分，检验维度是否可稳定区分（rubric pilot 的 skill 版）。
2. 对第一梯队（AER、econ-write、nature-skills）做第二轮深读：逐条提取可迁移的 validity 检查项与 rubric 锚点，沉淀到 `notes/pipelines/`。
3. 决定对比表的正式 schema（字段、证据链接、分档规则）后再进入 memory-docs 稳定层。
