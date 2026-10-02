---
layer: framework
update_mode: rewrite
role: "现在在做什么 —— 当前焦点 + 最近 3-5 条里程碑（快照，非流水账）"
read_when: "进入项目、规划工作、问当前状态时"
not_for: "模块级细节（-> PROGRESS），历史演变（-> HISTORY），决策来由（-> DECISIONS）"
line_budget: 160
stale_after_days: 14
---

# Status — AI Writing Lab

> 更新时间：2026-09-20

## Current Focus

- 学术研究与写作为当前主线；摘要结构全量描述的认识已转化为首个可分享产出：
  `skills/econ-abstract-writing/` 写作 skill（WHFFF 方法，中英双语文档）。
- Jev（TypeSafe `typesafe-ai/jev`，经 Vercel AI Gateway）评估模型接入验证完成：
  论文类型分类全量 benchmark 对 DS 标注一致率 91.2%（成分层 94.6-97.9%），
  置信度 ≥0.95 时 97.8% 准确；表注逐句标注设计（每句单选 + multi 补标）已验证。
- 表注（table notes）研究进行中：抽取管线 v3 + 全量标注完成，实证规律已总结
  （中位 5 句、var_def/sig_marker/table_purpose 核心三件套、repeat 72%）；
  过程中系统认识了 MinerU 版面抽取异常，OCR 验证/改进是用户指定的后续方向。
- 配套传播材料已就位：推文聚合统计与结构图、blog 草稿（待发布前校对）。
- 摘要结构研究第二阶段（规则审查 §7/H5、15 篇不一致案例复核、是否跑全量 pro）
  尚未启动；写作检查项落地前需先定目标期刊口径。

## Done（最近 3-5 条）

- [x] Jev 论文类型分类全量 benchmark（2026-09-20）— `probe_jev_classification`：
  4250 篇对 DS flash 标注，Choice 直判一致率 91.2%，成分层 94.6-97.9%，
  置信度 ≥0.95 子集 97.8% 准确（占 78%）；407 万 tokens；详见[benchmark 报告](../notes/data/jev_paper_type_benchmark.md)
- [x] Jev 表注逐句标注设计验证（2026-09-20）— `probe_jev_table_notes`：
  表级类型 Choice + 每句主功能单选 + multi 布尔二次补标；29 句长注跑通；
  拆句器用 DS n_sentences 交叉验证（75% 在 ±1）；全量 runner 待写
- [x] 表注管线与 MinerU 异常修复（2026-09-20）— 抽取 v1→v3 修四类版面异常，
  无注率 42%→18%（实证多为假象）；标注 prompt v0.3 含 note_verdict 同调用审计；
  全量 run_v03_full 731/732 篇 ¥12.5；详见[MinerU 异常目录](../notes/methods/mineru_layout_anomalies.md)
- [x] 首个写作 skill `econ-abstract-writing` 封装并推送（2026-09-11）— 单安装入口、英文 SKILL.md 为加载入口、中文为阅读译本；交流语言跟随用户、摘要默认英文；references 双语
- [x] 摘要结构传播材料（2026-09-11）— 推文聚合统计 + 结构图（fig1–6）、blog 草稿与配图、按功能用词统计；风格试验稿 styles/ 不入库，可用脚本复现

## In Progress

- Jev 表注全量标注：设计已验证，待写正式 runner（断点续跑+并发 5）并跑 4052 张
  verdict=ok 表（v3 数据）；随后可与 DS 表级 roles 对账。
- 表注写作规律：数据已净，待提炼为写作 skill / blog（参照摘要研究的产出路径）。
- blog 发布前校对：`manuscripts/draft/econ_abstract_blog.md` 附 editorial notes。
- 摘要结构研究：描述阶段完成，可靠性补强与规则审查待启动（见 Backlog 前三条，
  执行顺序未确认）。
- 学术写作评价设计：`ideas/evaluation_design.md` 仍为 proposal；Introduction rubric
  pilot 是未启动的候选方案。

## Backlog

- Jev 分类不一致案例复核：`disagreements_full.jsonl` 373 篇（对 DS 标签），
  其中 theory→mixed_or_structural 102 篇是主要模式。
- OCR 质量研究方向（用户指定）：如何 verify OCR 结果（规则+LLM 审计范式已验证）、
  如何更好地 OCR（MinerU 替代/后处理）；异常目录见 notes/methods/mineru_layout_anomalies.md。
- after_body_caption 回收的 157 张存疑表复核（note_verdict uncertain/not_note）。
- 15 篇同文标签不一致案例人工复核（全量可靠性证据）。
- 规则审查小样本（设计 §7/H5，套话/术语/识别策略，约 ¥6 量级）。
- 全量 pro（约 ¥150–200）：仅在需要全量尺度双模型证据时运行。
- 把「Why 仅 25%」「理论论文常省 how」「位置×功能倾向」做成写作检查项前，
  先决定目标期刊口径（按本刊风格对齐，不套全刊平均）。
- 评估 `papers/` 物化与数据工作区（依赖 playwright_crawler 数据）。

## 当前必须遵守的约束（快照）

> 这里只放"当前有效、影响决策"的少数硬约束。完整规则在 `CONVENTIONS.md`。

- 单仓库策略生效中；拆仓仅在触发条件满足时（DEC-001）
- 写作特征观察 ≠ 期刊青睐原因（DEC-004）；评价先拆可观察维度（CONVENTIONS）
- 版面/抽取层结论必须逐期刊验证，PDF 目检为地面真值（CONVENTIONS；DEC-008 同调用审计）
- 学术修改先检查事实、引用、证据强度与作者意图保持；历史 rubric、阈值和 taxonomy 仍待验证
- writing_pipeline / evaluation 为预留模块，不提前实现（DEC-001）
- public 仓库数据边界：LLM 调用缓存与含摘要全文产物不入库，只入派生层；
  凭据与私有路径走环境变量（DEC-007）

## 相关文档

- 模块实现清单：`memory-docs/detail_mem/PROGRESS.md`
- 项目演变：`memory-docs/HISTORY.md`
- 决策：`memory-docs/detail_mem/DECISIONS.md`
- 约定：`memory-docs/CONVENTIONS.md`
