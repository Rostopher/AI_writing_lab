# Academic Paper Writing 迁移记录

- Archived: 2026-09-08
- Reason: 用户要求由子智能体将姊妹仓库的学术写作研究材料移动到 AI Writing Lab，接续已有研究并保留历史。
- Preserves: 来源仓库 `playwright_crawler`，项目相对路径 `research/projects/academic_paper_writing/`；1,397 个文件，共 162,498,892 字节。逐文件原路径、目标路径和原始 SHA-256 见 [file_manifest.json](file_manifest.json)。
- Distilled into: [当前状态](../../STATUS.md)、[模块进展](../../detail_mem/PROGRESS.md)、[研究入口](../../detail_mem/MAP.md)、[当前约定](../../CONVENTIONS.md)与[历史决策索引](../../detail_mem/DECISIONS.md)。
- Keywords: academic_paper_writing, AI_writing_lab, academic writing, rubric pilot, validity gate, writing skills, migration, legacy-apw
- Reopen when: 需要追溯旧研究设计、还原原路径、核验参考快照版本或复查迁移完整性时。

## 范围与文件去向

| 源项目内容 | 文件数 | 当前归属 |
|---|---:|---|
| 实质笔记 | 4 | 目标 `notes/concepts/` 与 `notes/pipelines/`，原文保留 |
| 研究问题、评价设计、skills 调研 | 3 | 目标 `ideas/`，仍属待验证方案 |
| 六个外部参考仓库（含 `.git`） | 1,365 | 目标 `repos/`，保留上游内容与版本 |
| 源 `repos/README.md` | 1 | 原文位于 `source_project/repos/README.md`；当前 `repos/README.md` 已合并六仓导航 |
| 原项目入口、说明、忽略文件与项目记忆 | 24 | `source_project/` 下保留原相对结构 |

源 `AGENTS.md` 唯一更名为 `source_project/AGENTS.md.snapshot`，避免旧规则在归档中继续生效。
源项目 README 原文也在快照中；源位置现在仅保留一份重定向 README。
期刊采集数据、其他研究项目与共享材料未纳入本次迁移。

## 完整性与版本核验

子智能体在移除源文件前完成复制核验，原始文件哈希已写入清单。
主智能体随后独立复算了全部 1,397 个原始文件在目标中的对应文件，包括合并导航的归档原文：

- 1,391 个文件的字节数与 SHA-256 均与迁移前一致。
- 6 个差异文件均为 `repos/<仓库>/.git/index`，字节数保持一致；迁移后的 Git 状态检查刷新了索引缓存。
- 在 `GIT_OPTIONAL_LOCKS=0` 下核查，六仓 HEAD 均与迁移前相同，`git diff --cached --quiet` 与 `git diff --quiet` 均返回 0。没有参考代码或暂存内容变化。
- 清单保留迁移前 `SourceSHA256` 和复制阶段核验记录，追加最终审计字段；不将缓存差异覆盖成“原始哈希”，也不宣称全部文件逐字节不变。

六个固定快照的来源、HEAD 与许可见 [repos/README.md](../../../repos/README.md)，详细迁移前后状态见 JSON 清单。
参考仓库继续沿用本地只读输入的 Git 忽略规则，没有在目标主仓库提交这些快照。

## 历史与当前边界

原项目目录在姊妹仓库中尚未提交，本次没有创建 commit；可恢复证据是迁入文件、嵌套仓库版本与逐文件清单。
当前主仓库也尚无首次提交。目录搬迁不等于研究实验完成。

旧项目 DEC-001/002 原文见 [历史决策](source_project/memory-docs/detail_mem/DECISIONS.md)，
当前索引使用 `legacy-apw:` 命名空间，避免与新项目编号冲突。
五层写作框架、Introduction rubric pilot 和 skills 排名仍需验证；已有研究局限在当前 PROGRESS 和原 proposal 中继续可见。

## 验证方式与运行材料

文件完整性按 JSON 清单逐文件复算；源目录检查只保留重定向 README；当前 Markdown 导航和两仓 memory-docs 使用各自已安装校验器检查。
一次性搬迁脚本已从归档移至被忽略的 `tmp/`，不作为可重复运行的公共入口。以后查证优先使用本记录与文件清单。
