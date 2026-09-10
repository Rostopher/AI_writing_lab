# Academic Paper Writing 迁移档案

- **Archived:** 2026-09-08
- **Reason:** 将姊妹仓库 `playwright_crawler/research/projects/academic_paper_writing` 的研究笔记、研究 proposal、六个固定参考仓库和原项目快照集中接续到 `AI_writing_lab`，保留来源路径、版本和逐文件完整性证据。
- **Preserves:** 来源为 `playwright_crawler` 仓库的 `research/projects/academic_paper_writing/`；迁移前为未提交目录，六个参考仓库保留 `.git`、固定 HEAD、分支和许可证。逐文件原始哈希保留在清单中；六个 Git 索引缓存的后续差异见迁移报告。
- **Distilled into:** 当前项目快照见 [`memory-docs/STATUS.md`](../../STATUS.md)，模块导航见 [`detail_mem/PROGRESS.md`](../../detail_mem/PROGRESS.md) 与 [`detail_mem/MAP.md`](../../detail_mem/MAP.md)，研究约束见 [`memory-docs/CONVENTIONS.md`](../../CONVENTIONS.md)；历史决策原文见 [`source_project/memory-docs/detail_mem/DECISIONS.md`](source_project/memory-docs/detail_mem/DECISIONS.md)。
- **Keywords:** `academic_paper_writing`, academic writing, writing analysis, evaluation design, writing skills, reference repositories, NaturePanelForge, revise-paper, migration, legacy-apw
- **Reopen when:** 需要追溯旧项目路径、核对研究 proposal 的原始边界、复查六个参考仓库的固定版本或验证迁移完整性时，先阅读 [`manifest.md`](manifest.md) 和 [`file_manifest.json`](file_manifest.json)，再按 `source_project/` 与目标 `notes/`、`ideas/`、`repos/` 的映射查阅。

## 归档内容

- `source_project/` 保存源项目除已接续材料外的原始文件与目录结构；源 `AGENTS.md` 在归档中命名为 `AGENTS.md.snapshot`，避免旧规则在目标仓库生效。
- `notes/` 下 4 份实质笔记已原样进入目标 `notes/`；`ideas/` 下 3 份文件保留为历史 proposal，不能视为已验证结果。
- `repos/` 下六个外部参考仓库整体进入目标 `repos/`。目标 [`repos/README.md`](../../../repos/README.md) 是静态六仓导航；表中用途不构成实测效果排名。
- `manifest.md` 记录迁移范围、分类、六仓版本和来源重定向；`file_manifest.json` 记录 1,397 个来源文件的路径、字节数、SHA256 及迁移后核验状态。
