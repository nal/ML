# CNN Shape Classifier

A small learning project: a convolutional neural network (CNN) that classifies synthetic images of **circles, rectangles, and triangles**. It runs locally on a Mac with an M1 Pro, inside Docker by default, and is built step by step with [GitHub Spec Kit](https://github.com/github/spec-kit).

- **Requirements and decisions:** [`CNN_image_classification_research.md`](CNN_image_classification_research.md)
- **Rules for coding agents** (Claude Code and Codex): [`AGENTS.md`](AGENTS.md)

---

## Contents

1. [Current status](#1-current-status)
2. [How the work is organized](#2-how-the-work-is-organized)
3. [Before every working session](#3-before-every-working-session)
4. [Step 1 — Project constitution (once)](#4-step-1--project-constitution-once)
5. [Step 2 — Feature 001: generate the dataset](#5-step-2--feature-001-generate-the-dataset)
6. [Step 3 — Feature 002: train and evaluate the CNN](#6-step-3--feature-002-train-and-evaluate-the-cnn)
7. [Step 4 — Feature 003: MPS and performance comparison](#7-step-4--feature-003-mps-and-performance-comparison)
8. [Reference](#8-reference)

---

## 1. Current status

**Done**

- [x] Requirements researched and decided (`CNN_image_classification_research.md`)
- [x] Spec Kit 1.3.1 set up with **Claude Code** (default) and **Codex**
- [x] Spec Kit git extension set up: `feat/NNN-slug` branches, Conventional Commit auto-commits
- [x] Commit-message hook (pre-commit + conventional-pre-commit) installed and tested
- [x] Agent rules written in `AGENTS.md`
- [x] Step 1: project constitution v1.0.0 (`.specify/memory/constitution.md`)

**To do**

- [ ] Step 2: feature 001, generate the dataset
- [ ] Step 3: feature 002, train and evaluate the CNN
- [ ] Step 4: feature 003, MPS and performance comparison

---

## 2. How the work is organized

The project is built as **three features**, one after another. Each feature gets its own branch and its own folder under `specs/`.

| Step | Feature | Branch | What it delivers |
|---|---|---|---|
| 2 | 001 | `feat/001-shape-dataset` | Docker environment and the image generator (training and held-out sets) |
| 3 | 002 | `feat/002-cnn-training` | Preprocessing, CNN, training, evaluation, saved model, prediction |
| 4 | 003 | `feat/003-device-benchmark` | Optional native MPS (Mac GPU) mode, `--device` flag, speed comparison |

Every feature goes through the same Spec Kit cycle:

```
specify → clarify → plan → tasks → analyze → implement ⇄ converge → merge
```

| Spec Kit step | What it does |
|---|---|
| `specify` | Creates the feature branch and writes `spec.md`: *what* to build |
| `clarify` | Asks a few questions to remove ambiguity from the spec |
| `plan` | Writes `plan.md`: *how* to build it |
| `tasks` | Breaks the plan into `tasks.md` |
| `analyze` | Read-only check that spec, plan, and tasks agree |
| `implement` | Writes the code, task by task |
| `converge` | Compares the code with the spec; adds tasks for anything missing |

Each step auto-commits with a Conventional Commit message, for example `docs(spec): add shape dataset specification`.

> **Claude Code or Codex?** Both work. Commands below are written for Claude Code (`/speckit-…`). In Codex, replace `/` with `$` (`$speckit-…`). Use only one agent per step.

---

## 3. Before every working session

1. **Open a terminal in this folder:** `CNN/image_classification`.
2. **Start the Docker daemon** (Docker Desktop or Colima). Check with:

   ```bash
   docker info >/dev/null && echo "Docker is running"
   ```

3. **Start a new Claude Code (or Codex) session in this folder**, so it reads `AGENTS.md`.

**New clone or new machine only:** install the commit-message hook once, from the `ML/` repository root:

```bash
uv tool install pre-commit
pre-commit install --hook-type commit-msg -c CNN/image_classification/.pre-commit-config.yaml
```

---

## 4. Step 1 — Project constitution (once)

The constitution records the project's principles. Spec Kit checks every later spec and plan against it.

> **Optional:** the constitution auto-commit lands on the current branch. If you don't want it on `main`, create a branch first (for example `git switch -c chore/speckit-constitution`).

**Run:**

```
/speckit-constitution Principles for a small learning project:
1. Simplicity: smallest design that meets the spec; no speculative features.
2. Reproducibility: fixed, overridable seeds; pinned Python 3.14.10 and package versions; Docker as the default runtime.
3. Honest evaluation: always report held-out accuracy next to training accuracy; never present training accuracy as generalization; report performance results even when unfavorable.
4. Shared preprocessing: training and prediction use one preprocessing definition.
5. Conventional Commits 1.0.0 for all commits, as described in AGENTS.md.
Use CNN_image_classification_research.md as the source of truth for requirements.
```

**Done when:**

- [x] `.specify/memory/constitution.md` contains the five principles
- [x] A commit like `docs: add project constitution` was created and passed the commit hook

---

## 5. Step 2 — Feature 001: generate the dataset

**Goal:** a Docker image that generates 30 training images and 15 held-out images, reproducibly from seeds.

### 2.1 Specify

```
/speckit-specify Generate the synthetic shape dataset, as defined in the
"Dataset" section of CNN_image_classification_research.md: a training set of
10 images per class and a mandatory held-out set of 5 images per class
(circle, rectangle, triangle), PNG at 1920x1080, filled shapes, random
position/size/rotation/color, random solid background with minimum contrast,
squares allowed as rectangles, triangles with every angle >= ~20 degrees,
fixed default seeds (different for training and held-out) overridable by
CLI flags. Runs inside Docker (python:3.14.10-slim, pinned dependencies)
and writes images to a host-mounted data directory, one folder per set and
class. Out of scope: training, evaluation, MPS.
```

Creates the branch `feat/001-shape-dataset` and `specs/001-shape-dataset/spec.md`.

### 2.2 Clarify

```
/speckit-clarify
```

Most questions are already answered in the research file, so this should be short. One open question you may be asked: **should generated images be committed to git?** Recommended answer: **no**. Add `data/` to `.gitignore`, because the images can be regenerated exactly from the seeds.

### 2.3 Plan, tasks, analyze

```
/speckit-plan Use the "Technical stack" section of CNN_image_classification_research.md: Docker CPU runtime, uv-managed pinned dependencies with pyproject.toml and .python-version 3.14.10, Pillow for drawing. Plan only what feature 001 needs.
/speckit-tasks
/speckit-analyze
```

If `analyze` reports problems, fix them in `spec.md` or `plan.md` and run `/speckit-analyze` again before implementing.

### 2.4 Implement and converge

```
/speckit-implement
/speckit-converge
```

Repeat `implement` → `converge` until converge reports **Converged**.

### 2.5 Generate and check the dataset

The exact commands are defined by the plan. They will look roughly like this:

```bash
docker build -t shapes .
docker run --rm -v "$PWD/data:/app/data" shapes generate             # training + held-out sets
docker run --rm -v "$PWD/data:/app/data" shapes generate --seed 123   # seed override example
```

**Check the result:**

| Check | How |
|---|---|
| Image counts | `data/train/<class>/` has 10 PNGs each; `data/heldout/<class>/` has 5 each |
| Resolution | `sips -g pixelWidth -g pixelHeight data/train/circle/*.png \| head` shows 1920 × 1080 |
| Reproducible | Generate twice with the same seeds; `shasum data/train/*/*.png` gives identical results |
| Looks right | `open data/train/triangle/*.png`: shapes are filled, visible, and stand out from the background |

### 2.6 Finish

- [ ] All checks above pass
- [ ] `/speckit-converge` reports **Converged**
- [ ] Merge `feat/001-shape-dataset` into `main`

---

## 6. Step 3 — Feature 002: train and evaluate the CNN

**Goal:** train the CNN in Docker on the training set, report training and held-out accuracy, save `shapes.pth`, and predict new images.

**Requires:** feature 001 merged into `main`. Start from an up-to-date `main` (`git switch main && git pull`).

### 3.1 Specify

```
/speckit-specify Train, evaluate, and use a small CNN on the dataset from
feature 001, as defined in the "Evaluation", "Image processing and model",
and "Saved result" sections of CNN_image_classification_research.md:
shared preprocessing (Resize((144, 256)), ToImage, ToDtype float32 scaled to
[0, 1]), images loaded and resized once and cached in memory, light
training-only augmentation (rotation, flips, slight color jitter), a CNN with
2-3 conv/ReLU/pool blocks + adaptive average pooling + 3-class output,
cross-entropy loss and Adam, fixed overridable training seed. Report training
accuracy and held-out accuracy side by side. Save a single shapes.pth with
the state_dict (moved to CPU) and plain-data metadata (class order, input
size, scaling, seeds, PyTorch version, environment, device), loadable with
weights_only=True. Provide train, evaluate, and predict commands, running in
Docker on CPU. Out of scope: MPS and performance comparison.
```

Creates the branch `feat/002-cnn-training`.

### 3.2 Clarify, plan, tasks, analyze

```
/speckit-clarify
/speckit-plan Reuse the Docker image and project layout from feature 001. Add torch 2.15.0+cpu and torchvision 0.29 as pinned dependencies. Keep the model definition and preprocessing in modules shared by train, evaluate, and predict.
/speckit-tasks
/speckit-analyze
```

Questions `clarify` may raise: the **number of epochs** and **batch size** (recommended defaults: about 30 epochs, batch size 8, both overridable by CLI flags), and the **output format** of predictions (recommended: class name and confidence per image).

### 3.3 Implement and converge

```
/speckit-implement
/speckit-converge
```

Repeat until **Converged**.

### 3.4 Train, evaluate, and predict

Exact commands come from the plan. Roughly:

```bash
docker build -t shapes .
docker run --rm -v "$PWD/data:/app/data" shapes train
docker run --rm -v "$PWD/data:/app/data" shapes evaluate
docker run --rm -v "$PWD/data:/app/data" shapes predict data/heldout/triangle/<file>.png
```

**Check the result:**

| Check | Expected |
|---|---|
| Training accuracy | Close to 100% (this only proves the pipeline works) |
| Held-out accuracy | Reported next to training accuracy. Well above 33% (chance level) means the model learned the shapes. With 15 images, each image is about 6.7%. |
| Saved model | `data/shapes.pth` (or the path the plan chose) exists and loads with `weights_only=True` |
| Reproducible | Training twice with the same seed gives nearly identical accuracy |
| Prediction | Prints a class name (and confidence) for an image the model has not trained on |

### 3.5 Finish

- [ ] All checks above pass
- [ ] `/speckit-converge` reports **Converged**
- [ ] Merge `feat/002-cnn-training` into `main`

---

## 7. Step 4 — Feature 003: MPS and performance comparison

**Goal:** run the same training natively on the Mac's GPU (MPS) and compare speed across Docker CPU, native CPU, and native MPS.

**Requires:** feature 002 merged into `main`.

### 4.1 One-time native setup (outside Docker)

This step uses Python directly on the Mac, because Docker cannot use the Mac's GPU.

```bash
uv python install 3.14.10   # uv reads .python-version
uv sync                     # creates .venv with the pinned dependencies
uv run python -c "import torch; print(torch.__version__, torch.backends.mps.is_available())"
```

The last command should print `2.15.0 True`. If it prints `False`, MPS is not available and this feature cannot be tested.

### 4.2 Specify

```
/speckit-specify Add an optional native macOS mode and a device performance
comparison, as defined in the "Technical stack" (native macOS and device
selection) and "Performance comparison" sections of
CNN_image_classification_research.md: a uv-managed native environment using
the same pinned versions, a --device {auto,cpu,mps} flag on train, evaluate,
and predict (auto prefers MPS; mps fails clearly if unavailable, never
silently falls back), torch.mps.synchronize() before reading timers,
recording per-run results (environment, device, versions, thread count,
Docker CPU/memory allocation, total and per-epoch training time excluding
the first epoch, inference time per image, loss, training and held-out
accuracy) to a JSON or CSV file, and a summary command that prints a
comparison table for Docker CPU, native CPU, and native MPS. Docker remains
the default runtime.
```

Creates the branch `feat/003-device-benchmark`.

### 4.3 Clarify, plan, tasks, analyze

```
/speckit-clarify
/speckit-plan Keep Docker as the default runtime. The native mode reuses the same code and pyproject.toml; it must not require a different dependency set. The default PyPI torch wheel is used natively (it includes MPS), the CPU wheel in Docker.
/speckit-tasks
/speckit-analyze
```

### 4.4 Implement and converge

```
/speckit-implement
/speckit-converge
```

Repeat until **Converged**.

### 4.5 Run the comparison

Exact commands come from the plan. Roughly:

```bash
docker run --rm -v "$PWD/data:/app/data" shapes train --device cpu   # 1. Docker, CPU
uv run shapes train --device cpu                                     # 2. Native, CPU
uv run shapes train --device mps                                     # 3. Native, MPS
uv run shapes benchmark-summary                                      # comparison table
```

**Check the result:**

| Check | Expected |
|---|---|
| Three runs recorded | The results file has one entry each for Docker CPU, native CPU, and native MPS |
| `--device mps` in Docker | Fails with a clear error (no silent CPU fallback) |
| Fair timing | Same seeds, epochs, and batch size in all three runs; first epoch excluded |
| Honest result | With this tiny model, MPS may be **no faster or even slower** than CPU. That is a valid result. |
| Accuracy | Similar across devices; small differences are expected, because MPS and CPU math are not bit-identical |

### 4.6 Finish

- [ ] All checks above pass
- [ ] `/speckit-converge` reports **Converged**
- [ ] Merge `feat/003-device-benchmark` into `main`
- [ ] Update [Current status](#1-current-status)

---

## 8. Reference

### Project layout

| Path | What it is |
|---|---|
| `CNN_image_classification_research.md` | Requirements and decisions (source of truth) |
| `AGENTS.md` | Rules for Claude Code and Codex (read automatically) |
| `.specify/` | Spec Kit scripts, templates, constitution, git extension config |
| `.claude/skills/` | Spec Kit skills for Claude Code (`/speckit-*`) |
| `.agents/skills/` | Spec Kit skills for Codex (`$speckit-*`) |
| `.pre-commit-config.yaml` | Commit-message hook config |
| `specs/NNN-slug/` | Spec, plan, and tasks for each feature (created by Spec Kit) |

### Branches and commits

- Branches: `feat/NNN-slug`, created by `/speckit-specify`. Don't rename them: the number links a branch to its `specs/` folder.
- Commits: [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/), `type(scope): subject`.
  - Types: `feat`, `fix`, `docs`, `refactor`, `test`, `build`, `ci`, `chore`, `perf`, `style`, `revert`.
  - Suggested scopes: `spec`, `plan`, `tasks`, `data`, `model`, `train`, `eval`, `predict`, `bench`, `docker`, `deps`.
- The commit hook rejects messages that don't follow the format. Fix the message and commit again; never use `--no-verify`.

Full details: [`AGENTS.md`](AGENTS.md).

### Troubleshooting

| Problem | Fix |
|---|---|
| `Cannot connect to the Docker daemon` | Start Docker Desktop or Colima |
| Commit rejected: `Bad commit message` | Rewrite it as `type(scope): subject` with an allowed type |
| Agent doesn't follow `AGENTS.md` | Start a new session in this folder. Don't add a `CLAUDE.md`: it would stop Claude Code from reading `AGENTS.md` (unless it contains `@AGENTS.md`). |
| `/speckit-…` command not found | Make sure the session was started in `CNN/image_classification` |
| `torch.backends.mps.is_available()` is `False` natively | Requires macOS 15+ and the native (not Docker) environment |
