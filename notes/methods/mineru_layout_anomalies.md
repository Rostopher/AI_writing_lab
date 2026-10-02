# MinerU 版面抽取异常目录（top_journal_ocr 数据）

> 记录日期：2026-09-20。主题：消费 playwright_crawler `top_journal_ocr`（MinerU layout.json）
> 时已证实的异常模式、量化规模、修复方法与重开条件。
> 触发背景：表注研究（modules/academic_writing）发现"40% 表无注"，逐层排查后证明
> 大部分是抽取假象。本文是该问题的详细 owner；STATUS/PROGRESS/MAP 只留指针。

## 一句话结论

**MinerU 的版面失败模式随期刊版式不同而不同，任何布局层结论必须逐期刊验证，并以
PDF 渲染目检为地面真值。** 我们曾因只验证一篇 AER（恰好是最干净的期刊）就外推全库，
得出"40% 表无注是真实分布"的错误结论；PDF 目检 7/7 张"无注表"全部有注。

## 四类结构性异常（按影响排序）

### B. 表注脱离 table 块，被标成独立顶层 text 块（影响最大，v3 已修）

注与表之间有视觉空隙时，MinerU 不把注圈进表格区域，注成为 table 块之后的兄弟 text 块。
- 证据：aer_2021_aer20160999 p14 块序列 `[table, table, text("Notes: Distance…"), text(正文)]`
- 规模：v2 无注表的 41%（726/1773）紧随其后有注样式 text 块；AER 74%、ECMA 74%、
  REStud 48%、JPE 37%、QJE 19%（由 probe_detached_notes.py 统计，脚本已退役）
- 修复：无注表向后看同页 2 块 + 下页首块，`^(Notes?[:.—]|…)` 前缀 + 同页间距 ≤80pt
  的 text 块并入，消费标记防重复归属
- 修复后精度：LLM note_verdict 审计 **99.0% ok**（684 张）

### A. 表注被误标为 table_caption，跟在 table_body 后面（v2 已修）

异常序列 `caption → body → caption`。JPE 的 `Note.—` 小字号紧跟表下，与标题块形态相似。
- 规模（75 篇分层样本）：QJE 26 例、REStud 19 例、JPE 16 例、AER 仅 4 例；
  body 后 caption 含注特征词比例 ECMA 100%、JPE 58%、QJE 51%、REStud 45%
- 修复：最后一个 body 之后的 caption 改判 footnote；以 TABLE/FIGURE/PANEL 开头的
  （混入的下一浮动体标题）丢弃
- 注意：此规则的回收质量明显低于模式 B——note_verdict 审计只有 **67.1% ok**
  （uncertain 22.9%、not_note 9.2%），主要原因是回收文本本身 OCR 乱码重，
  模型读不懂。157 张存疑表（占全部 3%）分析时应剔除 not_note

### C. 跨页/横排续表被拆成多个碎片（v3 已修，乱码容错）

QJE 爱用整页横排表；续表 caption "TABLE II CONTINUED" 被 OCR 拆成乱码
（`ABLE I ONTINUE`），注只落在末页碎片。第一轮按关键词搜 "continued" 只命中 12 条，
严重低估——**乱码使关键词排查失效**是反复出现的坑。
- 修复：清洗后 caption 含 `ONTINU` 的跨页碎片并入前一张逻辑表

### D. 同页 panel 被拆成多个 table 块（v3 已修）

一张表的 Panel A/B 拆成两个 table 块，后者无 caption（幻影表，占空 caption 的大头），
还会"抢走"本该属于整表的游离注。
- 修复：同页相邻、后者无 caption 的表块合并。全库表数 5362 → 5143（消掉 219 个碎片）

## 文本层异常（未修，只能容忍）

JPE/QJE 小字号文本被拆成 sub/sup 碎片、吞字母、丢空格："Note" → `<sub>vation</sub>`。
无注表 caption 带乱码比例：AER 0%、JPE 44%、QJE 53%。
- 危害：关键词搜索/匹配全部失效（搜 "Note" 找不到注）；对 LLM 标注影响有限
  （模型读乱码能力强于关键词匹配）
- MinerU 输出里文本已碎，抽取侧无解；根治需换 OCR 或后处理

## 结构事实（改抽取前必读）

- table 子块只有 3 种：`table_caption` / `table_body` / `table_footnote`，**无 table_title**；
  JPE/ECMA/REStud 标题拆成两个 caption 块（"TABLE 2" + 实际标题）
- table 块无嵌套，全在 `para_blocks` 顶层；`table_body` 文本 100% 在 spans 的 `html` 字段
- span **无字号字段**（只有 bbox、type、score），"注是小字号"只能拿行高当代理
- 756 个 table_body 里 12 个 html 为空（OCR 彻底失败）

## 修复效果与当前状态

| 版本 | 无注率 | 说明 |
|---|---|---|
| v1（原始） | 42%（2249/5362） | "40% 无注"错误结论的来源 |
| v2（模式 A） | 33%（1773/5362） | |
| v3（A+B+C+D） | **18%**（902/5143） | AER 4%、REStud 14%、ECMA 9%、JPE 30%、QJE 31% |

剩余 902 张里 367 张 caption 带乱码、144 张无 caption，仍是抽取残渣居多；
真实无注率估计 10% 上下，"顶刊正文表几乎都有注"基本成立。

## 产物与可恢复路径

- 抽取：`modules/academic_writing/extract_table_units.py`（v3 规则，2026-09-20）
- probe（结论已固化进 v3，脚本随 2026-10 整理退役）：`probe_layout_table_structure.py`
  （结构普查）、`probe_detached_notes.py`（游离注量化）、`probe_empty_notes.py`（无注表构成）——
  数字见上文各异常条目；git 历史中可检回脚本本体
- PDF 目检截图：`modules/academic_writing/outputs/table_notes/pdf_check/`（7 张）
- 数据：`table_units.jsonl`(v1) / `table_units_v2.jsonl` / `table_units_v3.jsonl`；
  标注 `run_v03_full/annotations.jsonl`（731/732 篇，jpe_2023_723636 顽固失败，
  caption 乱码重，模型两次漏一张表）
- LLM 审计字段：`note_verdict`（ok/wrong_table/not_note/uncertain），随 v0.3 prompt
  在同一次标注调用中返回（DEC-008）

## 局限与重开条件

- after_body_caption 回收的 157 张存疑表未逐张复核（uncertain 多为乱码所致）
- JPE/QJE 残余约 30% 无注中，可能还有注被 OCR 吞得连前缀都不剩的情况；
  可补一轮"几何位置候选（无前缀）+ LLM 判定"
- `body_head` 只存前 30 个 cell，基于它的星号检测不可靠（"无注表带星号 41%"有水分）
- 重开方向（用户指定，2026-09-20）：**OCR 质量研究**——如何更好地 verify OCR 结果
  （规则回收 + LLM 审计的混合范式已在此验证有效）、如何更好地 OCR（MinerU 替代/
  后处理/小字号增强）。若换 OCR 后端，本文四类异常需重新普查
