# 现成 Skills 与一手参考资料

核查日期：2026-09-10。以下均为参考资料，不代表本项目 skill 得到相关机构认证。此包不含第三方 skill 的复制件、字体文件或原始研究数据。

## A. 可以直接参考的现成 Skills

### K-Dense：scientific-visualization

仓库：`K-Dense-AI/scientific-agent-skills`

路径：`skills/scientific-visualization/SKILL.md`

来源：`https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/scientific-visualization/SKILL.md`

适合用作科学图形的工作流基础，涉及证据定义、图形编码、可访问性、输出与检查。该目录还包含 references、scripts、assets；需要使用原版时应读取完整目录，而不只是复制一段提示词。它不是 Nature 或 Science 的官方规则。

### Anthropic：data-visualization

仓库：`anthropics/knowledge-work-plugins`

路径：`data/skills/data-visualization/SKILL.md`

来源：`https://github.com/anthropics/knowledge-work-plugins/blob/main/data/skills/data-visualization/SKILL.md`

提供图形选择、Python 模式、版式和可访问性建议。适合补充日常图形选择；其通用示例的画布、标题和字号不能直接当作正式期刊印刷规格。

### wshobson：data-storytelling

仓库：`wshobson/agents`

路径：`plugins/business-analytics/skills/data-storytelling/SKILL.md`

来源：`https://github.com/wshobson/agents/blob/main/plugins/business-analytics/skills/data-storytelling/SKILL.md`

偏非技术受众、汇报与数据叙事，强调信息主线。适合补充解释型短文的标题和顺序，不是 McKinsey 官方制图 skill。不能把其商业说服目标直接等同于研究推断规范。

## B. 官方出版规格

### Nature Research Figure Guide

制图规格：`https://research-figure-guide.nature.com/figures/preparing-figures-our-specifications/`

布局与输出：`https://research-figure-guide.nature.com/figures/building-and-exporting-figure-panels/`

当前页面列出 Nature 的印刷宽度 89 mm / 183 mm，普通文字 5–7 pt，分面标号另有 8 pt 要求，并强调标准字体、可编辑文字和矢量图形。这里是 Nature 相关页面的具体规格，不是所有 Nature Portfolio 期刊、网页图片和幻灯片的一体化标准。正式投稿前核查目标期刊、稿件类型与提交阶段。

### Science

官方初稿说明地址：`https://www.science.org/content/page/instructions-preparing-initial-manuscript`

本次该页面直接读取返回 403，因此本包不声称已核验 Science 当前的具体字号、尺寸或分辨率要求，也不以 Science Partner Journals 中其他刊物的作者指南替代 Science 主刊规范。

## C. 设计判断与案例

### Nature Methods：Points of View

官方分类导读：`https://blogs.nature.com/methagora/2013/07/data-visualization-points-of-view.html`

Layout：`https://www.nature.com/articles/nmeth.1711`

Labels and callouts：`https://www.nature.com/articles/nmeth.2405`

Storytelling：`https://www.nature.com/articles/nmeth.2571`

该系列涵盖布局、视觉显著性、色彩、标签与叙事，是给 agent 提炼设计规则的材料；部分文章正文可能需要订阅。并非所有设计建议都是期刊强制投稿要求。

关于科学叙事的边界：`https://www.nature.com/articles/nmeth.2726`

### Financial Times：Visual Vocabulary

来源：`https://github.com/Financial-Times/chart-doctor/tree/main/visual-vocabulary`

FT 可视化团队的图形选择参考，仓库包含简体中文版本。它是参考资源，不是原生 SKILL.md。

### McKinsey：公开图表案例

Chart of the Week：`https://www.mckinsey.com/featured-insights/charts`

Year in Charts：`https://www.mckinsey.com/featured-insights/year-in-review/year-in-charts`

可用作公开解释图的案例库。它们不是已经验证存在的官方通用制图 skill，也不宜被归纳成适用于研究论文的绝对规范。

## D. 外观工具，不等于设计 Skill

### SciencePlots

来源：`https://github.com/garrettj403/SciencePlots`

Matplotlib 样式库，提供 science、nature 等组合样式及其他选项。能帮助统一外观，但不会自动决定图形选择、文章证据顺序或多标签统计口径。项目名称与样式名称不代表 Science 或 Nature 的官方认证。
