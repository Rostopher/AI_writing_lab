---
layer: detail
update_mode: patch
role: "概念 → 入口文件的快速导航（只记入口，不记全量清单）"
read_when: "要找某功能 / 概念的代码在哪、追溯某产物的来源时"
not_for: "术语定义（-> GLOSSARY），当前状态（-> STATUS），全量端点 / 组件 / 字段清单（留在代码里）"
---

# Map — 概念 → 入口文件

> MAP 只记**概念 / 功能 → 1-2 个入口文件**，是给 Agent 的**快速导航指针**。
> 拿到入口后，剩下的自己读代码。
>
> 当前已有迁入的研究设计与参考材料，尚无业务实现。模块目录仍为规划入口。

## 研究材料层

- 期刊论文工作区：`papers/`（待 paper-workspace 物化；生成物勿手改）
- 原始/派生数据：`data/`
- 参考仓库：`repos/`（只读）

## 已有研究入口

- 写作分析层级：[五层框架](../../notes/concepts/paper_writing_analysis_framework.md)。
- 研究问题与评价候选方案：[charter](../../ideas/project_charter.md)、[evaluation proposal](../../ideas/evaluation_design.md)。
- 参考工具研究：[六仓 skills 调研](../../ideas/writing_skills_survey.md)、[两仓 pipeline 比较](../../notes/pipelines/reference_repo_comparison.md)。
- 六个参考快照及来源：[repos 入口](../../repos/README.md)。
- 旧项目路径、版本和历史决策：[迁移档案](../archive/20260908_academic_paper_writing_migration/manifest.md)。

## 模块（规划中 → 建立后更新真实入口）

- 学术研究（文献调研、问题定位、期刊案例）：`modules/academic_research/`
- 学术写作（规划、起草、修订、审核）：`modules/academic_writing/`
- 通用写作流水线（预留）：`modules/writing_pipeline/`
- 评价实现（预留）：`modules/evaluation/`
- 商业写作（待任务出现后建立）：`modules/business_writing/`

## 规则

- 一个概念只挂 1-2 个入口文件，多了就说明该建子文件夹了。
- 文件改名 / 删除时同步更新本文件。
- 保持指针和映射，不写长篇解释。
