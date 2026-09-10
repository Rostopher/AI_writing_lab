# Repos

这里保存六个外部参考仓库的固定快照，用于理解写作工具、研究 pipeline、审查协议和评价方法。参考仓库默认只读；项目自己的代码进入 `modules/`，复现说明与 pipeline 理解进入 [`notes/pipelines/`](../notes/pipelines/)。

## 固定快照导航

| 目录 | 来源 | 固定快照（HEAD） | 分支 | 许可 | 可观察的研究用途 |
|---|---|---|---|---|---|
| [`AER-Skills/`](AER-Skills/) | [brycewang-stanford/AER-Skills](https://github.com/brycewang-stanford/AER-Skills) | `85eae99fe5935c79c209f597a56c88899082a090` | `main` | MIT | AER、AER: Insights 与 AEJ 系列的期刊写作 skill 栈 |
| [`anti-defensive-writing/`](anti-defensive-writing/) | [Kiterlin/anti-defensive-writing](https://github.com/Kiterlin/anti-defensive-writing) | `1b92530b55217dc60db0e00cffd0c707e82f4886` | `main` | MIT | 减少过度防御、犹豫和无效限定的写作规则 |
| [`econ-writing-skill/`](econ-writing-skill/) | [hanlulong/econ-writing-skill](https://github.com/hanlulong/econ-writing-skill) | `f2bf7a22c5e3b37921a5e6c73bd1fb380a5e00e8` | `main` | MIT | 经济学论文写作辅助的规则与提示组织 |
| [`nature-skills/`](nature-skills/) | [Yuan1z0825/nature-skills](https://github.com/Yuan1z0825/nature-skills) | `b1a37a2bf881feb6d71e2587c70f0e4e70b72548` | `main` | Apache-2.0 | Nature 相关科研写作与研究流程 skill 集合 |
| [`NaturePanelForge/`](NaturePanelForge/) | [littlepeachs/NaturePanelForge](https://github.com/littlepeachs/NaturePanelForge) | `0ca0c91267b9e8260b959bfa4be659030dd9a5b7` | `main` | MIT | 图表面板复现、agent review loop、artifact 与多维评价线索 |
| [`revise-paper/`](revise-paper/) | [CISLab-HKUST/revise-paper](https://github.com/CISLab-HKUST/revise-paper) | `22e5a235f132ef64749b1a200ab4c3a54ad0ec78` | `main` | CC BY-NC-SA 4.0 | 论文结构、语言、图表和参考文献审查及修订报告 |

表中用途是对来源内容的静态导航，不是效果排名，也不代表已经完成实测或验证。相关理解笔记见 [`reference_repo_comparison.md`](../notes/pipelines/reference_repo_comparison.md)、[`nature_panel_forge_pipeline.md`](../notes/pipelines/nature_panel_forge_pipeline.md) 和 [`revise_paper_pipeline.md`](../notes/pipelines/revise_paper_pipeline.md)。

## 使用规则

- 默认视为**只读**；除非任务明确要求修改或打补丁，否则不改内部文件。
- 更新快照前记录新的 commit、分支和工作区状态，并同步更新本导航与迁移清单。
- 各仓库的许可证文件随快照原样保留；使用代码或文本时遵守对应许可证。
- 外部仓库体量较大，主仓库默认忽略其内容；确需纳入时记录规模、来源和许可证。
