---
layer: framework
update_mode: patch
role: "硬规则 / 约定 —— 该遵守什么（不讲为什么，为什么 -> DECISIONS）"
read_when: "动代码前、问风格 / 命名 / 契约 / 安全约束时"
not_for: "决策来由（-> DECISIONS），运行方式（-> 仓库 RUNBOOK / README），一次性偏好"
---

# Conventions

> 记录项目里**必须遵守**的硬规则、稳定契约、命名约定、安全约束。
> 这些规则**增长很慢**，属于框架层。如果某类规则开始大量膨胀，考虑拆进子文件夹并在 `DIRS.md` 登记。

## 仓库结构

- 主线研究材料放在 `notes/`、`ideas/` 和 `data/`；可执行实现放在 `modules/<module>/`。
- `repos/` 是外部参考仓库，默认只读；先把理解写入 `notes/pipelines/`。
- 正式论文、报告和附录进入 `manuscripts/`，不要与外部论文工作区 `papers/` 混放。
- 当前没有已启用的自动生成产物目录。

## 命名与结构

- 项目与模块目录使用小写 `snake_case`。
- 项目级研究问题独立建模块，不在项目根堆放脚本和运行产物。
- Python 路径必须由 `Path(__file__).resolve()` 拼接，不依赖 `cwd` 或裸相对路径。
- 修改 Python 核心逻辑前先写 `_test_*.py` 或最小诊断脚本。

## 安全与错误处理

- 数据、证据或许可不明确时标记 unknown / needs confirmation，不虚构或静默补值。
- 不允许静默跳过会改变研究口径、样本或评价结论的错误。
- 自动修订必须保留原文、上下文、禁止改变项、候选和审核证据。
- 事实、数字、引用、结果、贡献或作者意图发生漂移时必须判定 validity failure。

## 数据 / 接口契约

- 当前尚无稳定 benchmark schema；`ideas/` 中的 schema 与 rubric 均为 proposal。
- 评价至少区分 validity、局部语言、discourse、人类效用与 reliability。
- validity failure 是 gate，不能被其他维度平均抵消。
- 生成与审核角色分离，评价按 section、领域、任务和风险分组报告。

## 产物规则

- 日志和运行产物沿 `modules/<module>/logs/`、`outputs/` 保存。
- 最终研究写作交付进入 `manuscripts/`。
- 外部仓库、大数据和二进制材料不纳入主仓库；大文本和结构化数据优先抽样、分块或流式读取。

## 文档（memory-docs）维护规则

- 框架层文件**保持精简**，不随项目膨胀。
- 新增 API / 功能 → `detail_mem/MAP.md` 加**一行**（概念→入口文件），`STATUS.md` 加**一句话**。
- 重大选择 → `detail_mem/DECISIONS.md` 加**一条**。
- 会话交接 → `SHORT_MEMORY/`；定稿沉淀 → `HISTORY.md`。
- 建新子文件夹 → `DIRS.md` 登记**一行**。
- 代码与文档冲突，**以代码为准**，并修文档或标记。

## 环境规则

- 运行时版本：尚未确定，随首个可执行模块确认。
- 依赖管理：优先 `uv + venv`。
- 环境变量策略：使用示例文件记录变量名，不提交真实值。
- 本地路径 / 密钥策略：不提交本机绝对路径、密钥、token。
