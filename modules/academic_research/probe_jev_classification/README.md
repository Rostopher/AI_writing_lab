# probe_jev_classification

用 TypeSafe Jev（经 Vercel AI Gateway）对经济学论文摘要做类型分类，与 DeepSeek v4-flash 的标注结果对比。

## 目的

测试 Jev 的 `state + questions` 接口在论文类型判定上的表现，评估其作为大规模论文结构化第一层语义 mapper 的可行性。

## 设计

- **输入**：title + abstract_normalized（来自 `run_20260908_a/corpus_manifest.jsonl`）
- **基准**：DeepSeek v4-flash 标注（`run_20260909_v03_full/annotation_flash/annotations.jsonl`，prompt v0.3）
- **Jev 问题**（每篇一次调用，5 个并行问题）：
  - 4 个布尔成分：`methods` / `empirical` / `theory` / `structural`（措辞对齐 DeepSeek 成分定义）
  - 1 个 Choice 主类型：5 类互斥单选（`empirical` / `theory` / `mixed_or_structural` / `methods` / `unclear`）
- **对比维度**：
  - 成分层：Jev 布尔概率 >= 0.5 判 yes，与 DS component (yes/no) 比
  - 主类型层：Jev Choice 直判 + 代码组合两种，与 DS primary_type 比

## 文件

| 文件 | 用途 |
|---|---|
| `test.ts` | 最小调用验证（1 条假数据） |
| `sample_benchmark.ts` | 分层抽样 benchmark（默认每类 5 篇），带详细对比输出 |
| `run_full.ts` | 全量 4250 篇，并发 5，断点续跑 |
| `analyze_full.py` | 全量结果分析：一致率、混淆矩阵、calibration、不一致案例 |

## 运行

```bash
# 进入目录
cd modules/academic_research/probe_jev_classification

# 安装依赖（首次）
PATH="/c/nvm4w/nodejs:$PATH" npm install

# 最小测试
PATH="/c/nvm4w/nodejs:$PATH" npx tsx test.ts

# 抽样 benchmark（每类 5 篇）
PATH="/c/nvm4w/nodejs:$PATH" npx tsx sample_benchmark.ts

# 全量（后台跑）
PATH="/c/nvm4w/nodejs:$PATH" npx tsx run_full.ts

# 分析
F:/global_venv/.venv/Scripts/python.exe analyze_full.py [full|sampleN] [threshold]
```

## 环境

- `.env` 需要 `JEV_API_KEY`（映射到 `AI_GATEWAY_API_KEY`）
- Node.js >= 18，`ai` >= 7.0.105
- 模型硬编码 `typesafe-ai/jev`，无 fallback

## 初步发现（25 篇样本）

- 成分层一致率 >90%（empirical 91%, theory 96%, structural 96%）
- 主类型 Choice 72% 一致，composed 60%
- Jev 几乎不判 unclear；DS 标 unclear 的论文 Jev 多判为 empirical，人工核查后 Jev 更合理
- Choice 的 softmax 归一化比代码阈值组合更能做主贡献权衡
