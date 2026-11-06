# CNN image classification project summary

## Goal

Build a small, local CNN project that classifies synthetic images of circles, rectangles, and triangles. Generate the images in advance. The project must run on a Mac with an M1 Pro and use [GitHub Spec Kit](https://github.com/github/spec-kit) to guide specification, planning, implementation, and verification.

## Dataset

### Sets

- **Training set:** **10 PNG images per class** (30 total), each at **1920 × 1080** resolution.
- **Held-out set (mandatory):** **5 PNG images per class** (15 total), same resolution, generated with a **different seed** from the training set. These images are never used for training.

### Shape definitions

- **Circle:** filled circle.
- **Rectangle:** filled rectangle with a random width and height. Any aspect ratio is allowed, **including squares**.
- **Triangle:** filled triangle with random vertices (equilateral, isosceles, or scalene), with **every interior angle at least about 20°** so no triangle becomes a thin sliver.
- All shapes are drawn **filled**, not as outlines.

### Variation

- Vary shape position, size, rotation, and color across every class so the model cannot rely on a class-specific color or location. Keep shapes large enough to remain visible after resizing to 256 × 144.
- Each image has a **random solid background color**.
- The shape color must meet a **minimum contrast** against the background (a set brightness/color distance threshold). If a randomly picked color is too close, pick another until it passes.

### Reproducibility

- Image generation uses **fixed default seeds**: one for the training set and a different one for the held-out set. Each seed can be overridden with a CLI flag.
- The same seed always produces exactly the same images.

## Evaluation

- Report **training-set accuracy**, which checks that the pipeline works but does not measure performance on new images.
- Always report **held-out accuracy** next to training accuracy. This is the number that shows whether the model learned the shapes or memorized the training images (chance level with 3 classes is about 33%).
- The small sets are intended as a learning demo, not evidence of robust real-world performance. With 5 images per class, each held-out image is about 6.7% of the score.

## Technical stack

The same code runs in two environments. Docker is the default; native macOS is an optional mode for using the M1 Pro GPU and comparing performance.

### Shared

- **Python 3.14, pinned to the same patch release (3.14.10) in both environments.** PyTorch 2.15 supports Python 3.11+; 3.14 is used for everything.
- Record the version in a `.python-version` file (`3.14.10`) and as `requires-python = "==3.14.*"` in `pyproject.toml`.
- PyTorch 2.15 and torchvision 0.29, Pillow for image generation, matplotlib for optional plots. Pin exact versions in one shared requirements/lock file used by both environments.

### Default: Docker (CPU)

- **All dependencies are installed and all code runs inside Docker.** The image is arm64 Linux, built and run on the M1 Pro with Docker Desktop, Colima, or a similar runtime (the Docker daemon must be running).
- Base image: the official `python:3.14.10-slim` image, pinned in the Dockerfile (optionally also by digest). Install the CPU build of PyTorch from the PyTorch CPU index (`torch==2.15.0+cpu`, Linux arm64 wheel for Python 3.14).
- **CPU only.** Docker on macOS runs Linux containers in a VM with no access to Apple's Metal GPU, so PyTorch's `mps` device is unavailable inside the container. For 30 images at 256 × 144 and a small CNN, CPU training is expected to take about a minute or less.
- Generated images, the held-out set, `shapes.pth`, and benchmark results are written to a host directory mounted into the container, so they persist after the container exits.
- The Docker VM may be allocated fewer CPU cores and less memory than the Mac itself; record this in benchmark results.

### Optional: native macOS (MPS or CPU)

- A native virtual environment on the Mac, created with a **`uv`-managed Python 3.14.10** (`uv python install 3.14.10`; `uv` reads `.python-version`), using the same pinned package versions. Do not use Homebrew's Python (currently 3.14.7), because Homebrew upgrades it automatically and would break the pin. The standard macOS arm64 PyTorch wheel includes MPS support.
- Requires macOS 15 or newer for MPS (PyTorch 2.15); this Mac runs macOS 27.0.1.
- Reads and writes the same project data directory as the Docker mode, so both modes can use the same generated images.

### Device selection

- Training, evaluation, and prediction accept `--device {auto,cpu,mps}`:
  - `auto` (default): use `mps` if available, otherwise `cpu`. Inside Docker this always resolves to `cpu`.
  - `cpu`: always CPU.
  - `mps`: use MPS; **fail with a clear error** if MPS is unavailable (for example inside Docker) instead of silently falling back to CPU.
- Log the resolved device, the environment (Docker or native), and the PyTorch and Python versions at the start of every run.

### Verified facts (2026-11-06)

- PyTorch 2.15.0 is the latest release on PyPI, with macOS arm64 wheels for Python 3.11–3.15; torchvision 0.29.2 ships one wheel for all Python 3 versions.
- Python 3.14 wheels exist for every dependency on both platforms: `torch 2.15.0` (macOS arm64, and `2.15.0+cpu` Linux aarch64 from the PyTorch CPU index), `pillow 13.0.0`, `matplotlib 3.11.2`, `numpy 2.5.4`.
- Docker Hub provides `python:3.14.10-slim` (latest 3.14 patch as of this date).
- PyTorch 2.15 requires Python 3.11+ and macOS 15+ for MPS ([release blog](https://pytorch.org/blog/pytorch-2-15-release-blog/)).

## Performance comparison

- Provide a way to compare the three configurations on the same data, seeds, model, epochs, and batch size:
  1. Docker, CPU
  2. Native, CPU
  3. Native, MPS
- Each training run records, in a machine-readable results file (JSON or CSV, one entry per run):
  - environment, device, PyTorch and Python versions, CPU thread count (and Docker VM CPU/memory allocation for Docker runs);
  - total training time and mean time per epoch, **excluding the first (warm-up) epoch**;
  - inference time per image on the held-out set;
  - final training loss, training accuracy, and held-out accuracy.
- MPS runs asynchronously, so call `torch.mps.synchronize()` before reading the timer; otherwise MPS times will look misleadingly fast.
- Provide a summary command that prints a comparison table from the results file.
- Report results honestly: with this tiny model and dataset, MPS may be **no faster or even slower** than CPU, because GPU launch and data-transfer overhead can outweigh the small amount of compute. That is a valid finding, not a bug.
- Accuracy may differ slightly between devices, because MPS and CPU arithmetic are not bit-identical.

## Image processing and model

### Preprocessing (shared by training and prediction)

- Keep the generated files at **1920 × 1080**. Before both training and prediction, resize them to **256 × 144** (width × height), preserving the 16:9 aspect ratio. This is a practical starting size for large, simple shapes; increase it to 320 × 180 only if important detail disappears.
- Set the size in the shared torchvision preprocessing transform as `Resize((144, 256))`, where the tuple is **height, width**.
- Pixel scaling: `ToImage()` → `ToDtype(torch.float32, scale=True)`, which maps pixels to **[0, 1]**. No additional normalization.
- The CNN receives RGB tensors shaped `(batch, 3, 144, 256)`.

### Data loading

- At the start of training, load and resize each image **once** and **cache the resulting tensors in memory** (about 13 MB for 30 images). Do not reread or resize from disk every epoch.

### Augmentation (training only)

- Apply **light augmentation** to the cached tensors each epoch: random rotation, random horizontal and vertical flips, and slight color jitter.
- Never apply augmentation at evaluation or prediction time.

### Model and training

- Start with a small CNN: two or three convolution/ReLU/pooling blocks, adaptive average pooling, and a three-output classifier. Use cross-entropy loss and Adam.
- Training uses a **fixed default seed** (applied to `torch`, `random`, and `numpy`), overridable with a CLI flag.
- With fixed seeds, CPU training in the same Docker image should be repeatable. Document that tiny differences are still possible (for example from multithreaded CPU kernels or a different image build), so results should be nearly identical rather than guaranteed bit-identical.
- MPS training is not guaranteed to be bit-identical between runs, even with fixed seeds, and will not exactly match CPU results.

## Saved result

- Save everything prediction needs in a **single `.pth` file**, such as `shapes.pth`, containing:
  - the model `state_dict`;
  - a metadata dictionary of plain data only (strings, numbers, lists): class order (`circle`, `rectangle`, `triangle`), input size (height 144, width 256), pixel scaling setting, the seeds used, the PyTorch version, and the environment and device used for training.
- Move the weights to CPU before saving, so a checkpoint trained on MPS loads in Docker (CPU) and vice versa without `map_location` tricks.
- The file must load with `torch.load(..., weights_only=True)`.
- Prediction also needs the matching CNN definition in code.
- A checkpoint from any environment can be used for prediction in any other environment and on any device.

## Spec Kit workflow

### Setup

- Use `specify-cli` **1.3.1** (latest on PyPI as of 2026-11-06; already installed locally). Install or upgrade with `uv tool install specify-cli`.
- Install **both** integrations so either Codex or Claude Code can drive the workflow:
  - `specify init <project> --integration claude`, then `specify integration install codex` inside the project.
  - Claude Code skills go to `.claude/skills/speckit-<command>/` and are invoked in Claude Code as `/speckit-<command>`.
  - Codex skills go to `.agents/skills/speckit-<command>/` and are invoked in Codex chat as `$speckit-<command>`.
- Skills are invoked in the agent chat, not as terminal commands. Both agents share the same `spec.md`, `plan.md`, and `tasks.md`, so use one agent at a time per step.

### Git conventions

All commits follow [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/). Branch creation and auto-commits are handled by Spec Kit's bundled **git extension** (`specify extension add git` if it is not already enabled), configured in `.specify/extensions/git/git-config.yml`.

**Branches**

- Format: **`feat/NNN-slug`** with **sequential** numbering, for example `feat/001-shape-classifier`, `feat/002-benchmark-report`.
- The slug is a 2–4 word name the agent derives from the feature description.
- Spec Kit requires the last path segment to start with the number (it links the branch to `specs/NNN-slug/`) and does not support a per-branch type, so the `feat/` prefix is fixed for all feature branches.

**Spec Kit git extension config**

```yaml
branch_numbering: sequential
branch_prefix: "feat"
init_commit_message: "chore: initialize project with Spec Kit"
commit_style: conventional        # agent writes type(scope): subject from the diff
auto_commit:
  default: false
  after_constitution: { enabled: true }
  after_specify:      { enabled: true }
  after_clarify:      { enabled: true }
  after_plan:         { enabled: true }
  after_tasks:        { enabled: true }
  after_analyze:      { enabled: true }
  after_implement:    { enabled: true }
```

- Every Spec Kit step commits when it finishes. `converge` has no hook of its own; implementation work in the implement ⇄ converge loop is committed by `after_implement`.

**Commit messages**

- Format: `type(scope): subject`, single-line subject in the imperative mood, optional body and footers.
- Allowed types (the `@commitlint/config-conventional` set): `feat`, `fix`, `docs`, `refactor`, `test`, `build`, `ci`, `chore`, `perf`, `style`, `revert`.
- Suggested scopes (optional, not enforced): `spec`, `plan`, `tasks`, `data`, `model`, `train`, `eval`, `predict`, `bench`, `docker`, `deps`.
- Breaking changes use `!` after the type/scope or a `BREAKING CHANGE:` footer. Trailers such as `Co-Authored-By:` are valid footers.
- Examples: `docs(spec): add shape classifier specification`, `feat(data): add synthetic shape generator`, `feat(train): add CNN training loop`, `build(docker): pin python:3.14.10-slim base image`.

**Enforcement**

- Record the convention in the **constitution** and in **`AGENTS.md`**, so Claude Code and Codex follow it for commits made outside Spec Kit hooks. Claude Code (v2.1.277+) reads `AGENTS.md` directly, so no `CLAUDE.md` is needed. Don't add one: a `CLAUDE.md` in this folder or any folder above it would stop Claude Code from reading `AGENTS.md`, unless it imports it with `@AGENTS.md`.
- Enforce it with the **pre-commit** framework (installed with `uv`) running the [`conventional-pre-commit`](https://github.com/compilerla/conventional-pre-commit) hook at the `commit-msg` stage, restricted to the allowed types above. Pin the hook's `rev` to its latest release. Install the hook with `pre-commit install --hook-type commit-msg`. No Node.js is required.

### Steps

Commands are shown in Claude Code form; in Codex, replace `/` with `$`.

1. `/speckit-constitution`: record simplicity, reproducibility, honest evaluation, and Conventional Commits principles.
2. `/speckit-specify`: capture the goal and requirements above.
3. `/speckit-clarify`: resolve any remaining ambiguity in the spec (most was resolved in this document, so this should be short).
4. `/speckit-plan`: stack and design (Docker CPU default, optional native MPS mode, device selection, benchmark recording, module layout).
5. `/speckit-tasks`: break the plan into tasks for image generation, training, evaluation, and prediction commands.
6. `/speckit-analyze`: read-only check that `spec.md`, `plan.md`, and `tasks.md` agree. Fix any issues at the source and re-run before implementing.
7. `/speckit-implement`: build the tasks.
8. `/speckit-converge`: check the codebase against the spec, plan, and tasks. If it finds gaps, it appends tasks to `tasks.md`. Repeat implement → converge until it reports **Converged**.

## References

- [Spec Kit quickstart](https://github.github.io/spec-kit/quickstart.html), [installation](https://github.github.io/spec-kit/installation.html), [Codex integration](https://github.github.io/spec-kit/integrations/codex.html), and [Claude Code integration](https://github.github.io/spec-kit/integrations/claude.html)
- [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) and [conventional-pre-commit](https://github.com/compilerla/conventional-pre-commit)
- [PyTorch 2.15 release blog](https://pytorch.org/blog/pytorch-2-15-release-blog/) (Python 3.11+ and macOS 15+ for MPS) and [MPS backend notes](https://docs.pytorch.org/docs/stable/notes/mps.html)
- [torchvision Resize](https://docs.pytorch.org/vision/main/generated/torchvision.transforms.v2.Resize.html) and [PyTorch model saving](https://docs.pytorch.org/tutorials/beginner/saving_loading_models.html)
