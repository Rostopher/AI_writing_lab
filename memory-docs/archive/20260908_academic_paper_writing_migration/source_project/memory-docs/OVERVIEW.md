---
layer: framework
update_mode: rewrite
role: "项目是什么 —— 一页纸的整体认知（做什么、怎么组织、技术栈）"
read_when: "进入项目、问架构 / 范围 / 技术栈时"
not_for: "当前进度（-> STATUS），项目演变（-> HISTORY），术语（-> GLOSSARY），代码位置（-> MAP）"
---

# Project Overview

## 一句话定位

Academic Paper Writing 研究高质量学术论文如何形成，并把整体论证、修辞功能、
句子表达与评价机制转化为可复现的知识、实验、benchmark 和 AI 应用。

## 目标

- 建立从整篇论文到词句语法的多层写作分析框架，避免把写作等同于语言润色。
- 从论文写作研究、真实修订材料和外部工具中提取可验证的共同机制。
- 设计能识别意义漂移、过度宣称等 hard negatives 的多维 evaluation。
- 在评价可靠后，探索可审计的论文诊断、修订与审核工具。

## 主要工作流

```text
写作研究、授权材料与参考仓库
  -> pipeline 审计和写作层级 / failure taxonomy
  -> rubric 与修订对 pilot
  -> validity gate、多维质量和一致性评价
  -> benchmark、AI writing assistant 与论文
```

## 核心区域

| 区域 | 角色 | 入口（详见 detail_mem/MAP.md） |
|---|---|---|
| 概念研究 | 描述 paper 到 lexico-grammar 的分析层级与跨层错误 | `notes/concepts/paper_writing_analysis_framework.md` |
| 参考仓库研究 | 审计外部工具的流程、产物、评价和可迁移边界 | `notes/pipelines/reference_repo_comparison.md` |
| Evaluation | 设计 validity gate、任务族、hard negatives 与 reliability | `ideas/evaluation_design.md` |
| 可执行模块 | 后续承载仓库审计、标注、evaluation 与实验 | `modules/README.md` |

## 技术与数据状态

- 当前以 Markdown 研究协议和本地 Git 参考仓库为主，尚未确定正式实现栈。
- 数据、rubric 和 benchmark schema 均处于 proposal 阶段，尚无已验证数据集或模型结果。
- `repos/` 中外部仓库为固定快照和只读研究输入，不属于本项目实现。

## 相关文档

- 当前状态：`memory-docs/STATUS.md`
- 项目演变：`memory-docs/HISTORY.md`
- 术语：`memory-docs/GLOSSARY.md`
- 约定：`memory-docs/CONVENTIONS.md`
- 代码导航：`memory-docs/detail_mem/MAP.md`
