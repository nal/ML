# CNN Shape Classifier Constitution

## Core Principles

### I. Simplicity

- The project MUST use the smallest design that meets the current feature's spec.
- Speculative features, abstractions, configuration options, or dependencies not required by a spec
  MUST NOT be added.
- Any added complexity (extra layer, service, dependency, or framework) MUST be justified in the
  plan's Complexity Tracking table, together with the simpler alternative that was rejected.

**Rationale**: this is a small learning project; every extra moving part makes it harder to
understand what the CNN and the pipeline actually do.

### II. Reproducibility

- Every source of randomness (image generation for each dataset split, augmentation, weight
  initialization, data order) MUST be driven by a fixed default seed that can be overridden from
  the command line.
- The same seeds MUST produce byte-identical generated images.
- Python MUST be pinned to 3.14.10, and every dependency MUST be pinned to an exact version in a
  single shared lock or requirements file.
- Docker MUST be the default runtime. Documented application commands MUST work inside the Docker
  image, except commands explicitly identified as optional native macOS execution. Commands for
  host administration and host-side launchers MUST be identified as host commands and need not run
  inside the Docker image.
- Known limits of reproducibility (for example MPS and multithreaded CPU kernels are not
  bit-identical) MUST be documented rather than hidden.

**Rationale**: results are only meaningful if anyone can regenerate the same data and get the same
(or documented, near-identical) outcome.

### III. Honest Evaluation

- Held-out accuracy MUST always be reported next to training accuracy, wherever accuracy is reported.
- Held-out images MUST NOT be used for training, augmentation, or model selection.
- Training-set accuracy MUST NOT be presented as evidence of generalization.
- Performance and benchmark results MUST be reported as measured, including results where the
  expected faster option (for example MPS) is slower or no better.
- Documentation MUST state that the dataset is a small synthetic demo, not evidence of real-world
  performance.

**Rationale**: with 30 training images a model can reach 100% training accuracy by memorization;
only honest, separate reporting shows what was actually learned.

### IV. Shared Preprocessing

- Training, evaluation, and prediction MUST use one shared preprocessing definition (resize, pixel
  conversion, scaling); it MUST NOT be duplicated per command.
- Augmentation MUST be applied only during training, never during evaluation or prediction.
- The preprocessing settings and class order needed for prediction MUST be stored with the saved
  model.

**Rationale**: a mismatch between training-time and prediction-time preprocessing silently breaks
predictions; a single definition makes that mistake impossible.

### V. Conventional Commits

- Every commit MUST follow Conventional Commits 1.0.0 with one of the allowed types (`feat`, `fix`,
  `docs`, `refactor`, `test`, `build`, `ci`, `chore`, `perf`, `style`, `revert`), as described in
  `AGENTS.md`.
- The `commit-msg` hook MUST NOT be bypassed (no `--no-verify`).
- Each commit SHOULD contain one logical change.

**Rationale**: a consistent, machine-checkable history makes each step of the Spec Kit workflow
easy to review and revert.

## Technical Constraints

- Runtime: Docker (arm64 Linux, `python:3.14.10-slim`), CPU only by default. An optional native
  macOS mode MAY use MPS; it MUST use the same code and pinned dependency versions.
- Device selection: an explicitly requested device that is unavailable MUST fail with a clear error
  instead of silently falling back.
- Stack: PyTorch and torchvision for the model, training, and prediction; Pillow for image
  generation; matplotlib only for optional plots. New dependencies require justification under
  Principle I.
- Saved model: a single `.pth` file with the state dict (saved from CPU) and plain-data metadata,
  loadable with `torch.load(..., weights_only=True)`.
- Source of truth for requirements: `CNN_image_classification_research.md`. Specs MAY refine it;
  conflicts MUST be resolved by updating one of the two documents, not by ignoring it.

## Development Workflow

- Work is delivered as Spec Kit features on `feat/NNN-slug` branches created by `/speckit-specify`;
  branches MUST NOT be renamed.
- Each feature follows: specify → clarify → plan → tasks → analyze → implement ⇄ converge.
- `/speckit-analyze` issues MUST be resolved before `/speckit-implement`.
- A feature is complete only when `/speckit-converge` reports **Converged** and the feature's
  documented checks (for example dataset counts, reproducibility, accuracy reporting) pass.
- Only one agent (Claude Code or Codex) MUST run a given Spec Kit step at a time.
- Features are merged into `main` through a pull request.

## Governance

- This constitution takes precedence over other project practices. `AGENTS.md` provides runtime
  guidance for coding agents and MUST stay consistent with it.
- Amendments are made with `/speckit-constitution`, committed as `docs: amend constitution to
  vX.Y.Z (…)`, and reviewed in a pull request.
- Versioning follows semantic versioning:
  - MAJOR: a principle is removed or redefined in a backward-incompatible way.
  - MINOR: a principle or section is added or materially expanded.
  - PATCH: clarifications and wording fixes with no change in meaning.
- Every plan MUST pass the Constitution Check gate before Phase 0 research and again after design.
  Reviewers MUST verify compliance in each pull request; violations MUST be fixed or justified in
  the plan's Complexity Tracking table.

**Version**: 2.0.0 | **Ratified**: 2026-11-06 | **Last Amended**: 2026-11-07
