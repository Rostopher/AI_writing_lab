# 摘要结构研究全量描述报告（run_20260909_v03_full）

日期：2026-09-09。执行依据：`ideas/abstract_structure_study_design.md`（v0.3）。
标注 prompt：`ideas/abstract_structure_annotation_prompt.md` **v0.3**
（sha256 `ba3e8e60…c0987c`，与 v0.3 独立验证集同一文件）。
本报告对应设计 §9.D「扩展决定」之后的**全量已有语料描述**；规则审查
（设计 §7 / H5）**仍未运行**，相关结论标注「未检查」。

与 pilot 报告（`abstract_structure_pilot_report.md`，v0.2 prompt、100 篇等权
样本）的关系：本报告用 v0.3 prompt、全量语料，是描述主结果；pilot 报告中的
双模型一致性与 agent 核验结论仍有效，但 v0.2→v0.3 改了 how_aspects
（禁 mechanism）与 Why 口径，数值不可直接跨版本比较。

## 1. 样本与运行概况

- 语料：五刊（AER/ECMA/JPE/QJE/REStud）2015–2026 已发表文章，全量合规样本
  **4250 篇**（`full_sample_manifest.jsonl`）。这是语料全量描述，不是抽样
  推断——不需要抽样误差，但外推限于实际覆盖（缺失来源见 §7）。
- 模型：deepseek-v4-flash 单模型（temperature=0，max_tokens=32768，
  response_format=json_object）。pro 全量未跑（费用决策待定）。
- 完成情况：4250/4250 成功，其中 4192 篇首轮通过、58 篇修复通过、0 失败。
  总费用 **¥96.08**。运行窗口 2026-09-09 12:35–19:55（含 1 篇补跑）。
- 产物：`annotation_flash/annotations.jsonl`、`v03_full_derived_deepseek-v4-flash.json`
  （设计 §10.1–§10.9 派生指标）、`run_manifest.json`、
  `compare_full_vs_validation.json`（与 v0.3 验证集的一致性核对）。

## 2. 长度：期刊差异远大于年份趋势

总体（n=4250）：median 106 词，mean 124.4，p25=99，p75=146，p95=203.5。
分布：≤100 词 36.6%，101–150 词 41.9%，>150 词 21.5%。

| 期刊 | n | median | >150 词占比 |
|---|---|---|---|
| AER | 1262 | 100.0 | 2.9% |
| JPE | 798 | 100.0 | 0.4% |
| ECMA | 743 | 136.0 | 30.3% |
| REStud | 910 | 140.5 | 36.3% |
| QJE | 537 | 160.0 | 59.4% |

- **AER/JPE 中位数钉在 100 词**（与 AER 100 词上限一致），QJE 近六成超过
  150 词。pilot 在小样本上看到的期刊差异在全量上完全复现且更极端。
- **年份上几乎无趋势**：2015–2026 各年中位数在 103–113 之间波动，均值
  121–127。「摘要越来越长」在本语料窗口内不成立（2026 为 partial year）。
- 按 paper_type：methods 中位 122 > mixed 111 > empirical 104 ≈ theory 103。

## 3. 功能覆盖：核心三功能约 2/3 齐备，Why 仅 1/4

口径：narrow = 句子主标签；inclusive = 含次要标签；core3 = what/how/findings
齐备。

| 指标 | 全量（4250） |
|---|---|
| what present（narrow / inclusive） | 76.7% / 99.6% |
| how present | 87.6% |
| findings present | 98.2% |
| why_it_matters present | 25.5% |
| core3 覆盖（narrow 下界 / inclusive 下界） | **66.9%** / 85.9% |
| 四功能齐备（narrow / inclusive） | 16.0% / 21.1% |

按期刊的 narrow core3：QJE 75.6% > REStud 70.8% > ECMA 65.8% > AER 63.7% >
JPE 62.7%——长摘要期刊覆盖更全，与长度差异同向。

按 paper_type 的 narrow core3：empirical 73.8%、mixed_or_structural 74.4%、
methods 65.4%、**theory 55.0%**；how present 在 theory 仅 78.2%（empirical
90.5%、mixed 98.5%）。**理论论文摘要更常省略明确的方法句**。paper_type 为
unclear 的 53 篇 core3 仅 13.2%——类型判定不确定的文章语义指标也弱，
解释时应对照。

## 4. 句数与顺序：公式不成立，首现顺序有倾向

- **句数联合规则**（What 1–2 句 ∧ How 1 句 ∧ Findings 1–2 句）：总体仅
  417/4250（9.8%），在 core3 齐备子集中也只有 417/2843（14.7%）。
  pilot 结论在全量上确认：**句数公式作为描述不成立**，主因是功能同句交织。
- 句数分布（触句数主峰）：what 1–2 句；how 1–2 句（1 句 1504 篇、
  2 句 1338 篇）；findings 2–4 句（合计 3023 篇）；why 0–1 句。
- **块顺序**（core3 各自成块且按 what→how→findings 排列）：445/2843
  （15.7%）成立。强形式与实际摘要不符。
- **首现位置**（更贴近实际的弱形式）：
  - what 先于 findings：2958 篇 '<' vs 175 篇 '>'（narrow 口径，下同）；
  - how 先于 findings：2545 '<' vs 587 '>'；
  - what 与 how 的先后接近对半偏 what 先：1569 '<'、1120 '='（同句）、
    212 '>'。
- Why 首现在 findings 之后（all4 子集 679 篇中 634 篇）。

**观察**：稳定成立的是「What/How 大致先于 Findings」的首现倾向；任何
「固定句数配比、功能分块」的强规则都与多数摘要相悖。写作建议只能引用
弱形式。

## 5. 文本占比与框架外内容

- 平均文本占比：findings **49.4%**、how 21.4%、what 12.5%、
  why_it_matters 4.0%；核心三功能并集 85.8%；框架外 10.1%。
  **摘要的一半篇幅在给结论**——这是最稳定的全量事实之一。
- 框架外内容：46.2% 的文章至少一句（3113 句）。描述词频头部为
  background / motivating / motivation / statement / context / literature /
  prior——以**背景与动机铺垫**为主，与 pilot 的归类一致。按设计口径，
  框架外单独记录、不作负面评价。
- 含 uncertain 片段的文章 74 篇（1.7%），按口径不计作确定新功能。

## 6. 与 v0.3 验证集的一致性（全量结果可用性证据）

详见 `compare_full_vs_validation.json`。要点：

- 大多数指标（what/findings/why presence、覆盖、占比、框架外）与 100 篇
  验证集差 1–4pp，一致。
- how presence 验证集 95% vs 全量 87.6%（约 7pp）。逐项排除期刊构成、
  年份构成、dev/pilot 排除规则后，决定性证据是**同文复现性**：同一批
  100 篇文章两次运行 how 标签仅 3 篇翻转（双向），任意功能标签差异
  15 篇。差异主要由 100 篇抽样波动解释（z≈2.2）。
- 结论：无系统性标注漂移，全量派生指标可用于描述性分析。
- 同时量化了 temperature=0 下的标签级非确定性：单功能标签约 3% 会翻转，
  涉及功能边界的结论不应建立在个位数篇数上。

## 7. 句数分布：中位 5 句，4–6 句占 65.5%

（2026-09-09 追加；产物 `v03_full_positional_deepseek-v4-flash.json`，脚本
`modules/academic_research/abstract_structure/analyze_sentence_positions.py`，
直接基于 `annotation_flash/annotations.jsonl` 派生，未新增模型调用。
句子的功能按标注的 label 集合处理——prompt 规定 functions 无序、不强制单一
主功能——故位置矩阵报告「到达该位置的句子中标签集合含该功能」的比例。）

总体（n=4250）：mean=5.78 句，median=5，p25=5，p75=7，p95=9（范围 1–19）。
分布：**4 句 19.0%、5 句 26.1%、6 句 20.4%，合计 65.5%**；3 句 5.1%，
7 句 13.3%，8 句及以上约 8%。

| 期刊 | n | median | mean | 主峰 |
|---|---|---|---|---|
| JPE | 798 | 5 | 4.89 | 5句 37%、4句 28% |
| AER | 1262 | 5 | 5.12 | 5句 32%、4句 26% |
| ECMA | 743 | 6 | 6.21 | 6句 22%、5句 22% |
| REStud | 910 | 6 | 6.29 | 6句 23%、7句 18% |
| QJE | 537 | 7 | 7.21 | 7句 20%、6句 20%、8句 15% |

**观察**：句数的期刊差异与词数差异（§2）同向——JPE/AER 短（4–5 句），
QJE 长（6–8 句）。句数来自标注覆盖的句子（extract 阶段切分），与词数
口径独立。

## 8. 位置×功能：每个位置通常承担什么功能

W=what，H=how，F=findings，Y=why_it_matters；多标签句同时计入多个功能。
以最大的 5 句类（n=1111）为模板：

| 位置 | W | H | F | Y | 最常见形态 |
|---|---|---|---|---|---|
| 第1句 | 55.7 | 29.6 | 9.3 | 0.2 | 纯 W 36.8%；背景句（无功能）26.6%；W+H 同句 18.5% |
| 第2句 | 18.4 | 45.5 | 39.2 | 0.4 | F 28.9% / H 27.0% 对半 |
| 第3句 | 8.3 | 33.3 | 68.9 | 1.6 | 纯 F 56.2% |
| 第4句 | 5.6 | 21.9 | 80.9 | 5.4 | 纯 F 67.6% |
| 第5句 | 5.6 | 16.4 | 69.9 | 19.4 | 纯 F 52.9%；纯 Y 13.7% |

4 句（n=806）与 6 句（n=867）类模式同构，findings 段相应压缩/膨胀一句
（条件矩阵见派生 JSON）。无条件全量矩阵（所有文章按绝对位置）呈现同样
梯度：第 1 句 W 主导，第 2 句 H/F 对半，第 3 句起 F 稳定在 60–76%，
Y 随位置后移单调上升至末句约 20%。

**首句**（全量）：53.8% 含 what（其中约 1/3 与 how 同句，"We use X to
study Y" 式）；28.0% 为无功能标签的**背景/动机开局**——QJE 最偏爱背景
开局（33.0% 首句为背景），AER/JPE/ECMA/REStud 首句以纯 what 居多。
**末句**（全量）：70.0% 含 findings、19.9% 含 why；纯 F 53.4%、
纯 Y 13.9%、F+Y 5.2%。Why 若出现基本在末句，QJE 末句纯 Y 比例最高
（20.7%）。

**写作含义**：主流模板（约 2/3 已发表摘要，4–6 句）是——
① 第一句给研究内容陈述（或背景动机句开局，期刊间有差异）；
② 第二句给方法或直接进结论；③ 中间 1–3 句为 findings 主场；
④ 末句以 findings 收尾或一句 why 升华。但完整功能序列是**长尾**的：
5 句摘要中最高频的完整模式 `W H F F F` 也仅 3.6%；功能同句交织
（多标签句 12–20%）是常态。稳定成立的是「位置×功能的概率倾向」，
不是任何固定公式——写作建议的合理形式是逐位置倾向 + 期刊口径，
而非「第 N 句必须写什么」。

## 9. 局限

1. **单模型单 run**：全量只有 flash；pro 全量未跑，无法在全量尺度上做
   双模型系统误读检查（validation 尺度上 pro 修复率更低：0/100 vs 1/100）。
2. 标签级非确定性约 3%（how），15 篇同文不一致案例未人工复核。
3. 语料缺口（台账已标注）：ECMA 92 篇 Wiley ajax 页无摘要；JPE 202 篇
   期级字段回退；QJE/REStud 373 篇 paragraphs[0] 回退；2026 partial year。
   全量描述限于实际覆盖，不代表五刊全部已发表文章。
4. 规则审查（§10.10 规则矩阵）未运行：套话、术语、识别策略说明等
   **未检查**。
5. 一切结论是对已发表摘要的**观察**，不构成「这样写导致发表」的因果
   证据；也不构成「不写 Why 就不好」的评价——Why 缺失可能只是期刊风格。

## 10. 下一步建议

- 15 篇同文标签不一致案例人工复核，补齐全量可靠性证据。
- 规则审查小样本（设计 §7，约 ¥6 量级）作为第二阶段独立一轮。
- 是否跑全量 pro（约 ¥150–200）取决于后续是否要在全量尺度上做双模型
  证据；validation 证据下 flash 已够用。
- 若要把「Why 仅 25%」「理论论文常省 how」做成写作检查项，需先决定
  目标期刊口径——按本刊风格对齐，而非套全刊平均。

## 附：产物索引

`data/processed/abstract_structure/run_20260909_v03_full/`：
`run_manifest.json`、`full_sample_manifest.jsonl`、
`annotation_flash/annotations.jsonl`（4250 条）、
`annotation_flash/failures.jsonl`（1 条已补跑成功的历史记录）、
`annotation_flash/requests|responses/`（调用缓存）、
`v03_full_derived_deepseek-v4-flash.json`、`compare_full_vs_validation.json`、
`v03_full_positional_deepseek-v4-flash.json`（句数分布与位置×功能，§7–§8）。
验证集：`run_20260909_v03_validation/`（100 篇 × 双模型 + 派生 + 双模型
比较）。
