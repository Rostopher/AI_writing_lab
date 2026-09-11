# 经济学英文摘要写作 · Econ Abstract Writing

简体中文 | [English](README.en.md)

**摘要最后写。先有结果，形成完整的论文故事，写好 Introduction，再用五个问题把论文提炼成摘要。**

这是 [AI Writing Lab](../../README.md) 的英文经济学摘要写作 skill，适合三种情况：

- 主要结果和 Introduction 已完成，准备从零写摘要；
- 全文 draft 基本完成，希望从论文中提炼摘要；
- 已有摘要，希望检查结构、内容取舍并修改英文表达。

## 五个问题，组织一段摘要

| 部分 | 先回答的问题 |
|---|---|
| **W — What** | 这篇论文最核心的研究问题是什么？ |
| **H — How** | 回答这个问题最重要的方法是什么？ |
| **F1 — Findings** | 对研究问题最直接、最重要的回答是什么？ |
| **F2 — Findings** | 为什么会出现这个结果？有什么机制证据？ |
| **F3 — Findings** | 还有哪个发现最值得记住：差异、对照、代价、长期影响或经济后果？ |

你可以先用中文回答。AI 会帮助检查内容之间的联系，再按 **WHFFF** 组织英文。
没有机制结果时，F2 可以使用另一条关键发现；问题与方法也可以合写。
重点是每条发现都有信息，并且来自你的论文。

如果还只有零散结果，skill 会先帮助整理故事和需要补齐的内容，等 Introduction 形成后再写正式摘要。
如果已经提供全文，AI 可以先提炼五个答案，供你核对；已有摘要则可以直接开始检查。

## 一个 skill，两种阅读语言

中英文用户都安装、调用 **`econ-abstract-writing`**。AI 跟随你的语言交流，摘要默认用英文。

[SKILL.md](SKILL.md) 是唯一的英文执行入口，[SKILL.zh.md](SKILL.zh.md) 是中文阅读译本。
使用说明和参考材料都有中英文版本，可通过各页的语言链接切换。
安装时保留整个文件夹，无需选择单独的 `-zh` 或 `-en` skill。

## 使用

### 在 Codex 中安装

可以把下面这句话发给带有 `skill-installer` 的 Codex：

```text
请使用 $skill-installer，从 https://github.com/Rostopher/AI_writing_lab 安装
skills/econ-abstract-writing 这个 skill。
```

也可以下载本仓库，将整个 `econ-abstract-writing` 文件夹复制到自己论文项目的
`.agents/skills/`，形成 `.agents/skills/econ-abstract-writing/SKILL.md`。
保留文件夹里的 `references/` 和 `agents/`。Codex 的加载位置与安装方式见
[官方 skills 文档](https://learn.chatgpt.com/docs/build-skills)。

仓库中的 `skills/` 是公开维护的源码位置；下载整个仓库后，可按以上方式安装，
也可直接让 AI 阅读本目录的 `SKILL.md`。这个 skill 无需 API key、额外脚本或论文数据库。

### 三种开始方式

**还没有摘要：**

```text
请使用 $econ-abstract-writing。我的主要结果和 Introduction 已完成，
请先引导我回答五个问题，再帮我写英文摘要。下面是 Introduction 和结果：……
```

**已有全文：**

```text
请使用 $econ-abstract-writing，根据这份完整 draft 提炼五个问题的答案，
让我核对核心问题和三个发现后再写英文摘要。目标字数是……
```

**检查已有摘要：**

```text
请使用 $econ-abstract-writing 检查下面的摘要。
请看核心问题是否清楚、方法是否到位、三个发现是否各有信息，先给修改建议。
摘要：……
```

也可以把五个答案和材料一次性给出，请 AI 直接起草；需要直接改稿时明确说“请检查并修改”。
若使用不支持安装 skills 的对话工具，可将 [SKILL.md](SKILL.md) 和需要的参考文件提供给它，
让它按说明工作；这属于在对话中提供方法，不会自动安装 skill。

## 文件与依据

- [SKILL.md](SKILL.md)：供 AI 执行的完整方法；[中文阅读译本](SKILL.zh.md)。
- [结构选择](references/zh/abstract_patterns.md)：WHFFF 的内容分工与变体。
- [教学示例](references/zh/examples.md)：自拟研究材料、五个答案、英文摘要与改稿示范。
- [语料证据与方法来源](references/zh/corpus_evidence.md)：4250 篇摘要的关键观察及其适用范围。

语料来自 AER、JPE、Econometrica、REStud、QJE 在 2015—2026 年间的已有覆盖，
2026 年为部分年份。统计用于帮助组织写作；“摘要最后写”和五个问题是本项目采用的作者工作流程。
第一版的实际改稿效果仍需要通过使用案例比较。欢迎反馈具体材料、修改前后文本及仍未解决的问题。

维护时先修改英文执行入口和参考材料，再在同一轮改动中同步中文译文。
实际执行写作任务时不需要重复加载两种语言的内容。
