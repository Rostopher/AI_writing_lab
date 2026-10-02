我先看下 manuscripts 里摘要研究的写法，再把表注分析的完整结果跑一遍。

摘要研究的套路清楚了：标注 → 统计分布 → 提炼公式 → 配真题示例。现在把表注的完整分析跑一遍：

数据全了。我再补两个关键条件统计（"有注的表"内部的分布），并抽几条真实表注当样例：

验证完毕，规律可以讲了。以下全部基于 686 篇论文、5041 张表的标注（2021–2026，Top5 实证论文），先说结论：**顶刊实证论文的表注有一套相当趋同的写法，和摘要的 WHFFF 一样，可以提炼成公式**。

## 规律一：先决定"写不写"——两派期刊，两种合法答案

40% 的表没有表注，这是真实分布（MinerU 无漏抓，我们验证过）。但不是随机不写，而是强烈的期刊风格：

- **AER**：无条件中位数 5 句——几乎张张写
- **JPE / QJE**：中位数 0——半数表不写注
- REStud 居中偏写，ECMA 样本少（69 张）参考性弱

所以"不写注"在 JPE/QJE 是正常操作，通常发生在 caption 已自明、变量定义在正文或附录、无星号要解释的情况。但如果你的表有 SE、星号、缩写变量，不写注的代价是读者读不懂——这类表在顶刊里几乎都配注。

## 规律二：写的话，4–8 句，中位数 6

只看有注的 3186 张表：句数中位数 **6**，p25=4、p75=8、p90=10。5 句最多（444 张），4–8 句合计占 62%。超过 10 句的不到 10%。一句话：**表注是一段，不是一节**。

## 规律三：写什么——"核心四件套"+ 两个按需项

有注表里各功能的出现率：

| 功能           | 占比  | 干什么                          |
| -------------- | ----- | ------------------------------- |
| var_def        | 77.6% | 变量/缩写怎么定义、怎么构造     |
| sig_marker     | 70.7% | SE 在哪、聚类到哪层、星号含义   |
| table_purpose  | 68.9% | 这张表估计/报告什么             |
| sample         | 55.6% | 样本限制、N、观测期             |
| col_nav        | 55.1% | 列/panel 导航（"Column 1 is…"） |
| method         | 52.5% | 估计方法细节                    |
| identification | 39.5% | 识别策略（按需）                |
| data_source    | 34.0% | 数据来源（按需）                |

var_def + sig_marker + table_purpose 是雷打不动的核心；identification 和 data_source 只在需要时出现（首stage/IV 表的 identification 达 49%，summary 表只有 5%，但 summary 表的 data_source 有 30%）。

## 规律四：顺序有公式——"目的开头，SE 收尾"

对 3113 条非空注做了位置验证：

- **30.6% 以 "This table presents/reports…" 开头**（首句含 SE 的只有 8.4%）
- **48.4% 以 SE/聚类/星号句结尾**

中间填变量定义、样本限制、列导航。典型模板（AER 2022 一篇表 8 的真实注，6 句）：

> Notes: Locally weighted observations: 565,687. ①样本量 All estimates are evaluated at the mean values of the instruments. ②方法 Standard errors in parentheses are block bootstrapped at the high school campus by cohort level. ③SE Complier shares are the same across outcomes due to common first stage equations. ④技术细节 Academic outcomes are measured at age 28. ⑤变量定义 Quarterly earnings are measured in real 2010 US dollars and averaged within person over ages 28–30. ⑥变量定义

对应到摘要研究的表格，可以这样落地：

| 位置        | 这句要完成的事                                              |
| ----------- | ----------------------------------------------------------- |
| 开头 1 句   | 这张表报告什么（也可省，caption 已说时）                    |
| 中间 2–5 句 | 变量定义/构造 → 样本限制 → 列或 panel 导航 → 方法与识别细节 |
| 最后 1 句   | SE 位置、聚类层级、星号/括号约定                            |

## 规律五：每张表自含地重复，别用指针

`note_strategy` 修正后的分布：**repeat 63.3%**、mixed 14.7%、**pointer 只有 2.5%**。只有 8.3% 的表出现 "See notes to Table X"。最极端的证据：上面那篇 AER 2022 的表 8、11、12 的注几乎逐字相同（同一套 SE 约定、同一套变量测量，每张表完整重写一遍）。

这个发现和直觉相反——很多人觉得重复写注是偷懒，应该用指针。但顶刊的实际惯例是：**让读者不翻页就能读懂每一张表**。指针省的是作者的墨水，花的是读者的时间。

## 一个必须说的边界

按项目规则强调：这些是**观察到的趋同惯例**，不是"这样写导致发表"的因果证据——研究质量和写作方式交织在一起。它的正确用法和摘要 skill 一样：当你不知道怎么写时，这是顶刊的默认答案；当你有理由偏离时（比如投 JPE/QJE 且表已自明），偏离也有顶刊先例撑腰。

如果下一步要做成和摘要 skill 对等的"表注 skill"，我建议补一块：按表类型（回归/IV/summary/balance）各出一个模板 + 2–3 条真题示例，数据都在 `annotations.jsonl` 里，随时可以抽。





对，是真的没有——我去 MinerU 的 layout.json 里核对过，它明确区分了有 `table_footnote` 子块和没有的表，不是漏抓。但"为什么没有"我之前只给了推测，现在可以直接拿数据验证。让我看看这些无注表到底长什么样：

子块的 html 是空的，文本在 lines/spans 里，重新抽取：

原因查清楚了，而且**我要修正自己之前的结论**。"MinerU 没有漏抓"这个判断我只在一篇 AER 论文上验证过，外推到全部期刊是错的。完整证据链是这样的：

## 无注表的三个来源，真假各占一部分

**来源一：抽取错误（占大头，集中在 JPE/QJE）。** 那篇 JPE 论文（jpe_2021_711347）的 layout.json 显示：

- 表 1 的注明明存在于 PDF——"…student from the ECLS-K. All models are estimated by OLS. Standard errors are clustered…"——但 MinerU 把它标成了 `table_caption` 而不是 `table_footnote`，我们的抽取只取 footnote 块，所以是空的
- 注文本还以 sub/sup 乱码形式混进了 caption 字段（`<sub>vationisastudentfromtheECLS-K</sub>`——"Note" 这个词本身都被 OCR 拆碎了，所以我第一轮搜 "Note" 只找到 2-4%，低估了）
- JPE 的注用小字号印在表下（`Note.—…` 格式），和标题块长得像，MinerU 在 JPE/QJE 的紧密版式上系统性分错

量化：无注表里 caption 带乱码的比例——**AER 0%、JPE 44%、QJE 53%**、REStud 19%；caption 里能检出注特征词（standard error/clustered/significant）的——AER 4%、JPE 10%、QJE 21%。也就是说 **JPE/QJE 的"无注表"至少有一半是抽取假象**。

**来源二：续表（真实但小头）。** QJE 无注表里 13% 是 "TABLE II CONTINUED" 跨页续表（caption 被 OCR 拆成 "ABLE I ONTINUE"，我第一轮只搜到 12 条也是因为乱码）。注只落在续表的首页或末页，中间页自然为空。

**来源三：真的不写注（真实存在，但没有 40% 那么夸张）。** AER 抽取干净（0% 乱码 caption），它的 364 张无注表基本是真的——AER 无注率约 17%，主要是 caption 已自明、变量定义在正文/附录的表。

## 对之前结论的影响

- "40% 无注是真实分布"——**高估了**。真实无注率可能在 25-30% 左右，且"JPE/QJE 半数表不写注"的期刊差异很大一部分是假象
- 有注表内部的统计（中位 6 句、roles 占比、repeat 63%）不受影响——那 3186 张表的注是真实抽出来的
- 规律五"repeat 为主、pointer 极少"也不受影响

## 建议的修法

`extract_table_units.py` 加一条规则：**出现在 `table_body` 之后的 `table_caption` 块，改判为 footnote**（这正是 MinerU 误标的模式：caption, body, "caption"），同时把含高密度 sub/sup 的 caption 标记为低质量。改完重跑抽取+标注，JPE/QJE 的长度和无注率数字会明显变化，AER 基本不动。

要不要我现在就改抽取脚本、把 JPE/QJE 重抽一遍？这样"表注怎么写"的规律才能建立在干净的数据上。





这个设计好——问题数从 `12×句数` 降到 `2×句数+1`，29 句的长注也只有 59 个问题，而且多功能句是少数，二次调用很便宜。我来改：

29 句的极限长注也跑通了——这次没有 503，证实之前的失败就是并发争用。结果质量相当好：

**表类型**：`main_results`（概率 1.00）✓

**句级标注**几乎全对：

- "OLS estimates of within-village treatment and placebo effects..." → table_purpose，multi=0.60 → 二次调用补出 method(0.94) + col_nav(0.85) + data_source(0.60)，这句确实同时干了四件事 ✓
- "Minimum q-values are in square brackets..." → multiple_test(1.00) ✓（DS 表级也标了这个 role）
- "Adult equivalents are constructed using the OECD scale." → var_def(1.00) ✓
- 十几个变量定义句全部 var_def(1.00) ✓
- "Notes." 这种纯开头 → none(0.98) ✓

**两个已知的小瑕疵**（都不影响使用）：

1. 句 13/14 在 "(Author 2008)." 处切分略糙——引用年末尾的句号被当成句末，但切出来的碎片也都被正确标了
2. 句 29-32 是 OCR 出来的 LaTeX 星号（`^{*}p<.10` 被拆成 4 段），Jev 还是全标对了 sig_marker

**成本**：这张怪物注 26k tokens（调用1）+ 6k（调用2）。普通短表 2-5k。4052 张 verdict=ok 的表全量跑估计 1500-2500 万 tokens，在 Vercel 当前 Jev 免费的情况下没问题。

**方案验证完毕，设计定稿**：

```
调用1（每表）：表类型 Choice + 每句主功能 Choice(13选1) + 每句多功能布尔
       = 1 + 2×句数 个问题
调用2（仅 multi≥0.5 的句）：补问其余 11 个功能的布尔
```

下一步我写正式的全量 runner（断点续跑 + 并发 + 结果落盘），先跑 50 张表试点确认稳定性，还是直接全量 4052 张？