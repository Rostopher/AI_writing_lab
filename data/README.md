# Data

项目数据层。是否版本化由**每份数据**的大小、许可证与可复现性决定，不默认全提交或全忽略。

## 建议布局

```text
data/raw/          原始数据（来自 playwright_crawler 的导出、下载物）
data/interim/      中间处理结果
data/processed/    最终分析用派生数据
data/external/     第三方公开数据
data/dictionaries/ 数据字典、代码册、crosswalk
```

## 边界

- 期刊论文全文 / metadata 属 papers/ 层，由 paper-workspace 物化，不复制到这里。
- 数据理解与口径笔记 → `notes/data/`。
- 处理脚本 → `modules/`。
