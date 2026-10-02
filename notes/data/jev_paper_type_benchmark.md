# Jev 论文类型分类 benchmark（对照 DeepSeek v4-flash 全量标注）

> 日期：2026-09-20；状态：全量完成。
> 代码：`modules/academic_research/probe_jev_classification/`（README 有运行方式）。
> 结果：`jev_results_full.jsonl`（4250 篇逐篇记录）、`disagreements_full.jsonl`（373 篇不一致案例）。

## 设计

- 被测模型：TypeSafe Jev（`typesafe-ai/jev`，经 Vercel AI Gateway，AI SDK `experimental_evaluate`）。
  凭据走环境变量 `JEV_API_KEY`（映射 `AI_GATEWAY_API_KEY`）；代码硬编码模型 ID，无 fallback。
- 输入：title + abstract_normalized（`run_20260908_a/corpus_manifest.jsonl`）。
- 基准：DeepSeek v4-flash 全量标注 `run_20260909_v03_full`（prompt v0.3）。
- Jev 问题（每篇一次调用，5 个并行问题，措辞对齐 DS prompt 的 RESEARCH TYPE 段）：
  - 成分层 4 个布尔（非互斥）：methods / empirical / theory / structural
  - 主类型 1 个 Choice（互斥）：empirical / theory / mixed_or_structural / methods / unclear
- 另测了"成分布尔 + 代码阈值组合出 primary_type"（composed）作为对照。

## 结果（4250 篇，0 失败）

成分层一致率（Jev 概率 ≥0.5 判 yes，DS=unclear 不计入）：
- empirical 97.9%（4062/4150）；theory 94.6%（3940/4166）；structural 97.8%（3945/4032）

主类型一致率（对 DS primary_type）：
- **Jev Choice 直判 91.2%**（3877/4250）；代码组合 composed 81.8%（3475/4250）

Choice 置信度校准：
| 置信度 | 一致率 | 占比 |
|---|---|---|
| ≥0.95 | 97.8% | 78% |
| 0.90–0.95 | 77.5% | |
| 0.80–0.90 | 82.1% | |
| 0.70–0.80 | 67.9% | |
| 0.50–0.70 | 56.6% | |
| <0.50 | 32.5% | |

成本：407 万 tokens（input 351 万），约 3.5 小时（并发 5→15 吞吐不变，上游限流 ~17/min 为实际上限；
限流失败记录靠断点续跑补跑，79 篇全部重试成功）。

## 分歧模式

- DS=theory 而 Jev=mixed_or_structural：102 篇（Jev 更易把量化理论判 mixed）。
- DS=unclear 的 53 篇 Jev 只同意 1 篇：Jev 几乎不主动判 unclear。人工抽查
  （Narrative Economics、Star Scientists、Old Age Risks 等 9 篇）显示 Jev 在这些案例
  多数更合理——DS 的 unclear 偏保守。
- 成分层不一致极少且双向对称（empirical 44+44、structural 64+23、theory 169+57），
  主要分歧集中在"哪个是主贡献"的权衡，不是成分识别。

## 结论与边界

- Jev 适合作为论文级语义判定的第一层（cheap semantic mapper）：成分识别与 DS 高度一致，
  主类型 Choice 直判优于代码组合，置信度可用于路由（≥0.95 自动接受）。
- 局限：Jev 不给证据引文（DS prompt 要求 quote，Jev 布尔/Choice 接口无法约束）；
  unclear 行为与 DS 口径不同，对比时 DS=unclear 需单独处理。
- 复现：`run_full.ts`（全量，断点续跑）→ `analyze_full.py`（分析）。
