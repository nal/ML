# Classifier CLI Contract

The existing `python -m shape_dataset` interface and its Docker default entrypoint remain unchanged. Classifier operations use `python -m shape_classifier` inside the same image:

```text
python -m shape_classifier train [--data-dir PATH] [--checkpoint PATH]
    [--seed INTEGER] [--epochs POSITIVE_INTEGER] [--batch-size POSITIVE_INTEGER]
    [--dataset-train-seed INTEGER] [--dataset-held-out-seed INTEGER]
python -m shape_classifier evaluate [--data-dir PATH] [--checkpoint PATH]
python -m shape_classifier predict IMAGE [--checkpoint PATH]
```

- Defaults: data directory `/data`, checkpoint `/data/shapes.pth`, seed 42, epochs 30, batch size 8. Omitted dataset seed flags record `unknown` independently.
- `train` uses only training data for optimization and saves the final model; it reports labeled training and held-out correct/total counts and accuracies together. `evaluate` loads the checkpoint and reports both counts and accuracies, with no training. `predict` prints one of `circle`, `rectangle`, `triangle` and does not report accuracy.
- Each operation logs runtime environment, resolved CPU device, Python and PyTorch versions; no unpaired accuracy is logged.
- Invalid data, arguments, unreadable image, incompatible checkpoint, failed training or unwritable output returns nonzero with a clear stderr message; do not emit a success result. Extra non-image files in data directories are ignored; unexpected PNGs or invalid class directories fail dataset validation.
- Existing generator behavior and flags remain supported and are tested as a regression.
