# Implementation Plan: Improve Default Training

**Branch**: `feat/003-improve-default-training` | **Date**: 2026-11-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-improve-default-training/spec.md`

## Summary

Compare fixed 30-, 60- and 120-epoch candidates using only training images. Choose a longer default only when the predeclared training-count and time rule supports it; otherwise retain 30. Freeze the decision without publishing unpaired counts, then evaluate and report every candidate's training and held-out results together. Update both default entry points, documentation and focused regression checks.

## Technical Context

**Language/Version**: Python 3.14.10

**Primary Dependencies**: Existing pinned CPU PyTorch, torchvision, NumPy and Pillow; no new dependencies

**Storage**: Existing host-mounted generated dataset and CPU checkpoint; temporary private candidate data and a versioned paired comparison record under this feature

**Testing**: Existing unittest suite, focused CLI/default tests and Docker CPU integration checks

**Target Platform**: Docker, arm64 Linux CPU, one thread

**Project Type**: Local command-line classifier

**Performance Goals**: Select the shortest longer candidate with at least 3 additional correct training predictions and training time at most four times the 30-epoch baseline; otherwise use 30. Record actual time; no cross-machine latency promise.

**Constraints**: Fix decision before any candidate held-out result is inspected; retain paired reporting, deterministic setup, overrides, saved model compatibility, and unchanged architecture.

**Scale/Scope**: One fixed generated 30-image training split, 15-image held-out split, and 30/60/120 epoch candidates.

## Constitution Check

- **Simplicity**: PASS — reuse the existing model and CLI; the experiment is a short-lived validation harness, not a new runtime feature.
- **Reproducibility**: PASS — fixed generator seeds, training seed, image, settings and explicit decision rule; record dataset identity, versions and timing conditions.
- **Honest evaluation**: PASS — no candidate accesses held-out images before selection; choose from training counts and elapsed time, then report paired results without claims of generalization.
- **Shared preprocessing**: PASS — use existing data loader, transforms and augmentation.
- **Conventional commits and technical constraints**: PASS — Docker CPU and existing dependency pins; no commit bypass or new architecture.

**Post-design gate**: PASS. Candidate counts remain internal until the choice is frozen; every published training result is paired with the matching candidate's held-out result. No held-out data is used for selection. Generate any missing legacy checkpoint only after the decision is frozen.

## Project Structure

### Documentation (this feature)

```text
specs/003-improve-default-training/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── contracts/cli.md
├── quickstart.md
├── comparison.md       # implementation-time selection record
└── tasks.md            # generated later
```

### Source Code (project root)

```text
src/shape_classifier/__main__.py  # CLI epoch default
src/shape_classifier/train.py     # Python training default
src/shape_classifier/data.py     # shared cached training dataset
src/shape_classifier/transforms.py
README.md
tests/test_classifier.py          # existing and focused regression coverage
```

**Structure Decision**: Keep the existing classifier and command interface. Any experiment harness is temporary, uses existing components, and must be checked for equivalence to the real training loop; do not add a separate production command.

## Complexity Tracking

No constitution violations require justification.
