# Repository Studies

未来用于把外部论文写作、审稿、benchmark 和 AI writing 仓库统一映射为：

```text
source input -> normalization -> model/rules/human judgment -> artifacts -> validation -> evaluation
```

当前只有人工审计笔记，见 `../../notes/pipelines/`；尚无可执行 extractor。后续若实现，应先写 `_test_*.py`，并只读取 `repos/`，不修改外部仓库。
