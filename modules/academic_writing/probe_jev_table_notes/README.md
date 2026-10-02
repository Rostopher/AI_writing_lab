# probe_jev_table_notes

用 Jev（`typesafe-ai/jev`，经 Vercel AI Gateway）做表注**逐句**功能标注的可行性验证。
对照 `run_table_notes.py` 的 DeepSeek 表级标注（roles 为整注多选，无逐句粒度）。

## 设计（2026-09-20 验证通过）

每张表一次（或两次）调用：

```
state = caption + body_head（前 30 cell）+ footnote

调用 1（问题数 = 1 + 2×句数）：
  table_type: Choice 10 类（summary_stats / main_results / robustness / heterogeneity /
             mechanism / balance_test / first_stage_iv / structural_model /
             data_description / other）
  s{i}_func:  Choice，每句主功能单选（11 roles + other + none）
  s{i}_multi: boolean，该句是否同时承担多个功能

调用 2（仅 multi≥0.5 的句）：补问其余 11 个功能的布尔
```

12 个功能标签与 `run_table_notes.py` 的 ROLES 一致（措辞对齐）。

设计演进：最初每句 × 12 功能布尔（笛卡尔积），29 句长注 → 349 个问题直接 503；
改成"单选 + multi 补标"后 29 句长注只需 65 + 40 个问题，跑通且质量好。

## 文件

| 文件 | 用途 |
|---|---|
| `sentence_split.ts` | 表注拆句（保护缩写/小数/编号列表）；用 DS `n_sentences` 交叉验证：57.7% 完全一致，75% 在 ±1 |
| `test_split.ts` | 拆句器验证（对照 run_v03_full） |
| `test_jev_table_notes.ts` | 3 张真实表的可行性测试 |
| `test_long_note.ts` | 29 句极限长注测试（qje_2026_qjag002 表 6） |

## 验证结果

- 短表（2-4 句）：逐句标签与 DS 表级 roles 吻合；multi 标记能正确捕到多功能句
  （如 "For each treatment..., the table reports..." multi=0.74 → 二次补出 var_def 0.86）
- 29 句长注（qje_2026_qjag002 表 6）：表类型 main_results=1.00；32 句逐句标签目测全对；
  OCR LaTeX 星号碎片（`^{*}p<.10`）也被正确识别为 sig_marker
- 表类型判定准确且置信度高（summary_stats 0.94-0.98、main_results 0.68-1.00）

## 数据版本注意

- 表单元用 **`table_units_v3.jsonl`**（最新，含游离注回收）；`table_units.jsonl` 是最初版。
- DeepSeek 标注 `run_v03_full` 是对着 v3 跑的；与旧 units 混用会出现脚注错位。
- 只标 `note_verdict=ok` 的表（v3 中 4052 张有注且 ok）。

## 环境

与 `modules/academic_research/probe_jev_classification/` 相同：`JEV_API_KEY`、模型硬编码。
Jev 上游吞吐上限约 17/min（并发 5 与 15 相同），全量跑并发设 5 即可。
