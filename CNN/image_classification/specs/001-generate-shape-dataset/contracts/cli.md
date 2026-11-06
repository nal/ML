# CLI Contract

Container entrypoint: `python -m shape_dataset`.

```text
python -m shape_dataset --output-dir PATH [--train-seed INTEGER] [--held-out-seed INTEGER]
```

- Docker default output is `/data`; `--output-dir` may override it. Defaults: training seed 42 and held-out seed 43; equal seeds are invalid.
- A successful invocation returns zero, identifies the output directory and set counts, and writes the layout described in [data-model.md](../data-model.md).
- Invalid arguments, equal seeds, unsafe manifests, untracked destination collisions, or filesystem errors return nonzero with an actionable error. Unrelated files are preserved. A process interruption during publication may leave partial generated output. The next invocation first resumes the recorded transaction; if files have changed unexpectedly or recovery data is invalid, it fails safely with an actionable error and preserves unrelated files. Power-loss durability is not guaranteed.
- Seed overrides affect only their corresponding set. Manifest metadata must not affect PNG bytes.
