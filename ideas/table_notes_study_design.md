# 表注（Table Notes / Footnotes）写作惯例研究 — Design

> 状态：proposal / 未启动。给接手 agent 的自包含说明：目标、数据、方法、待决问题。
> 关联：写作惯例观察 → `modules/academic_writing/`（属「期刊案例分析」，归 academic_writing 输出侧）。

## 研究问题

经济学 top5 实证论文里，**表注怎么写**。三个子问题：

1. **写多长**：表注句数 / 字符长度的分布；跟表类型（变量定义表 vs 回归结果表 vs robustness）的关系。
2. **写什么**：表注里每句话承担什么职责（见下方 roles 清单）。
3. **表间怎么呼应**：一篇里多个表用同一批 X/Y（不同回归）时，表注是重复写、写一次后指针引用、还是混合。

非目标：不评价「哪种写法更好」，先建立**观察到的惯例分布**（区分观察 ≠ 因果，见 AGENTS.md / DEC-004）。

## 背景动机

作者写实证论文时的真实纠结：表注该写多详细？太简略被导师说「读者看不懂」，太详细被说「太长」。本研究要弄清顶刊表注实际包含**哪些职责**、详略的**分寸**在哪——即什么信息该进表注、什么该留正文/附录、跨表复用时怎么省力——供作者自己写稿定详略，并可复用进写作 skill。

（附带观察：导师强调 (a) 表/图注 sentence case；(b) 已定义变量标签大写并全篇统一。本研究顺带记录 capitalization 实际形态，但非核心目标。）

## 已有证据（本 repo 已做的观察）

- `top_journal_ocr` 的 MinerU `layout.json` 把每页分块，table block 内含 `table_caption`（表标题）、`table_body`（整段 `<table>` HTML）、`table_footnote`（表注）、`ref_text`（参考文献）。表注可**结构化抽取**，不靠正则猜位置。
- 抽样观察到 top5 表注职责高度固定：标准误/星号、变量定义（"X refers to"）、数据来源（"from X" / "See Data Appendix"）、估计方法、列/panel 导航、跨表指针（"See note to Table X"）。
- 实证刊（AER）特有：`table_purpose`（"The table presents OLS coefficients..."）、`identification`（IV/DID/RDD 识别策略）、`clustered SE`、多重假设校正（FDR/Romano-Wolf）。
- 跨表复用三种策略都已见到：指针（QJE `See note to Table VI`）、逐表重复核心句（REStud bootstrap 句）、混合（指针+补本表特有）。

## 数据

- **OCR 语料**：`F:/codeF/llm_projects/playwright_crawler/top_journal_ocr/`（详见 `playwright_crawler/memory-docs/DATA_DIRS.md`）。**不递归扫目录**；经 `crosswalk.jsonl` 按 `paper_id`/`doi`/`journal`/`year` 定位单篇 `layout.json`。
- **实证筛选**：复用 `abstract_structure` 全量标注 `data/processed/abstract_structure/run_20260909_v03_full/annotation_flash/annotations.jsonl` 的 `output.paper_type.primary_type`。`article_id` 形如 `AER:10.1257/aer.xxx`（期刊:DOI），与 crosswalk 的 `doi` 字段 join。
- **样本框**：top5（QJE/AER/JPE/ECMA/REStud）× 2021–2026 × `primary_type == "empirical"` ≈ **748 篇**（已 join 验证：empirical 标注 1471，对到 2021–26 crosswalk 748，109 篇 DOI 形式不一致未匹配）。

## 方法

### 第 1 步：抽取表单元（纯 Python，不走模型）

脚本 `modules/academic_writing/extract_table_units.py`：

- 遍历样本框 748 篇 → 读每篇 `layout.json` → 抽每个 `table` block 的 `{序号, table_caption, table_body(行标签/列头), table_footnote}`。
- `table_body` 是整段 `<table>` HTML：解析出表头行与前若干行的文本作为「表格主体」进 prompt（含行标签/列头，让模型能对照注与表内变量）。超长表截断（如最多 ~30 个非空 cell）。
- 同时记录**无 table_footnote 的论文**（「不写注」本身是发现）。
- 输出 `outputs/table_notes/table_units.jsonl`：每行一篇 `{paper_id, journal, year, doi, n_tables, tables:[{idx,caption,body_head,footnote}], has_any_note}`。

### 第 2 步：LLM 标注（deepseek-v4-flash）

- 复用 `modules/academic_research/abstract_structure/llm_client.py` 的 `DeepSeekClient`（flash/pro、预算护栏、缓存、重试、`response_format=json`）。模型 `deepseek-v4-flash`，temperature 0。
- **每篇论文一次调用**，输入该篇全部表的 `{序号, caption, body_head(行标签/列头), footnote}`（不给正文），输出 JSON：
  - 每张表注：`n_sentences`、`roles[]`、`cross_ref`(bool+指向)、`abbrev_expand`(bool)
  - 整篇：`note_strategy` ∈ `repeat`/`pointer`/`mixed`/`none`
- **roles 清单**（一句话可兼多职责）：
  `sig_marker` 标准误/星号/聚类层级；`table_purpose` 这表在估计什么；`identification` 识别策略(IV/DID/RDD/RCT)；`var_def` 变量/缩写定义或构造；`data_source` 数据来源/wave/样本期；`method` 估计方法细节；`sample` 样本构成/限制；`col_nav` 列或 panel 导航；`multiple_test` 多重假设校正；`cross_ref` 指向其他表注；`abbrev_expand` 缩写是否展开全称；`other`。

### 第 3 步：汇总分析（Python）

- 三个子问题各自的交叉表：长度分布（按表类型）、roles 频次与共现、note_strategy 分布；按期刊×年份分层。
- **详略分寸**（核心动机）：哪些 roles 高频出现（≈必备：如 sig_marker、data_source、var_def）、哪些低频（可选）；长注 vs 短注差的主要是哪几类职责——回答「什么必须写、什么可以省」。

## 成本估算

748 篇 × ~5k token 输入（含 body_head）+ ~0.5k 输出 → 输入 ~3.7M、输出 ~0.4M。flash 价（输入 ¥1/M、输出 ¥2/M）≈ **¥5–8**，谷期更低。**先 pilot ~50 篇**看标注质量再上量。

## 待决问题（接手前跟作者确认）

1. ~~pilot 规模~~（已定 50）与是否上 748 全量。
2. ~~`table_body` 行标签要不要进 prompt~~（已定：进，截断防超长）。
3. ~~`structural`/`mixed_or_structural` 算不算实证~~（已定：不算，只取 `primary_type == "empirical"`）。
4. roles 清单是否要加「稳健性说明」「假设限定」等类目（pilot 暂未出现，先不动）。
5. ~~`table_body` 截断策略~~（已定 ~30 非空 cell）。

## Pilot 观察（2026-09-20，50 篇 AER，run_20260920_103149）

> 注意：pilot 按 article_id 排序取前 50，全是 AER 单刊，不代表 top5。

- 成本：50 篇 ¥0.96（flash），零失败。
- 表注长度：中位 4 句、均值 4.2、p90 9。
- roles 高频必备（按表计）：var_def(205) > table_purpose(177) > sig_marker(171) > method(144) > sample(138) > col_nav(134)；中频 identification(89)/data_source(65)；低频 abbrev_expand(26)/multiple_test(2)。
- note_strategy：repeat 30 / mixed 10 / pointer 1 / none 9——重复为主、指针点缀。

## 失败条件 / 风险

- 若 `table_footnote` 标注漏抓率高（注在表题下方或跨页续表没被 MinerU 标成 footnote），样本会低估「写注」的论文——需抽几篇核对 layout 标注完整性，必要时改从 `full.md` 正则兜底。
- LLM 对「roles」判定若不稳定（同一句话归类漂移），先在 pilot 上人工复核 ~30 条再决定是否加校验或收紧 prompt。
- 「半篇论文没注」若占比过高，「写什么」的结论只能覆盖「有注的那部分」。

## 产物去向

- 探针：`modules/academic_writing/extract_table_units.py`、`run_table_notes.py`。
- 结果：`outputs/table_notes/`。
- 结论固化：惯例分布写成 note → `notes/`（如 `notes/pipelines/table_notes_conventions.md`），可复用进 `skills/econ-abstract-writing` 式的写作检查项（先定目标期刊口径）。
