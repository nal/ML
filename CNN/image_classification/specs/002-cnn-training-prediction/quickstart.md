# Quickstart Validation

Prerequisites: Docker daemon, writable host data directory and feature 001 generator. Run from the project root after implementation.

```sh
docker build -t shape-classifier .
mkdir -p data
docker run --rm -v "$PWD/data:/data" shape-classifier
docker run --rm -v "$PWD/data:/data" --entrypoint python shape-classifier -m shape_classifier train --seed 42 --dataset-train-seed 42 --dataset-held-out-seed 43
docker run --rm -v "$PWD/data:/data" --entrypoint python shape-classifier -m shape_classifier evaluate
docker run --rm -v "$PWD/data:/data" --entrypoint python shape-classifier -m shape_classifier predict /data/held-out/circle/01.png
docker run --rm --entrypoint python shape-classifier -m unittest discover -s tests
docker run --rm --entrypoint python shape-classifier -m pip check
```

The generator step writes or safely replaces its tracked images; use a fresh directory or ensure it is appropriate for regeneration. Training and evaluation each show paired training (30) and held-out (15) correct/total counts and accuracy, and `/data/shapes.pth` persists on the host. Prediction prints one supported class; its correctness is not guaranteed. Omitting dataset seed flags records them as `unknown`.

Repeat training with the same seed, settings and image in a separate output location; correct counts must differ by no more than one per set. Verify missing held-out images, unreadable images, invalid training configurations, and incompatible checkpoints fail clearly. Check that training images are decoded and resized once, evaluation and prediction share preprocessing without augmentation, and generator commands still work. See [CLI contract](contracts/cli.md) and [data model](data-model.md).

This small synthetic dataset is a learning demo, not evidence of real-world accuracy. Training accuracy alone does not establish generalization.
