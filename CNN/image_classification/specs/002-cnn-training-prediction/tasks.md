---
description: "Implementation tasks for CNN training, evaluation, and prediction"
---

# Tasks: CNN Training, Evaluation, and Prediction

**Input**: `specs/002-cnn-training-prediction/` specification, plan, research, data model, CLI contract, and quickstart.

**Format**: `- [ ] Tnnn [P?] [USn?] action with path`. `[P]` means independent work on different files with no dependency on an unfinished task.

## Phase 1: Setup

- [X] T001 Resolve and pin `torch==2.15.0+cpu`, `torchvision==0.29.2+cpu`, `numpy==2.5.4`, `Pillow==13.0.0`, `setuptools==80.9.0`, and all required transitive dependencies to exact versions in the shared `requirements.txt`, using the official CPU wheel index for CPU builds.
- [X] T002 Update `Dockerfile` to install the shared pins and classifier package while preserving the existing `python -m shape_dataset` entrypoint, generator flags, and Python 3.14.10 base image.
- [X] T003 Build `Dockerfile` cleanly on arm64; run `pip check` and CPU torch/torchvision import and transform smoke checks. Use a temporary minimal model for the initial forward-pass check; validate the feature classifier model after T005. Address resolver or binary incompatibilities before proceeding.

## Phase 2: Foundational

- [X] T004 Create `src/shape_classifier/__init__.py` and `src/shape_classifier/transforms.py` with shared RGB preprocessing `Resize((144, 256))`, `ToImage()`, `ToDtype(torch.float32, scale=True)`, and no additional normalization; define separate training-only rotation ±10°, horizontal/vertical flips at probability 0.5, and brightness/contrast/saturation jitter 0.1.
- [X] T005 [P] Create `src/shape_classifier/model.py` with two convolution/ReLU/pooling blocks, adaptive average pooling and a three-output classifier; preserve a stable model definition for checkpoint loading.
- [X] T006 Implement `src/shape_classifier/data.py` for root `/data`, splits `train` and `held-out`, and class order `["circle", "rectangle", "triangle"]`; require exactly 10 readable PNGs per training class and 5 per held-out class, reject missing/extra images and unexpected class labels, ignore unrelated non-image files, and apply the shared preprocessing.
- [X] T007 Implement `src/shape_classifier/checkpoint.py` for atomic save and `weights_only=True` load, strict model/metadata validation, CPU weights, and plain metadata: `class_order` `["circle", "rectangle", "triangle"]`, `input_size` `[144,256]`, `pixel_scaling` `"float32_0_1"`, integer `training_seed`, independent integer-or-`"unknown"` dataset seeds, string `pytorch_version`, `environment` `"docker"`, and `device` `"cpu"`.

## Phase 3: User Story 1 — Train and assess (Priority: P1, MVP)

**Goal**: Train from the existing dataset, save a reusable model, and display honest paired accuracy.

**Independent test**: Run training in Docker using both sets, verify the checkpoint persists on the host, and inspect training and held-out correct/total counts and accuracy together. Repeat with the same inputs and confirm the specified reproducibility tolerance.

- [X] T008 [US1] Implement caching in `src/shape_classifier/data.py`: decode and resize each training image once per run into unaugmented `[3,144,256]` float32 tensors in `[0,1]`, without epoch-by-epoch disk reads or resizing; preserve unaugmented data for accuracy reporting.
- [X] T009 [US1] Implement CPU training in `src/shape_classifier/train.py`: seed Python, NumPy and torch with default 42 before model and loader creation, use one CPU thread and deterministic algorithms where available, Adam learning rate 0.001, cross-entropy loss, default 30 epochs and batch size 8, and per-epoch training-only augmentation; never use held-out data for optimization or model selection.
- [X] T010 [US1] Implement unaugmented inference-mode assessment in `src/shape_classifier/train.py` for both splits after the final epoch; report each split's correct count, total and `correct/total` accuracy together, without any unpaired accuracy logs or weight updates.
- [X] T011 [US1] Save the final trained CPU state dict and metadata through `src/shape_classifier/checkpoint.py` to default `/data/shapes.pth` only after successful training; use user-supplied dataset seed provenance or independently record each omitted seed as `"unknown"`.
- [X] T012 [US1] Add `train` in `src/shape_classifier/__main__.py` with `--data-dir`, `--checkpoint`, integer `--seed` default 42, positive `--epochs` default 30, positive `--batch-size` default 8, and optional integer `--dataset-train-seed`/`--dataset-held-out-seed`; log Docker, CPU, Python and PyTorch versions and report errors to stderr with nonzero exit.
- [X] T013 [US1] Validate `specs/002-cnn-training-prediction/quickstart.md` training flow on a host mount: 30/15 paired counts, persisted CPU checkpoint with primitive metadata and weights-only loading, omitted/provided dataset-seed values, one-time preprocessing cache, held-out exclusion, and repeat-run correct counts differing by at most one per set.

## Phase 4: User Story 2 — Evaluate a saved classifier (Priority: P2)

**Goal**: Load a compatible checkpoint and report paired accuracy without retraining.

**Independent test**: Run evaluation with a compatible existing checkpoint and both sets; verify 30 and 15 total counts and accuracy equals correct divided by total; confirm missing held-out data fails.

- [X] T014 [US2] Implement checkpoint-based evaluation in `src/shape_classifier/train.py` using shared preprocessing, strict checkpoint metadata and matching weights, unaugmented inference mode, both 30-image training and 15-image held-out counts, and no parameter updates.
- [X] T015 [US2] Add `evaluate` in `src/shape_classifier/__main__.py` with `--data-dir` and `--checkpoint`, paired output and runtime details, and clear nonzero failures for missing, incomplete, corrupt or incorrectly labeled inputs.
- [X] T016 [US2] Validate the evaluation and failure scenarios against `specs/002-cnn-training-prediction/quickstart.md`, including a missing held-out image and incompatible checkpoint; confirm training accuracy is never printed alone.

## Phase 5: User Story 3 — Predict an image (Priority: P3)

**Goal**: Classify a supplied readable image with a saved compatible model.

**Independent test**: Run prediction using a known compatible checkpoint and a readable image, then try unreadable input and an incompatible checkpoint; verify one valid class or a clear failure respectively.

- [X] T017 [US3] Implement single-image CPU inference in `src/shape_classifier/predict.py`: decode and convert to RGB, apply the shared transform without augmentation, load strict checkpoint metadata/weights, and map the output through checkpoint class order `["circle", "rectangle", "triangle"]`.
- [X] T018 [US3] Add `predict IMAGE [--checkpoint PATH]` in `src/shape_classifier/__main__.py`, returning one class label and runtime details on success or a clear nonzero error for unreadable images and missing, corrupt or incompatible checkpoints.
- [X] T019 [US3] Validate prediction and negative cases using `specs/002-cnn-training-prediction/quickstart.md`; confirm prediction uses the same resize and scaling as training and evaluation and has no augmentation.

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T020 [P] Update `README.md` with classifier Docker commands, preserved generator invocation, default/override training and dataset seed flags, checkpoint path and portability, paired accuracy interpretation, tiny-demo caveat, and CPU reproducibility limits.
- [X] T021 Run the full Docker validation in `specs/002-cnn-training-prediction/quickstart.md`, including `pip check`, existing generator regression checks, CPU checkpoint round-trip, invalid inputs, shared preprocessing, augmentation boundaries, one-time cache, independent dataset seed metadata, and SC-004 repeat-run tolerance; resolve failures.

## Dependencies & Execution Order

- Setup T001 → T002 → T003 precedes the foundation. T004 and T005 are independent; T006 depends on T004; T007 depends on T005 and the checkpoint contract.
- After T005, validate the feature classifier model with a CPU forward pass before starting US1.
- US1 requires the foundation: T008 follows T006; T009 uses T004–T005 and T008; T010 follows T009; T011 requires T007 and T009; T012 integrates T009–T011; T013 validates the complete flow.
- US2 requires the shared data, model, checkpoint and paired assessment from US1; T014 → T015 → T016.
- US3 requires the shared model, preprocessing and checkpoint, and can begin after the foundation with an existing compatible checkpoint; T017 → T018 → T019. Since T012, T015 and T018 edit the same CLI file, integrate those changes sequentially even if other work is parallel.
- T020 may proceed once the CLI contract is stable. T021 follows all stories and documentation.

## Parallel Examples

- **US1**: T004 (`transforms.py`) and T005 (`model.py`) can proceed independently after setup.
- **US2**: Once shared components exist, evaluation implementation T014 can proceed independently of prediction implementation T017; sequence their later CLI edits.
- **US3**: T017 (`predict.py`) can proceed in parallel with T014 (`train.py`) after the foundation, using an existing compatible checkpoint for its independent test.

## Implementation Strategy

Complete setup and foundation, then deliver US1 as the MVP and validate paired accuracy plus a portable saved checkpoint. Add independent evaluation and prediction, preserve feature 001 behavior, then run the complete Docker validation. MPS and performance comparison are outside this feature.

## Phase 7: Convergence

- [X] T022 [P] Explain in `README.md` step 3 why repeated CPU runs may differ slightly despite fixed seeds (floating-point operation order and kernel selection vary with PyTorch build, CPU and thread count), and that this image pins one thread and deterministic algorithms so repeats in the same image are expected to match, per FR-014 (partial)
- [X] T023 [P] State in `README.md` step 3 that held-out accuracy is based on only 15 images, so each image changes it by about 6.7 percentage points, per FR-013 (partial)
- [X] T024 [P] Review the unrequested `.dockerignore` entries (`Dockerfile*`, `.dockerignore`, `node_modules/`) and `.gitignore` entries (`Thumbs.db`, `.vscode/`, `.idea/`); keep them only if intended, otherwise remove them, per plan: structure (unrequested)
