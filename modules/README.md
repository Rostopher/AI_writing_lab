# Modules

可执行研究工程层：与写作研究相关的数据处理、分析、评价、流程实现。每个模块独立成目录。

## 规划中的模块

| 模块 | 职责 | 状态 |
|---|---|---|
| `writing_pipeline/` | 通用写作流程（规划—起草—修改—审核）。从跨方向的真实复用中提取，不提前抽象 | 预留 |
| `academic_research/` | 学术研究模块：文献调研、问题定位、期刊案例分析 | **首个推进方向** |
| `academic_writing/` | 学术写作模块：论文规划、起草、修订与审核 | 待启动 |
| `evaluation/` | 评价实现：可观察的写作质量维度与领域专属标准 | 预留 |
| `business_writing/` | 商业写作（面向决策与行动） | 有具体任务后再建立 |

## 模块规范（建立具体模块时遵循）

```text
modules/<module-name>/
  README.md      # 模块职责、口径、如何运行
  PLAN.md        # 需要时：目标与阶段
  probe_*.py     # 按需建立的局部探索
  test_*.py      # 持续保护明确行为的正式测试
  run_*.py       # 主入口
  outputs/       # 生成结果（tmp 忽略）
  logs/          # 长任务日志（gitignore）
```

## 规则

- 路径使用 `pathlib.Path`，按脚本资源、项目配置或显式输入定位，不隐式依赖 `cwd`。
- 输出路径可配置、可追踪；默认可放模块内 `outputs/`，长日志进 `logs/`。
- 评价标准与领域规则若跨方向复用，先各自实现、验证相似性后再上移公共层，
  不提前造通用 `writing_pipeline`。

## 已接续的研究材料

旧 `academic_paper_writing` 的参考研究与学术评价设计分别进入 `notes/` 和 `ideas/`，
可从 [academic_writing](academic_writing/README.md) 接续。旧 `repository_studies` 和
`evaluation` 仅有模块说明，保留于迁移档案；没有迁入可执行模块，也不据此提前建立通用评价器。
