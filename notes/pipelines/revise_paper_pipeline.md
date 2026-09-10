# revise-paper Pipeline

## What It Is

`revise-paper` 是一个 Codex skill，不是可执行 benchmark 或带模型调用的应用。仓库快照只有 `README.md` 和 `SKILL.md`；真正的方法全部写在 skill 指令中。

## Main Pipeline

```text
完整 LaTeX/Overleaf 项目
  -> 识别 main tex、sections、bib、figures、build config、PDF
  -> 编译 baseline 并逐页检查 PDF
  -> reverse outline 与 section/paragraph 审查
  -> writing / figures / equations / references / layout 审查
  -> 修改源码并重新编译
  -> source-located revision report
```

它定义两套 authority：LaTeX source 是可编辑权威，compiled PDF 是视觉权威。这个区分避免只看抽取文本而漏掉布局、图表、引用和匿名化问题。

## Judgment Boundary

输出被分成三类：

- Automatic changes：明确 typo、grammar、format 等低判断风险修改。
- Suggested changes：结构重写、术语选择和不清楚技术表达，只给建议。
- Comments：unsupported claim、motivation、validation、contribution 等高学术判断问题，不自动改写。

最重要的可迁移原则是“权限随学术判断风险上升而收缩”，而不是具体 APA 或 LaTeX 规则。

## Artifacts

- 修改后的可编译 LaTeX 项目。
- baseline/rebuilt PDF 与 build log（协议要求，但仓库本身不提供执行器）。
- 按自动修改、建议、评论分类且精确定位源码的报告。

## Evaluation Gap

- 没有数据集、gold revision、runner、metric、inter-rater agreement 或实验结果。
- reverse outline、introduction quality 和 overclaim 检查是规范性指令，没有操作化评分定义。
- 没有证明 automatic/suggested/comment 分类在不同评审者之间一致。

## How To Migrate

- 保留完整项目上下文和 source/rendered 双 authority。
- 将 automatic/suggested/comment 推广为按风险分级的 edit authority。
- 把每条 finding 结构化为 location、level、issue_type、evidence、risk、action 和 confidence。
- 为高层写作问题另建 benchmark，不能把 skill 清单本身当 evaluation。

## Evidence

- `repos/revise-paper/README.md`
- `repos/revise-paper/SKILL.md`
- 快照：`22e5a235f132ef64749b1a200ab4c3a54ad0ec78`
