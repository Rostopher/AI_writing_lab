---
layer: detail
update_mode: patch
role: "模块 / 功能级实现清单 —— 各模块做到什么程度（清单，非流水账）"
read_when: "要看模块完成度、做多模块工作、查某模块是否实现时"
not_for: "高层状态（-> STATUS），决策来由（-> DECISIONS），带日期的变更流水（-> archive/）"
---

# Progress — 模块级实现清单

> 更新：2026-09-08。旧学术写作材料已迁入；目前有研究设计与参考分析，尚无业务实现或实验结果。

## 主线

- 主路径：`modules/academic_research/`（学术方向为首个推进方向）
- 主入口：尚未建立
- 当前权威实现：无（尚未开发）

## 已实现

- 目录与项目入口已建立。
- 研究材料：`notes/concepts/paper_writing_analysis_framework.md` 保存五层候选分析框架；
  `notes/pipelines/` 保存两仓详细分析与对比；`ideas/writing_skills_survey.md` 保存六仓静态调研。
- 六个外部参考仓库位于 `repos/`，保留来源、固定快照和许可；参考实现不等于本项目已实现能力。
- 原项目说明、记忆和目录骨架归档；迁移完整性由
  [manifest](../archive/20260908_academic_paper_writing_migration/manifest.md) 路由。

## 进行中

- 学术方向起步：首个主题、样本和执行任务尚未选定。
- 学术写作评价设计：`ideas/evaluation_design.md` 提出 validity gate、分层评价、
  hard negatives 与评审一致性验证；缺少经验证 rubric、适用修订对与评审数据。
- 原项目的下一步候选是少量 Introduction 样本的 rubric pilot；迁移不构成实验启动或结果确认。

## 未开始 / 缺口

- `modules/academic_research/`：实际文献调研、问题定位与期刊案例分析尚未执行；已有可参考的写作框架与工具调研。
- `modules/academic_writing/`：规划、起草、修订、审核尚无实现；学术评价 proposal 在 ideas 中接续。
- `modules/writing_pipeline/`：通用写作流程 —— **预留**，不提前实现；触发条件见 DEC-001
- `modules/evaluation/`：评价实现 —— **预留**；先要确定可观察维度与领域专属标准
- `modules/business_writing/`：**未建立**，有具体任务后再创建
- 数据接入：`papers/` 物化与工作区建立 —— 待评估（依赖 playwright_crawler 数据）

## 相关文档

- 高层状态：`memory-docs/STATUS.md`
- 决策：`memory-docs/detail_mem/DECISIONS.md`
- 代码导航：`memory-docs/detail_mem/MAP.md`
