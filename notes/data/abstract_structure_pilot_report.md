# 摘要结构研究 pilot 报告（run_20260908_a）

日期：2026-09-08。执行依据：`ideas/abstract_structure_study_design.md`（v0.2）
与其 §12 执行说明。标注 prompt：`ideas/abstract_structure_annotation_prompt.md`
**v0.2 已冻结**（sha256 `c29f09b3…8bc5`，schema_version `abstract_structure_v0.1`）。

本报告对应设计中的「100 篇双模型 pilot」阶段。规则审查（设计 H5 /
`abstract_rules_audit_prompt.md`）**本轮未运行**，下文相关位置标注「未检查」。

## 1. 样本与运行概况

- 语料：五刊（AER/ECMA/JPE/QJE/REStud）2015–2026 已发表文章，派生台账
  5431 条、摘要可用 4334 条；2026 为 partial year。AER 2015–2017 年 5 月号
  （Papers & Proceedings 专辑）整期剔除。
- pilot 样本：100 篇，每刊等权 20 篇，分层随机 seed=20260908
  （`pilot_sample_manifest.jsonl`）。**等权样本不代表五刊全体的篇数加权分布**。
- 双模型：deepseek-v4-flash、deepseek-v4-pro（temperature=0，
  max_tokens=32768，response_format=json_object）。
- 完成情况：两模型均 100/100 成功、零失败。flash 97 篇首轮 + 3 篇修复，
  pro 99 + 1。费用：pilot flash ¥2.07、pro ¥4.07；含开发集两轮全程约 ¥7，
  远低于 ¥30 预算护栏。
- 审核子集：25 篇（pilot 内部抽样，`pilot_review_subset.jsonl`），由 agent
  按同一 prompt 独立标注（`review_agent_annotations.jsonl`），标
  **「agent 初步核验」，不是 human gold**。首轮曾误抽 pilot 外样本，已纠正，
  旧标注保留为 `review_agent_annotations_extra_outside_pilot.jsonl`。

## 2. 长度（H1：100–150 词是中心趋势而非硬上限）

100 篇词数：median 108.5，mean 125.6，p25=99，p75=140.5，p95=198.4。
分布：≤100 词 34%，101–150 词 44%，>150 词 22%。

| 期刊 | median | >150 词占比 |
|---|---|---|
| AER | 100.0 | 0/20 |
| JPE | 100.0 | 0/20 |
| ECMA | 123.0 | 4/20 |
| REStud | 128.0 | 5/20 |
| QJE | 171.5 | 13/20 |

**观察**：100–150 词确为多数期刊的中心区间，但期刊间差异极大——AER/JPE
中位数钉在 100（与 AER 现行 100 词上限一致），QJE 明显更长。把「100–150」
当作通用写作规范会抹平期刊差异。

## 3. 功能覆盖（H2）

两种口径：narrow = 句子主标签；inclusive = 含次要标签。core3 =
what/how/findings 三者齐备。

| 指标 | flash | pro |
|---|---|---|
| core3 覆盖（narrow） | 71–72/100 | 77/100 |
| core3 覆盖（inclusive） | 89/100 | 91/100 |
| why_it_matters 出现 | 35/100 | 36/100 |
| 四功能齐备（narrow / inclusive） | 26–27 / 30 | 28 / 32 |

**观察**：多数摘要覆盖核心三功能；why_it_matters 只有约 1/3 的摘要明示。
what 的 inclusive 口径达 99–100/100——几乎没有摘要完全不含研究内容陈述，
narrow 与 inclusive 的差距主要来自 what 与 findings 同句交织。

## 4. 句数公式与顺序（H3/H4）

- **句数联合规则**（What 1–2 句 ∧ How 1 句 ∧ Findings 1–2 句同时满足）：
  flash 5/100，pro 2/100；在三功能齐备的子集里也只有 5/71、2/77。
  **该公式作为描述基本不成立**，主因是功能同句交织（一句多标签普遍，
  what~how 同句约 24–27%）。
- **块顺序**（core3 各自成块且按 what→how→findings 排列）：仅 8/71
  （flash）、4/77（pro）成立。
- **首现位置**更符合直觉：what 首次出现先于 findings 的约 70–74%，
  how 先于 findings 的约 58–59%；但 what 与 how 的首现次序接近对半
  （'<' 45–47，'=' 24–27）。

**观察**：「先说什么后说什么」在首现意义上有倾向性，但「分块、按固定
句数配比」的强形式与实际摘要不符。写作建议若引用句数公式，应降格为
「功能齐备 + 大致顺序」，而非可检查的硬规则。

## 5. 框架外内容

31–33% 的文章含至少一句四功能框架外内容（flash 59 句 / pro 54 句，
两模型判定的重叠见 §6）。对 flash 的 60 句按描述归类：背景/动机 46 句，
文献/缺口 5 句，方法细节补充 3 句，机构/数据细节 1 句，其他 5 句。

**观察**：框架外内容以背景动机为主，是摘要的正常组成部分，不宜判为
「违规」；这与设计中「框架外单独记录、不作负面评价」的口径一致。

## 6. 双模型一致性与审核子集核验（H6）

**flash vs pro（100 篇）**：macro F1 = 0.876；findings 0.97、what 0.90、
why 0.81、how 0.83（pro 对 how 过标，fp=66）；paper_type 一致率 0.95；
exact label-set 仅 0.29（句子级标签集合完全相同很难，属预期）。

**agent 核验 vs 模型（25 篇）**：

| 功能 | flash P/R/F1 | pro P/R/F1 |
|---|---|---|
| what | 1.00 / 0.62 / 0.76 | 0.97 / 0.74 / 0.84 |
| how | 0.90 / 0.81 / 0.85 | 0.80 / 0.96 / 0.87 |
| findings | 0.94 / 0.93 / 0.94 | 0.95 / 0.95 / 0.95 |
| why_it_matters | 0.33 / 1.00 / 0.50 | 0.25 / 0.67 / 0.36 |

paper_type 一致率 0.88（flash）/ 0.84（pro）；macro F1 0.76（两者）。

**解读**：findings 最可靠；主要残余分歧在 ① why_it_matters——模型比
agent 更倾向于把结果句里的意义暗示标为 why（fp=6，基数小）；② how 的
标定宽度——pro 偏宽、agent 居中、flash 偏窄；③ what 与 findings 同句时
的归属。注意这些是**分歧而非错误**：agent 核验本身非 gold，why 的低精度
同时反映 prompt 边界案例的真实难度（见 §7）。

**契约可靠性**：JSON Schema 合规率 100%，quote 定位失败率 0，
空响应重试机制生效（deepseek-v4 推理模型 reasoning tokens 计入
max_tokens，4096 会被耗尽返回空 content；已固定 max_tokens=32768 +
循环内重试 + 仍空则计入 failures 的处置）。

## 7. 标注口径的边界与歧义（来自 agent 核验笔记）

25 篇审核标注的 annotator_note 显示反复出现的难点：

- **机制句的双重身份**：模型传导机制、结果解释通道常同时是 findings 与
  how[mechanism]（rdaa051、rdy060、qjac006 等多篇）。现口径允许双标，
  但两模型与 agent 对何时双标判断不一。
- **无内容的预告/宣称句**：'illustrates the usefulness'、一致性宣称、
  示例预告等，在 what / findings(secondary) / connective_only / other
  之间归属不稳定。
- **薄模型信息**：仅说 'general equilibrium model' 不足以标 how
  （rdae077），但边界主观。
- **理论 + 实证交织摘要**的 paper_type 与 component 判定摇摆
  （empirical vs mixed_or_structural）。
- 长引言型摘要（前 8 句全背景，what 到 S9 才出现，ecta13971）挑战
  「功能齐备」的检查逻辑。

## 8. 局限

1. agent 核验非 human gold，§6 的一致率应读作三方口径分歧图谱，而非
   模型准确率。
2. 等权 pilot（每刊 20）不代表五刊全体；年份趋势未检验（by_year 数据
   已在派生文件中）。
3. 已知数据缺口：ECMA 92 篇 Wiley ajax 页无静态摘要（extraction_error）；
   JPE 202 篇为期级 abstract 字段回退、QJE/REStud 373 篇为 paragraphs[0]
   回退（均在台账标注来源）；OUP 订阅样板污染 800 条已修复。
4. 规则审查（H5）未运行：具体发现是否落摘要、被动语态、术语、识别策略
   说明等**未检查**，§10.10 规则矩阵留空。
5. 本研究的一切结论是**对已发表摘要的观察**，不构成「这样写导致发表」
   的因果证据。

## 9. 下一步建议

- 若扩大样本：prompt v0.2 可直接复用；建议先就 §7 的机制双标与宣称句
  边界补 2–3 条示例进 prompt，再跑 300–500 篇。
- 规则审查（约 ¥6 量级）可作为独立一轮，与结构标注结果合成规则矩阵。
- why_it_matters 的判定若要做进写作检查工具，需要人工 gold 子集校准，
  agent 核验不足以定边界。

## 附：产物索引

`data/processed/abstract_structure/run_20260908_a/`：
`corpus_manifest.jsonl`、`run_manifest.json`（含 annotation_runs 节）、
`pilot_sample_manifest.jsonl`、`pilot_annotations_{model}.jsonl`、
`pilot_derived_{model}.json`、`compare_pilot_flash_vs_pro.json`、
`pilot_review_subset.jsonl`、`review_agent_annotations.jsonl`、
`compare_review_vs_{model}.json`、`dev_*`（开发集两轮）。
