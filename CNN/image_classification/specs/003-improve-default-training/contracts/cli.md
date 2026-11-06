# CLI Contract

- `python -m shape_classifier train [--epochs POSITIVE_INTEGER]` uses the selected, documented default if `--epochs` is omitted. An explicit positive integer, including 30, overrides it. Zero, negative and non-integer values fail with nonzero status.
- The `shape_classifier.train.train()` Python entry point uses the same selected default as the CLI.
- A completed training operation saves a compatible CPU checkpoint and reports training and held-out correct/total counts and accuracy together. Errors do not claim success.
- `evaluate` and `predict` retain their current interfaces and support existing compatible and newly produced checkpoints.
- Dataset generation and its entrypoint remain unchanged. No public candidate-comparison or unpaired accuracy command is introduced.
