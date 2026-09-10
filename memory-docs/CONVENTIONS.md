---
layer: framework
update_mode: patch
role: "硬规则 / 约定 —— 该遵守什么（不讲为什么，为什么 -> DECISIONS）"
read_when: "动代码前、问风格 / 命名 / 契约 / 安全约束时"
not_for: "决策来由（-> DECISIONS），运行方式（-> 仓库 RUNBOOK / README），一次性偏好"
---

# Conventions — AI Writing Lab

## 仓库结构

- 主线路径：`modules/`（可执行研究）、`notes/`（研究理解）、`manuscripts/`（正式写作）
- 记忆层：`memory-docs/`（vibe-memory-system 三层结构，见 `INDEX.md`）
- 数据采集不在本仓库：期刊数据由姊妹仓库 `playwright_crawler` 采集维护
- 论文全文工作区：`papers/`，由 paper-workspace 物化，**生成物不手改**
- 参考仓库：`repos/` 默认只读

## 方向与抽象纪律（最重要）

- **先允许差异，后提取共性**：模块按方向各自实现；同一机制被两个方向实际需要、
  且接口趋于稳定后，才上移为 `modules/writing_pipeline/` 公共实现。禁止提前抽象。
- 学术/商业方向的领域专属标准（学术：贡献声明、引用支持、因果限定；商业：
  决策建议、执行条件、行动指引）**不并入通用层**，保留在各自模块内。
- **观察 ≠ 因果**：已发表论文中观察到的写作特征仅用于提出/检验假设，不写入
  "期刊青睐某种写法"的因果断言；「顶刊反复出现的组织方式」（观察）与
  「已验证有效的写作建议」（证据）分开记录。
- 评价写作质量前先把目标拆成**可观察问题**（套话、空泛判断、重复总结、机械段落
  结构、不必要修饰、缺少具体信息、作者声音不一致），比较修改前后是否更好；
  并标记哪些维度跨场景成立、哪些只是文体偏好。

## 内容分层规则

- 学术写作迁入材料沿用事实保持边界：不得制造或改变事实、数字、引用、结果、贡献或作者意图；
  意义漂移、删除必要限定与过度宣称须单独报告，不能由流畅度或综合分抵消。
- 写作 taxonomy、rubric、benchmark schema 及 skills 排名在实证验证前保留 proposal 状态。
  生成与审核保留独立证据，不能仅由生成者自评宣布通过。
- 外部参考快照保留来源、revision 与许可；只读参考，不将其测试或 benchmark 结果当作本项目结果。

- `notes/`：消化后的研究笔记（paper-reading / methods / data / concepts / pipelines），
  自由记录优先，不强求模板
- `ideas/`：未定型想法，每个至少写清 claim、证据需求、最小验证、失败条件
- 未稳定讨论 → notes/ideas；稳定事实 → memory-docs；面向读者文本 → manuscripts/
- 生成产物（papers/ 全文、metadata）自动生成、不手改

## 命名与结构

- 自有目录 / 文件：`snake_case`；新探针用 `probe_`，正式测试通常为 `test_*.py`；
  既有名称按用途理解，外部参考仓库保留上游命名。
- 模块边界：一个模块一个语义清晰目录，含 README.md；输出路径可配置、可追踪，
  默认可放模块内 `outputs/`，长日志进 `logs/`。
- 文档语言：中文；文档与实现冲突时**以实现为准**并指出

## 数据 / 接口契约

- `data/`：逐份数据决定是否版本化（大小、许可证、隐私、可复现性）
- public 仓库数据边界（DEC-007）：逐论文 LLM 调用缓存（`requests/`/`responses/`）与
  含摘要全文的产物（`corpus_manifest.jsonl`、`dev_set_manifest.jsonl`、
  `*annotations*.jsonl`）不入库；派生指标、比较 JSON、manifest、报告入库
- papers 全文来自 playwright_crawler 数据物化，本仓库不重复采集
- 大文件禁止整载入内存/上下文，默认头预览、抽样、流式处理

## 安全与错误处理

- 暴露真实错误，不预埋静默 fallback、空值替代或 `except: continue`
- Python 路径使用 `pathlib.Path`，按脚本资源、项目配置或显式输入定位，不隐式依赖 cwd。

## 环境规则

- Python：全局共享虚拟环境 `F:/global_venv/.venv/Scripts/python.exe`（项目未设独立 venv）
- Git 远端：GitHub public `Rostopher/AI_writing_lab`（2026-09-10 建立；推送前检查
  是否触碰 DEC-007 数据边界）
- LLM 凭据与上游数据根经环境变量配置，不落代码与文档默认值：
  `DEEPSEEK_API_KEY`（或 `DEEPSEEK_ENV_FILE` 指定 .env）、
  `ABSTRACT_STRUCTURE_UPSTREAM_ROOT`（playwright_crawler 数据集）
- 涉及数据处理/回归/诊断/测试/绘图任务时优先遵循 `research-engineering` skill 约定
- 本地绝对路径、密钥、token 不提交
