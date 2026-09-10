---
layer: detail
update_mode: append
line_budget: 200
role: "决策注册表与档案 —— 当前结论、生命周期，以及为什么选 A 不选 B"
read_when: "做设计选择、回看旧决策、想理解某东西为什么是这样时"
not_for: "操作规则（-> CONVENTIONS），未定论的讨论（-> SHORT_MEMORY/），演变叙事（-> HISTORY）"
---

# Decisions — AI Writing Lab

## Registry

| ID | Status | Topic | Current conclusion | Keywords | Detail |
|---|---|---|---|---|---|
| `DEC-001` | `governing` | 仓库边界与模块组织 | 单仓库 `AI_writing_lab` 承载多个方向；模块先有差异后抽公共；拆仓仅在触发条件出现时 | 仓库边界、单仓库、多仓库、拆分、writing_pipeline | [details](#dec-001) |
| `DEC-002` | `governing` | 学术方向命名与范围 | 学术方向称 academic（研究+写作），不用 academic_paper_writing：同时覆盖文献研究与论文表达认识 | 学术方向、academic_paper_writing、文献调研、定位 | [details](#dec-002) |
| `DEC-003` | `governing` | 学术方向内部区分 | 分为 research（内容定位：问题/贡献/证据）与 writing（表达组织：论文规划起草修订） | 研究内容 vs 表达组织、贡献声明、论证结构 | [details](#dec-003) |
| `DEC-004` | `governing` | 期刊案例观察的使用边界 | 论文写作特征是观察，可提假设不可断因果；观察与已验证建议分开记录 | 观察≠因果、写作特征、期刊青睐、模仿表面措辞 | [details](#dec-004) |
| `DEC-005` | `governing` | 评价实现原则 | 评价先拆可观察维度（套话/空泛/重复总结/机械结构等），区分跨场景与文体偏好 | 摆脱AI味、评价、可观察维度、文体偏好 | [details](#dec-005) |
| `DEC-006` | `governing` | 记忆系统与脚手架 | memory-docs（vibe-memory-system）作记忆层，research scaffold 提供研究目录；playwright_crawler 继续维护期刊数据 | memory-docs、research scaffold、docs、playwright_crawler | [details](#dec-006) |
| `DEC-007` | `governing` | public 仓库与数据版本化边界 | 仓库公开于 GitHub；LLM 调用缓存与含摘要全文产物不入库，只入派生层；凭据与私有路径走环境变量 | public 仓库、数据版本化、摘要全文、环境变量、gitignore | [details](#dec-007) |
| `legacy-apw:DEC-001` | `governing`（学术范围） | 迁入项目的跨层写作边界 | 局部表达服务整篇论证；五层 taxonomy 的具体标签仍待验证，与本仓 DEC-002/003 并存 | academic_paper_writing、跨层、rhetorical move | [原始记录](../archive/20260908_academic_paper_writing_migration/source_project/memory-docs/detail_mem/DECISIONS.md#dec-001) |
| `legacy-apw:DEC-002` | `governing`（学术范围） | 迁入项目的 validity-first 边界 | 事实与证据保持不能由流畅度抵消；rubric、阈值、schema 仍属 proposal，不改变通用 evaluation 预留状态 | validity、hard negative、rubric pilot | [原始记录](../archive/20260908_academic_paper_writing_migration/source_project/memory-docs/detail_mem/DECISIONS.md#dec-002) |

## 更新契约

- Registry 可 patch：状态、结论随生命周期更新；不删旧 ID。
- Detail 正常 append；rationale 不静默改写；被替代时追加新决策并互相链接。
- ID 一经发布永不复用。

## Details

### DEC-001

- 标题：仓库边界与模块组织——单仓库多方向
- 日期：2026-09-07
- 状态：`governing`
- 背景：曾考虑拆成 `academic_paper_writing`、`business_writing`、`writing_pipeline`
  三个平级仓库。但三者层次不同：前两者是应用方向，后者是可能被两者共用的实现。
  分别开发易产生两套起草/修订/审核/评价机制；过早抽公共 pipeline 会把未验证的相似性写死。
- 决策：总项目 `AI_writing_lab` 一个 Git 仓库，内部区分通用能力与应用方向；
  先允许差异，从实际复用中提取通用逻辑。`modules/writing_pipeline/`、`modules/evaluation/`
  只登记规划，不提前实现。
- 理由：单仓内多方向可独立立项、共享上下文，先验证相似性再抽象；拆仓成本可延后。
- 影响：拆仓触发条件——(a) writing_pipeline 接口稳定、需被其他项目单独安装/发布/调用；
  (b) 学术方向形成自己的数据集/实验体系/论文路线可独立推进；(c) 商业方向出现独立产品、
  协作者或访问权限边界。届时将成熟部分拆出。
- 证据 / 验证：仓库初始化已按此执行（2026-09-07）。
- 生命周期：governing（初始化即生效）

### DEC-002

- 标题：学术方向命名与范围
- 日期：2026-09-07
- 状态：`governing`
- 背景：学术方向从期刊数据库做 thorough 文献调研，可产生两种研究产出：研究内容的定位
  （已有研究解释了什么/争议/证据不足/贡献位置），以及论文表达与组织上的认识
  （如何建立背景、提问题、推进论证、回应替代解释、安排证据与限定）。
- 决策：学术方向用 `academic` 系命名（`academic_research/` + `academic_writing/`），
  覆盖两种产出；不使用只强调"写论文"的 `academic_paper_writing`。
- 理由：目标同时覆盖"研究什么、如何研究"与"如何把研究讲清楚"，比单一论文写作更贴切。
- 影响：目录 `modules/academic_research/`、`modules/academic_writing/` 分别承接两类认识。
- 证据 / 验证：本对话确认；目录已建立。
- 生命周期：governing

### DEC-003

- 标题：学术方向内部区分 research 与 writing
- 日期：2026-09-07
- 状态：`governing`
- 背景：文献调研中"研究内容定位"与"论文表达组织认识"是两种不同性质的知识。
- 决策：research 侧负责问题定位、贡献与证据组织（怎么研究）；writing 侧负责
  论文文本层面的规划、起草、修订与审核（怎么讲清楚）。两者可共享受众/结构/论证判断，
  但先各自推进，相似性验证后再上移公共层。
- 理由：两产出性质不同、更新节奏不同，分开便于独立推进与追踪。
- 影响：`modules/academic_research/` 与 `modules/academic_writing/` 职责边界清晰。
- 证据 / 验证：目录与 README 已按此建立（2026-09-07）。
- 生命周期：governing

### DEC-004

- 标题：期刊案例观察的使用边界（观察 ≠ 因果）
- 日期：2026-09-07
- 状态：`governing`
- 背景：从已发表论文可观察到反复出现的写作组织方式；但研究问题、设计、证据质量与
  表达方式是交织的，观察无法确认"某种写法就是期刊青睐它的原因"。
- 决策：已发表论文的写作特征用于提出和检验写作假设，但不作为因果证据。
  记录时分两类：「顶刊中反复出现的组织方式」（观察）与「已验证有效的写作建议」
  （证据）分开存放，避免从模仿文章滑向模仿表面措辞。
- 理由：保持假设与证据分离是研究设计的基本原则，防止把相关性写成因果。
- 影响：notes/ideas 分层均体现该区分；journal case 分析产出的组织方式笔记不直接
  作为"期刊偏好"结论。
- 证据 / 验证：作为研究设计原则保留在 CONVENTIONS 与 academic_research README。
- 生命周期：governing

### DEC-005

- 标题：评价实现原则（可观察维度优先）
- 日期：2026-09-07
- 状态：`governing`
- 背景："摆脱 AI 味"与"写得好"是笼统目标，无法直接比较修改前后是否更好。
- 决策：评价先拆成可观察问题：套话、空泛判断、重复总结、机械段落结构、不必要修饰、
  缺少具体信息、作者声音不一致。据此比较修改前后；并判断哪些维度跨场景成立、
  哪些只是文体偏好。学术领域专属标准保留在学术模块，不进通用 evaluation。
- 理由：只有可观察才能检验；领域专属标准与通用维度混在一起会破坏跨场景判断。
- 影响：`modules/evaluation/` 为预留模块，起步于维度清单而非抽象评分器。
- 证据 / 验证：拆解清单已写入 `modules/evaluation/README.md`。
- 生命周期：governing

### DEC-006

- 标题：记忆系统与脚手架选择
- 日期：2026-09-07
- 状态：`governing`
- 背景：初始化仓库时有多种结构约定可选（research scaffold 的 docs/ 占位 vs
  成熟 memory-docs 模板）；期刊数据已有独立采集仓库。
- 决策：记忆层用 `memory-docs/`（vibe-memory-system 三层结构模板，本地安装）；
  研究目录按 research scaffold 职责建 notes/ideas/papers/repos/data/modules/manuscripts；
  顶层入口用 `AGENTS.md`。期刊数据采集与维护留在 `playwright_crawler`，本仓库只消费。
- 理由：与本机既有项目（playwright_crawler 等）的 Agent 生态一致，模板与校验器可复用；
  避免重复建立 docs 占位体系。
- 影响：`memory-docs/` 已安装标准文件；`AGENTS.md` 含三层结构指引与仓库特定规则。
- 证据 / 验证：安装器输出 13 个标准文件并通过校验（2026-09-07，仅 STATUS 日期 warning，已补）。
- 生命周期：governing

### DEC-007

- 标题：public 仓库与数据版本化边界
- 日期：2026-09-10
- 状态：`governing`
- 背景：项目首次推送 GitHub public（`Rostopher/AI_writing_lab`）。摘要结构运行产物
  包含付费 API 产出与五刊摘要全文：摘要在期刊网站公开，但把 4250+ 篇全文打包进
  public 仓库属于批量再分发，有版权投诉风险；代码中曾硬编码本机私有绝对路径
  （LLMClient/.env、playwright_crawler 数据集）。
- 决策：① 逐论文 LLM 调用缓存（`requests/`/`responses/`，约 9700 个文件）不入库；
  ② 含摘要全文的产物（`corpus_manifest.jsonl`、`dev_set_manifest.jsonl`、
  `*annotations*.jsonl`）经 .gitignore 留本地；③ 派生指标、比较 JSON、样本/运行
  manifest、报告入库；④ LLM 凭据与上游数据根经环境变量配置
  （`DEEPSEEK_API_KEY` / `DEEPSEEK_ENV_FILE` / `ABSTRACT_STRUCTURE_UPSTREAM_ROOT`），
  代码不设私有默认路径。
- 理由：缓存可再生、全文有再分发风险；派生层已足以支撑报告结论与复核；
  私有路径公开违反「不提交机器特定配置」约定。
- 影响：clone 仓库无法直接复算全链路（派生 JSON 的 inputs 引用本地文件）；
  新数据产物按同一口径逐份决定；推送前检查是否触碰该边界。
- 证据 / 验证：commit `91bba2f`–`00bf243`（2026-09-10）；.gitignore 规则；
  环境变量化后 68 个 pytest 全部通过（无环境变量时真实上游 smoke 正确 skip）。
- 生命周期：governing

### 2026-09-08 迁入说明

用户授权将姊妹仓库旧学术写作项目材料迁入当前仓库。旧 DEC-001/002 使用
`legacy-apw:` 命名空间保留检索，原始理由与证据原样归档；不与本仓 DEC 编号混用。
这些设计边界仅适用于学术写作方向，具体分类和评价方案仍待验证。迁移未开展
实验或实现通用评价器，静态 skills 调研排名仍不能作为实测结论。
