---
layer: detail
update_mode: patch
role: "概念 → 入口文件的快速导航（只记入口，不记全量清单）"
read_when: "要找某功能 / 概念的代码在哪、追溯某产物的来源时"
not_for: "术语定义（-> GLOSSARY），当前状态（-> STATUS），全量端点 / 组件 / 字段清单（留在代码里）"
---

# Map — 概念 → 入口文件

> **本文件的边界（重要）：**
>
> MAP 只记 **概念 / 功能 → 1-2 个入口文件**，是给 Agent 的**快速导航指针**。
> Agent 拿到入口后，剩下的自己读代码。
>
> **不要**把全量 API 端点、全量前端组件、全量数据字段、全量配置都列进来。
> 那样会让 MAP 随项目线性膨胀，违背"快速导航"的初衷。
> 全量信息天然在代码里；个别需要详细展开的主题，建子文件夹并在 `DIRS.md` 登记，
> MAP 里只留一行指针。

## 项目边界与研究问题

- 入口：`README.md`
- 入口：`ideas/project_charter.md`

## 写作层级与跨层错误

- 入口：`notes/concepts/paper_writing_analysis_framework.md`

## 参考仓库 pipeline 审计

- 入口：`notes/pipelines/reference_repo_comparison.md`
- 入口：`repos/README.md`

## Evaluation 与 benchmark proposal

- 入口：`ideas/evaluation_design.md`
- 入口：`modules/evaluation/README.md`

## 可执行研究模块

- 入口：`modules/README.md`

## 规则

- 一个概念只挂 **1-2 个入口文件**，多了就说明该建子文件夹了。
- 文件改名 / 删除时同步更新本文件。
- 保持指针和映射，不写长篇解释。
