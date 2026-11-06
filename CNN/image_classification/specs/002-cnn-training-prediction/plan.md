# Implementation Plan: CNN Training, Evaluation, and Prediction

**Branch**: `feat/002-cnn-training-prediction` | **Date**: 2026-11-06 | **Spec**: [spec.md](spec.md)

**Input**: `specs/002-cnn-training-prediction/spec.md`

## Summary

Extend the existing CPU Docker image with a small PyTorch classifier and separate train, evaluate, and predict operations. Cache unaugmented training tensors, share preprocessing, keep held-out images out of learning and selection, report paired accuracy, and save a CPU-portable checkpoint. Preserve the existing dataset-generator entrypoint.

## Technical Context

**Language/Version**: Python 3.14.10, Linux arm64

**Primary Dependencies**: `torch==2.15.0+cpu`, `torchvision==0.29.2+cpu`, `numpy==2.5.4`, `Pillow==13.0.0`, and pinned transitive dependencies in the existing shared requirements file; `setuptools==80.9.0` for builds. Resolve CPU wheels from the official CPU index and all remaining exact dependencies from the appropriate index. Validate in a clean build rather than assuming index metadata guarantees binary compatibility.

**Storage**: Feature 001 `/data/train/<class>` and `/data/held-out/<class>`; `/data/shapes.pth` on a host mount

**Testing**: Existing unittest suite plus focused unit, CLI, CPU Docker integration and checkpoint/reproducibility checks

**Target Platform**: Docker on arm64 Linux, `python:3.14.10-slim`, CPU only

**Project Type**: Local command-line image classifier alongside the existing dataset generator

**Performance Goals**: Small demo; 30 epochs and batch size 8 by default. No hard latency target; verify completion on the target environment.

**Constraints**: All documented commands work in Docker; preprocessing is shared; both accuracy metrics always reported together; held-out images never train, augment, or select models; no MPS or benchmarking.

**Scale/Scope**: 30 training and 15 held-out images; one input image per prediction; three classes.

## Constitution Check

- **Simplicity**: PASS. One small classifier package, shared transforms, and no additional service; model dependencies are required by the feature.
- **Reproducibility**: PASS. Fixed overridable seed for all training randomness, pinned Python and dependencies; CPU repeat tolerance tested, limits documented.
- **Honest evaluation**: PASS. Both sets always reported together; held-out data never controls training or model selection; demo limitations documented.
- **Shared preprocessing**: PASS. A single transform is used across all operations; augmentation is training only; preprocessing metadata travels with checkpoint.
- **Conventional Commits**: PASS. Any commits must follow project rules.
- **Technical constraints**: PASS. Docker CPU and CPU-resident checkpoint, weights-only loading. MPS is explicitly out of scope.

**Post-design gate**: PASS, subject to verification of pinned wheel resolution, Docker execution, and the requirements checks during implementation.

## Project Structure

### Documentation (this feature)

```text
specs/002-cnn-training-prediction/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/cli.md
```

### Source Code (project root)

```text
Dockerfile                         # preserve existing generator entrypoint
requirements.txt                   # one shared exact-pin dependency file
src/shape_dataset/                 # existing generator, unchanged interface
src/shape_classifier/
├── __main__.py                    # train, evaluate, predict CLI
├── data.py                        # dataset validation and caching
├── transforms.py                  # shared preprocessing and training augmentation
├── model.py                       # matching CNN definition
├── train.py                       # training and paired evaluation
└── checkpoint.py                  # save/load and metadata validation
tests/                             # existing generator checks and classifier checks
README.md
```

**Structure Decision**: A separate classifier module is invoked with Docker's `--entrypoint python`; this leaves the existing generator's direct flags and default container command intact.

## Complexity Tracking

| Added complexity | Why needed | Simpler alternative rejected |
|---|---|---|
| Shared preprocessing and checkpoint metadata validation | Prevents training/prediction drift and rejects incompatible checkpoints. | Independent transforms or weights-only files omit information required for reliable prediction. |
| In-memory training cache | Required to resize each image once and avoid per-epoch disk reads. | Reloading images each epoch violates the feature specification. |
