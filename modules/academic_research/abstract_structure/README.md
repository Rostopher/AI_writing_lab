# abstract_structure — 经济学顶刊摘要结构研究：数据层与 LLM 调用层

阶段 A 工程部分：覆盖普查、摘要抽取、确定性文本处理、LLM 客户端与输出校验器。
当前设计：[设计 v0.3](../../../ideas/abstract_structure_study_design.md)、
[结构 prompt v0.3](../../../ideas/abstract_structure_annotation_prompt.md)、
[独立规则 prompt](../../../ideas/abstract_rules_audit_prompt.md)。
历史 pilot 依据：[设计 v0.2](../../../ideas/abstract_structure_study_design_v02.md)、
[冻结 prompt v0.2](../../../ideas/abstract_structure_annotation_prompt_v02.md)。执行者按版本使用，研究口径修改须按用户授权。

2026-09-09 的修改仅更新研究文档，尚未进行 v0.3 运行。运行器默认 prompt 路径现在指向 v0.3；
既有校验器仍保留 mechanism 历史枚举，新运行需加按 prompt 版本的约束，旧结果仍应可读。
理论 model + mechanism 的旧派生项不再适用于新版 How；Why 与四类共现只作启发式探索，
不能作为完整性门槛。具体接续要求见新版 prompt 的「执行交接」。

已完成首轮付费运行：开发集两轮（16 篇 × 双模型，prompt 从 v0.1 迭代至 v0.2 冻结）
与 pilot（100 篇 × 双模型，零失败，费用约 ¥7）。结果报告见
`notes/data/abstract_structure_pilot_report.md`；运行元数据见
`run_20260908_a/run_manifest.json` 的 `annotation_runs` 节。
规则审查（--task rules）尚未真实运行。

## 文件

| 文件 | 作用 |
|---|---|
| `textnorm.py` | 可导入模块：`normalize_abstract`（清洗+log）、`word_count_v1`、`whitespace_count`、`split_sentences`（pysbd，含字符偏移） |
| `probe_coverage.py` | 覆盖普查 → `coverage_issues.csv` / `coverage_summary.json` |
| `extract_abstracts.py` | 五刊适配器 + 派生台账 → `corpus_manifest.jsonl` / `run_manifest.json` |
| `validate_output.py` | 两个 prompt 输出契约的 JSON Schema + 语义校验器 |
| `llm_client.py` | DeepSeek（OpenAI-compatible）客户端：预算护栏、缓存、重试 |
| `run_annotation.py` | 批量标注执行（含 `--dry-run` 估算） |
| `sample_pilot.py` | pilot 分层随机抽样（seed 固定）→ `pilot_sample_manifest.jsonl` |
| `build_dev_annotations.py` / `build_review_annotations.py`(+`_v2`) | 把 agent 参照标注转成与模型输出同构的 JSONL |
| `compare_annotations.py` | 两份标注的句级 P/R/F1、paper_type 一致率 → `compare_*.json` |
| `derive_metrics.py` | 设计 §10.1–§10.9 派生指标 → `*_derived_*.json` |
| `fixtures/` | 合成语料 fixture（非研究数据），供 dry-run 演示 |
| `tests/` | pytest 契约测试 |

## 实际命令

Python 解释器：`F:/global_venv/.venv/Scripts/python.exe`
（依赖：pysbd 0.3.4、jsonschema、requests、python-dotenv、pytest；均已装入该 venv）

```bash
PY=F:/global_venv/.venv/Scripts/python.exe
BASE=modules/academic_research/abstract_structure

# 覆盖普查（全量约 2–3 分钟，大头是 ECMA page.html 读取）
$PY $BASE/probe_coverage.py

# 派生摘要台账（全量约 5–10 分钟）
$PY $BASE/extract_abstracts.py

# 测试
$PY -m pytest $BASE/tests/ -q

# 标注 dry-run（合成 fixture，不发起 API 调用）
$PY $BASE/run_annotation.py --task annotation --dry-run \
    --sample  $BASE/fixtures/synthetic_sample.jsonl \
    --corpus  $BASE/fixtures/synthetic_corpus.jsonl --model deepseek-v4-flash

# pilot 实际运行（run_20260908_a，已执行；付费调用需用户授权）
R=data/processed/abstract_structure/run_20260908_a
$PY $BASE/sample_pilot.py --corpus $R/corpus_manifest.jsonl \
    --out $R/pilot_sample_manifest.jsonl --per-journal 20 --seed 20260908
$PY $BASE/run_annotation.py --task annotation --corpus $R/corpus_manifest.jsonl \
    --sample $R/pilot_sample_manifest.jsonl --model deepseek-v4-flash --run-dir $R \
    --prompt-file ideas/abstract_structure_annotation_prompt_v02.md
$PY $BASE/derive_metrics.py --corpus $R/corpus_manifest.jsonl \
    --annotations $R/pilot_annotations_deepseek-v4-flash.jsonl \
    --sample $R/pilot_sample_manifest.jsonl --out $R/pilot_derived_deepseek-v4-flash.json
$PY $BASE/compare_annotations.py --ref $R/review_agent_annotations.jsonl \
    --pred $R/pilot_annotations_deepseek-v4-flash.jsonl --out $R/compare_review_vs_deepseek-v4-flash.json
```

## 配置方式

所有路径定位基于 `pathlib.Path` + `__file__`，不依赖 cwd。默认值是脚本顶部常量，
均可由 CLI 参数覆盖：

- `--upstream-root`：上游只读数据根（playwright_crawler 的 top_journal_dataset），
  也可用环境变量 `ABSTRACT_STRUCTURE_UPSTREAM_ROOT` 指定；两者都未配置时报错退出
- `--output-root` / `--run-id`：默认 `data/processed/abstract_structure/run_20260908_a`
- `run_annotation.py`：`--corpus`、`--sample`、`--task {annotation,rules}`、
  `--prompt-file`、`--model {deepseek-v4-flash,deepseek-v4-pro}`、`--run-dir`、
  `--max-requests` / `--max-total-tokens` / `--max-cost-cny`（预算护栏）
- LLM 凭据：环境变量 `DEEPSEEK_API_KEY`，或用环境变量 `DEEPSEEK_ENV_FILE` 指定
  含该变量的 .env 文件（`DeepSeekClient(env_path=...)` 亦可）；key 不进入任何日志与落盘

## 版本与计价

- `WORD_COUNT_VERSION = "v1"`；`NORMALIZE_VERSION = "v1"`；
  `SENTENCE_SPLITTER = "pysbd 0.3.4"`（均在 textnorm.py）
- 计价（CNY/百万 token，来源 `LLMClient/token_usage_tracker.py`，核验 2026-09-08）：
  flash 输入 1.0 / 输出 2.0 / 缓存命中输入 0.02；pro 输入 3.0 / 输出 6.0 / 缓存命中 0.025

## 能力 → 验证映射

| 能力 | 验证 | 状态 |
|---|---|---|
| 计词边界（don't / difference-in-differences / 3.5 / 1,000 / 百分号） | `tests/test_textnorm.py::TestWordCount` | 通过 |
| 清洗幂等、JPE 前缀、尾部 JEL/Keywords、疑似正文保留 | `tests/test_textnorm.py::TestNormalize` | 通过 |
| 切句偏移回切（text[start:end]==句文本，缩写/小数不断句） | `tests/test_textnorm.py::TestSplitSentences` | 通过 |
| 五刊适配、类型排除、DOI 规范化、版本冲突 selected、坏 JSON 显式记录 | `tests/test_extract_abstracts.py`（合成树） | 通过 |
| 真实上游 smoke | `test_real_upstream_smoke`（根目录缺失时 skip） | 通过（本机） |
| annotation 契约校验（全覆盖/quote 子串/focus 与 aspects 规则/connective_only/位置不唯一→needs_review） | `tests/test_validate_output.py` | 通过 |
| rules 契约校验（七项齐全/枚举/applies-scope 一致/jargon 状态一致） | `tests/test_validate_output.py` | 通过 |
| 覆盖普查全量 | `probe_coverage_20260908/coverage_summary.json` | 已运行 |
| 摘要台账全量 | `run_20260908_a/corpus_manifest.jsonl` | 已运行 |
| LLM 客户端真实调用 | dev 两轮 + pilot 100 篇 × 双模型（run_20260908_a），契约合规率 100%、零失败 | 已验证 |
| 空响应循环内重试（重试计入预算，仍空则非 transient 抛出） | `tests/test_llm_client.py`（mock `_post`）；真实运行中触发并重试成功 | 通过 |
| 派生指标 §10.1–§10.9（长度/功能列表/三态/覆盖上下界/句数/占比/顺序/框架外） | `tests/test_derive_metrics.py`（合成标注）；dev 16 篇与 pilot 100 篇实际运行 | 通过 |
| 规则矩阵 §10.10 | 未实现（第二阶段，留 TODO） | 未实现 |
| 修复请求路径（契约失败→1 次修复） | pilot 真实触发：flash 3 篇、pro 1 篇，均修复成功 | 已验证 |

## 已知边界与偏差（如实说明）

- **JPE 摘要来源回退**：任务基线取篇级 `article_content.json` 的 `abstract`，但 2023–2025
  上游篇级抓取大量为空（page.html 为错误页）。已核验：在篇级、期级均有值的期
  （2020–2023 抽样 5 期），期级 `abstract` 与篇级剥前缀后 33 篇中 32 篇空白归一后完全相等
  （唯一差异是篇级数学斜体重复渲染 "1 / 𝑒 1 / e"，期级反而更干净）。因此篇级为空时回退期级
  字段，记录 `abstract_source="issue_field_fallback"` 与 anomaly。未静默替换。
- **ECMA 部分文章（2019 起 Wiley 代理页）摘要经 ajax 加载**，静态 page.html 无
  abstract section → `extraction_error`，无合规回退（meta description 被截断，禁用）。
- **QJE/REStud 部分文章 abstract section 的 `text` 混入整篇正文**（全语料 373 篇，
  尾部带 "WorldCat Google Scholar" 等参考文献链接残渣）。已核验这 373 篇的
  `paragraphs[0]` 均为 `text` 前缀；此类记录取 `paragraphs[0]`（剥外层引号）并记
  anomaly `abstract_section_oversized:<len>:used_paragraph0`；前缀核验失败则记
  `extraction_error`，不静默兜底。
- **QJE/REStud 部分摘要尾部混入 OUP 订阅样板**（"As a benefit of your
  subscription…"，全语料约 800 条）。在样板起始处截断并记 anomaly
  `oup_subscription_boilerplate_removed`，不静默删除。
- **ECMA 期级文章列表含重复条目**（同文大小写不同标题两次出现），按规范化标题去重，
  期 anomaly 记 `issue_level_duplicates:N`。
- **non_english 检测未实现**：availability 枚举保留该值但当前不会赋予；README 如实标注。
- AER `AER201804_4-5`（重复合刊目录）、`AER201505_5/201605_5/201705_5`（P&P 专辑）
  整期排除并记录原因；`AER202607_7/08/09` 缺期级元数据（2026 partial year）。
- dry-run 的 token 估算为粗估（英文 ≈4 字符/token），仅用于预算预览。
