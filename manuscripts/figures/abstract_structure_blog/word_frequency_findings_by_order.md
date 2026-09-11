# 纯发现句用词：按“第几句发现”拆分（审查表）

口径：仅含功能标签为纯 findings 的句子（排除 how+findings 等混合句），
按该句在所属摘要中的发现序号分为 F1/F2/F3/F4+（第4句及以后合并）；
数值 = 含该词（词组）的句子占该组句子总数的比例 %。已去停用词与年份。
标记词（下表）动词按 spaCy lemma 归并，比较级与功能词保留原形。

## 标记词梯度（图5 数据）

| 标记 | F1 | F2 | F3 | F4+ |
|---|---|---|---|---|
| we find | 12.5 | 5.0 | 4.6 | 4.2 |
| we show | 11.4 | 4.6 | 4.7 | 2.7 |
| increase* | 12.4 | 12.6 | 11.4 | 10.8 |
| decrease*/reduce* | 11.1 | 11.3 | 10.8 | 8.2 |
| 机制簇 | 13.9 | 17.0 | 17.6 | 16.9 |
| welfare | 3.1 | 3.9 | 3.9 | 5.5 |
| finally | 0.1 | 0.3 | 1.6 | 3.3 |
| suggest* | 2.1 | 3.0 | 4.7 | 4.5 |
| first | 4.6 | 1.9 | 1.3 | 1.7 |
| percent* | 4.3 | 3.3 | 3.4 | 1.3 |

## F1 第1句发现（3947 句）

| 排名 | 词 | 句占比% | 句数 |
|---|---|---|---|
| 1 | show | 14.8 | 584 |
| 2 | find | 14.4 | 567 |
| 3 | but | 6.4 | 253 |
| 4 | equilibrium | 5.5 | 217 |
| 5 | firms | 5.3 | 209 |
| 6 | model | 5.0 | 199 |
| 7 | market | 5.0 | 198 |
| 8 | increase | 4.8 | 188 |
| 9 | large | 4.7 | 186 |
| 10 | optimal | 4.7 | 184 |
| 11 | effects | 4.5 | 179 |
| 12 | higher | 4.4 | 175 |
| 13 | information | 4.3 | 169 |
| 14 | increases | 4.1 | 161 |
| 15 | prices | 4.1 | 160 |
| 16 | first | 3.9 | 153 |
| 17 | policy | 3.6 | 143 |
| 18 | average | 3.6 | 142 |
| 19 | evidence | 3.6 | 141 |
| 20 | percent | 3.5 | 138 |
| 21 | results | 3.5 | 137 |
| 22 | rates | 3.4 | 134 |
| 23 | effect | 3.2 | 128 |
| 24 | less | 3.2 | 125 |
| 25 | price | 3.1 | 123 |

常见二元组：monetary policy（0.8%）、interest rates（0.8%）、paper shows（0.8%）、find evidence（0.8%）、labor market（0.8%）、percentage points（0.7%）、less likely（0.6%）、provide evidence（0.6%）、main result（0.6%）、results show（0.6%）

## F2 第2句发现（3124 句）

| 排名 | 词 | 句占比% | 句数 |
|---|---|---|---|
| 1 | show | 7.5 | 235 |
| 2 | but | 6.8 | 211 |
| 3 | find | 6.5 | 203 |
| 4 | increase | 5.8 | 181 |
| 5 | effects | 5.8 | 181 |
| 6 | higher | 4.7 | 147 |
| 7 | information | 4.7 | 146 |
| 8 | model | 4.7 | 146 |
| 9 | firms | 4.5 | 140 |
| 10 | market | 4.3 | 135 |
| 11 | effect | 4.3 | 133 |
| 12 | large | 4.2 | 132 |
| 13 | increases | 3.8 | 119 |
| 14 | welfare | 3.8 | 118 |
| 15 | less | 3.7 | 116 |
| 16 | results | 3.6 | 114 |
| 17 | prices | 3.6 | 114 |
| 18 | optimal | 3.5 | 108 |
| 19 | equilibrium | 3.4 | 105 |
| 20 | evidence | 3.2 | 101 |
| 21 | income | 3.2 | 100 |
| 22 | rates | 3.2 | 99 |
| 23 | however | 3.1 | 98 |
| 24 | risk | 3.1 | 97 |
| 25 | policy | 3.0 | 95 |

常见二元组：find evidence（0.7%）、percentage points（0.7%）、human capital（0.6%）、interest rates（0.6%）、less likely（0.6%）、results suggest（0.6%）、monetary policy（0.5%）、labor market（0.5%）、united states（0.5%）、adverse selection（0.4%）

## F3 第3句发现（1938 句）

| 排名 | 词 | 句占比% | 句数 |
|---|---|---|---|
| 1 | show | 7.2 | 140 |
| 2 | but | 6.9 | 133 |
| 3 | effects | 6.8 | 131 |
| 4 | find | 5.7 | 110 |
| 5 | firms | 5.1 | 98 |
| 6 | results | 4.7 | 92 |
| 7 | market | 4.6 | 90 |
| 8 | information | 4.5 | 88 |
| 9 | increase | 4.3 | 83 |
| 10 | higher | 4.1 | 80 |
| 11 | large | 4.1 | 80 |
| 12 | effect | 4.1 | 80 |
| 13 | model | 3.9 | 75 |
| 14 | evidence | 3.8 | 73 |
| 15 | less | 3.8 | 73 |
| 16 | welfare | 3.8 | 73 |
| 17 | prices | 3.6 | 70 |
| 18 | policy | 3.5 | 67 |
| 19 | risk | 3.4 | 66 |
| 20 | optimal | 3.4 | 65 |
| 21 | equilibrium | 3.4 | 65 |
| 22 | high | 3.3 | 64 |
| 23 | income | 3.2 | 62 |
| 24 | lower | 3.2 | 62 |
| 25 | time | 3.0 | 59 |

常见二元组：results suggest（1.2%）、find evidence（0.8%）、percentage points（0.8%）、monetary policy（0.7%）、labor market（0.6%）、welfare gains（0.6%）、provide evidence（0.6%）、interest rate（0.5%）、interest rates（0.5%）、tax rates（0.4%）

## F4+ 第4句及以后（1505 句）

| 排名 | 词 | 句占比% | 句数 |
|---|---|---|---|
| 1 | but | 8.2 | 123 |
| 2 | effects | 6.5 | 98 |
| 3 | find | 5.8 | 87 |
| 4 | welfare | 5.4 | 81 |
| 5 | model | 4.9 | 74 |
| 6 | higher | 4.7 | 70 |
| 7 | results | 4.5 | 67 |
| 8 | firms | 4.4 | 66 |
| 9 | show | 4.4 | 66 |
| 10 | market | 4.4 | 66 |
| 11 | increase | 4.3 | 64 |
| 12 | evidence | 4.3 | 64 |
| 13 | effect | 4.1 | 61 |
| 14 | optimal | 3.9 | 59 |
| 15 | increases | 3.9 | 58 |
| 16 | less | 3.7 | 55 |
| 17 | lower | 3.7 | 55 |
| 18 | price | 3.5 | 53 |
| 19 | large | 3.5 | 53 |
| 20 | policy | 3.5 | 52 |
| 21 | equilibrium | 3.5 | 52 |
| 22 | workers | 3.4 | 51 |
| 23 | gains | 3.3 | 50 |
| 24 | finally | 3.3 | 50 |
| 25 | costs | 3.3 | 49 |

常见二元组：welfare gains（1.1%）、labor market（1.1%）、results suggest（1.0%）、provide evidence（0.9%）、find evidence（0.7%）、monetary policy（0.7%）、long run（0.7%）、finally show（0.6%）、less likely（0.6%）、optimal policy（0.6%）
