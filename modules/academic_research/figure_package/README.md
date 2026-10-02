# Top5 论文与图片导出

按已有 AI 论文类型标注选择论文，经 OCR crosswalk 定点读取原始 PDF 和布局，
生成一篇论文一个文件夹的离线资料包。不遍历上游论文目录，不调用模型或重新 OCR。

默认口径：2021–2026 年，Top5，`primary_type == empirical`。
不按 JEL、图片类型或图片质量进一步挑选。PDF 内的附录图一并导出；
没有另行收集独立的 online appendix。

图片按 **PDF 页** 导出，合并该页所有 image/chart 图块及其标题，保留原有面板排列。
Figure/Table 以标题优先：补回带 Figure 标题的 table 块，排除带 Table 标题的图块；
仅有 Table 标题的页不把表格截图当作 Figure。调整数量和位置逐篇记录。
一页有多张图时放在同一张 PNG。若 PDF 图题提示 OCR 漏检、页坐标异常，
则导出整页并在 `paper_info.json` 记录原因。原 PDF 原样复制。
`reviewed_pages.json` 保存此次对无 OCR 图块的候选页逐页核查后的排除记录：
正文引用、只有续页图注、原 PDF 图形区域为空的页面不计入图片；真正的文字型 Figure 保留。

```text
top5_empirical_2021_2026/
  README.md
  papers.csv
  summary.json
  AER_2021_…__Short_Title/
    paper.pdf
    paper_info.json
    images/
      page_003.png
```

运行（使用已安装 PyMuPDF 的 Python 环境）：

```powershell
python export_paper_package.py --crawler-root <采集仓库> --output-root <输出目录> --workers 4 --zip
```

输入标注默认使用本仓库 `run_20260909_v03_full/annotation_flash/annotations.jsonl`，
摘要语料台账用于报告已标注但未匹配 OCR 的论文。通过 `--annotations`、`--corpus`
可以显式覆盖；通过 `--paper-id`（可重复）可以定点试运行。

重跑只复用已经完成且输出文件、图页数量均齐全的论文目录；不得覆盖输入数据。
导出规则修正后，可用 `--refresh-generated` 重建旧版本生成物；仅清理该清单中失效的 PNG。
失败记录在输出目录旁的运行日志中，任何失败都会阻止打包。
压缩包从运行清单中的文件构建，支持 ZIP64，并读取 ZIP 内容进行 CRC 校验。
运行统计、未匹配的分类记录与导出异常均明确报告，不将 OCR 未匹配解释为无图片。

验证以定点样例的原 PDF/导出图目检、输入输出数量对账和 ZIP 完整性检查为主。
这是批量导出工具，OCR 图块识别本身不是人工全页标注。
