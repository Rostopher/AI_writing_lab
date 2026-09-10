# Papers

文献工作区：目标期刊的论文 PDF、元数据与全文文本，用于学术方向的期刊案例分析与写作研究。

## 来源

- 由姊妹仓库 `playwright_crawler` 采集的期刊数据
- 经 `paper-workspace` 物化为可 rg 搜索的论文工作区（full.md、metadata、layout 等）

## 约定

- `papers/*/full.md`、metadata、layout JSON 属于**自动生成产物**：不手改，
  除非任务明确是元数据/OCR 修正。
- 每篇论文的阅读笔记 → `notes/paper-reading/`（不要放在这里）。
- 不要在这里放与期刊文献无关的写作笔记或项目决策。

## 规则

本目录默认不提交大规模全文数据；是否版本化由数据规模与来源决定
（参见 `memory-docs/CONVENTIONS.md`）。
