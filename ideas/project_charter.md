# Project Charter

## Claim

学术论文写作不能被还原为语法纠错或语言润色。高质量写作至少同时要求：研究问题与贡献成立、论证结构清楚、每个 rhetorical move 完成功能、句子准确表达证据强度，以及修改不破坏事实和作者意图。

## Why It Matters

现有工具很容易优化可见的表层指标，但论文最重要的错误往往是结构性或认识论错误：gap 不成立、贡献与文献比较脱节、claim 强于 evidence、流畅改写造成意义漂移。没有可靠 evaluation，就无法判断 AI 是帮助写作还是只让错误更像论文。

## Research Questions

1. 不同 section 中可稳定识别的 rhetorical moves 是什么？
2. 哪些修改可以自动执行，哪些需要建议，哪些必须由作者或领域专家判断？
3. 如何把 paper/section/paragraph/sentence/lexico-grammar 五个层级连接起来？
4. 如何构造包含 hard negatives 的修订对，使模型不能只靠流畅度得分？
5. 自动 judge 与人类专家在什么维度上可靠，哪里必须保留人工 evaluation？

## Evidence Needed

- 论文写作、rhetorical move、hedging/boosting 和 peer review 相关文献。
- 带上下文、修改意图和作者接受结果的真实修订对。
- 不同领域、venue、作者语言背景和 section 的分层样本。
- 专家 pairwise preference、错误标签和评审一致性。
- 参考工具的 prompt、workflow、artifact 和 evaluation 实现。

## Minimum Viable Test

选择少量公开或明确授权的 Introduction 段落，构造原文、人工接受修订、流畅但过度宣称的 hard negative、语法正确但 discourse role 失败的 hard negative。先测试专家是否能用同一 rubric 稳定地区分它们，再测试自动 judge。

## Failure Modes

- rubric 只能复述个人风格偏好，跨评审者一致性低。
- 专家能判断好坏但无法形成可复用标注协议。
- 自动指标只奖励流畅度、长度或与单一 reference 的表面相似。
- 数据许可、隐私或作者身份使真实修订历史不可用。
- 不同领域和 venue 的写作规范差异大于可提取的共性。

## Possible Paper Shape

1. 学术写作质量的分层 taxonomy。
2. 带 validity gate 和 hard negatives 的修订 benchmark。
3. 人类—自动 judge 的可靠性与偏差研究。
4. 基于上述证据设计的可审计 AI writing assistant。
