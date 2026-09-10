# Modules

## Purpose

Executable research engineering layer: diagnostics, tests, data processing, mapping, analysis, tables, and figures.

## Suggested Layout

```text
modules/<module-name>/
  README.md
  PLAN.md
  _test_*.py
  run_*.py
  outputs/
  logs/
```

## What Belongs Here

- Python/R/Stata scripts
- Test-first diagnostic scripts
- Reproducible analysis modules
- Module outputs and logs

## What Does Not Belong Here

- Raw PDFs
- General notes
- External reference repos
- Final manuscript sections

## Rule

Use `Path(__file__)` for project paths, write outputs under the module, and keep long logs in `logs/`.

## Planned Modules

| 模块 | 当前状态 | 目标 |
|---|---|---|
| `repository_studies/` | 只有方法说明 | 统一抽取参考仓库的 input -> process -> artifact -> evaluation 契约 |
| `evaluation/` | 只有设计说明 | 实现 validity gate、多维 rubric、pairwise/expert evaluation 与可靠性分析 |
