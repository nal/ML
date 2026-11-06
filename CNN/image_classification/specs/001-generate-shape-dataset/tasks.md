---
description: "Implementation tasks for synthetic shape dataset generation"
---

# Tasks: Generate Synthetic Shape Dataset

**Input**: `specs/001-generate-shape-dataset/` design documents and specification.
**Format**: `[ID] [P?] [Story] Description`; `[P]` denotes independent work on different files.

## Phase 1: Setup

- [X] T001 Create `pyproject.toml` with `requires-python = "==3.14.*"`, package discovery for `src/shape_dataset`, and `.python-version` pinned to 3.14.10.
- [X] T002 [P] Pin Pillow 13.0.0 in the single shared dependency file `requirements.txt`.
- [X] T003 Create `Dockerfile` from `python:3.14.10-slim`, install `requirements.txt` and the package, include `tests/`, and set the CLI entrypoint with `/data` as default output.

## Phase 2: Foundational

- [X] T004 Create `src/shape_dataset/__init__.py` and `src/shape_dataset/config.py`: roles `train` and `held-out`, classes `circle`, `rectangle`, `triangle`, 10 and 5 images per class, RGB 1920 × 1080, and integer default seeds 42 and 43.

## Phase 3: User Story 1 — Generate both datasets (P1, MVP)

**Goal**: Generate both sets with measurable variation, preserve unrelated files and recover interrupted publication.

**Independent test**: Run the default container with a writable mounted directory; verify 45 correctly organized images, geometric and contrast constraints, variation and safe repeat runs, including interrupted publication recovery.

### Validation checks

- [X] T005 [P] [US1] Create geometry and color checks in `tests/test_geometry.py` for contained filled shapes, triangles ≥20°, inscribed disk radius ≥120 pixels, square support, and sRGB contrast ≥3:1.
- [X] T006 [P] [US1] Create output and recovery checks in `tests/test_output.py` covering unrelated files, untracked collisions, invalid manifests and journals, traversal and symlink rejection, unexpected modified files, and interruption before and after each publication mutation on first and repeat runs.
- [X] T007 [P] [US1] Create default generation checks in `tests/test_generation.py` for readable RGB 1920 × 1080 PNGs, 10 training and 5 held-out images per class, and each set/class having at least two bounding-box centers, sizes and foreground colors, plus two distinct symmetry-normalized orientations for rectangles and triangles.

### Implementation

- [X] T008 [P] [US1] Implement random background and foreground selection and sRGB relative-luminance contrast ≥3:1 with rejection and resampling in `src/shape_dataset/colors.py`, without class-specific palettes.
- [X] T009 [P] [US1] Implement sampling in `src/shape_dataset/geometry.py`: fully contained circles, rectangles including squares with nonzero probability, and triangles with every angle ≥20°; each shape contains an inscribed disk of radius ≥120 source pixels; sample positions, size and rotation without class-specific regions.
- [X] T010 [US1] Implement RGB drawing and deterministic `SET/CLASS/NN.png` names in `src/shape_dataset/generate.py`, producing 10 training and 5 held-out images per class; deterministically resample until each set/class has at least two distinct raster-space bounding-box centers, bounding-box dimensions and foreground colors and, for rectangles and triangles, two orientations normalized for geometric symmetry.
- [X] T011 [P] [US1] Implement validated ownership manifest and recovery journal in `src/shape_dataset/output.py`: unique relative image paths limited to expected set/class directories; reject traversal, symlinks, malformed or duplicate entries and untracked destination collisions; stage images and atomically install the versioned journal before destination mutations.
- [X] T012 [US1] Implement process-released advisory locking and idempotent transaction recovery in `src/shape_dataset/output.py`: record prior absent or owned digest, desired digest, staged paths and stale owned digests; resume only when destination content matches prior or desired state, preserve unrelated files, atomically publish the manifest, then clean up journal and staging; fail clearly for unexpected changes or invalid recovery data.
- [X] T013 [US1] Connect generation, recovery, staging, publication and error reporting in `src/shape_dataset/__main__.py`; accept `--output-dir` defaulting to `/data`, report counts on success and return nonzero on invalid input or filesystem failure.
- [X] T014 [US1] Run the default-only checkpoint and US1 checks in `specs/001-generate-shape-dataset/quickstart.md` and `tests/` after T008–T013; verify success and repair any failures without requiring US2 flags.

## Phase 4: User Story 2 — Reproduce or vary datasets (P2)

**Goal**: Reproduce PNG bytes in the same pinned environment and independently override set seeds.

**Independent test**: Generate in separate empty directories using matching seeds, then change each seed independently and compare corresponding image bytes; verify equal and invalid seeds fail.

### Validation checks

- [X] T015 [P] [US2] Create CLI and reproducibility checks in `tests/test_reproducibility.py` for byte-identical matching seeds, independent changes for each set, fixed defaults, invalid integer input and equal-seed rejection.

### Implementation

- [X] T016 [P] [US2] Add integer `--train-seed` and `--held-out-seed` flags to `src/shape_dataset/__main__.py`, defaulting to 42 and 43, and reject equal or invalid seeds with clear errors.
- [X] T017 [P] [US2] Use separate `random.Random` streams per set, fixed traversal and fixed PNG save settings in `src/shape_dataset/generate.py`, including deterministic variation resampling, so changing one set seed never changes the other set's bytes.
- [X] T018 [US2] Run the seed and reproducibility checks in `tests/test_reproducibility.py` against the pinned Docker environment after T016 and T017.

## Phase 5: Polish & Cross-Cutting Concerns

- [X] T019 [P] Document Docker invocation, seed flags, layout, contrast and geometry thresholds, variation, safe reruns, interruption recovery, power-loss limitation and demo scope in `README.md`.
- [X] T020 Run the full Docker build and validation in `specs/001-generate-shape-dataset/quickstart.md`, including `tests/`, and correct any discrepancies.

## Dependencies & Execution Order

- Setup T001–T003 precedes T004; T001 and T002 are independent, and T003 requires T002.
- US1 validation checks T005–T007 can be authored independently after setup. T008, T009 and T011 can proceed independently after T004. T010 depends on T008 and T009; T012 follows T011; T013 integrates T010 and T012; T014 follows all US1 work.
- US2 follows the US1 generator. T015, T016 and T017 use separate files and can proceed concurrently after US1; T018 follows all three.
- T019 can proceed once the CLI and recovery contract is stable; T020 follows both stories and documentation.

## Parallel Examples

- **US1**: T005–T007 create independent checks; T008, T009 and T011 implement independent modules.
- **US2**: T015, T016 and T017 address separate files after the US1 checkpoint.

## Implementation Strategy

Complete setup and foundation, then deliver US1 as the MVP and verify both required datasets and recovery. Add US2 seed overrides and reproducibility, then run the complete Docker validation and finish documentation. Training, evaluation and MPS remain out of scope.

## Phase 6: Convergence

- [X] T021 CRITICAL: Add a Complexity Tracking table entry to `specs/001-generate-shape-dataset/plan.md` for the manifest, recovery journal, advisory lock and staging layer in `src/shape_dataset/output.py`, naming the simpler alternative that was rejected (for example replacing `SET/CLASS/NN.png` files in place) and why per Constitution I (contradicts)
- [X] T022 Restore the project `README.md` from `main` (status, workflow, feature steps, reference) and add the generator documentation required by T019 (Docker invocation, seed flags, layout, contrast and geometry thresholds, variation, safe reruns, interruption recovery, power-loss limitation, demo scope) as a section within it, instead of replacing the file per T019 (contradicts)
- [X] T023 [P] Normalize square orientations modulo π/2 (non-square rectangles modulo π, triangles modulo 2π) in the variation check in `src/shape_dataset/generate.py` per FR-004 (partial)
- [X] T024 [P] Assert at least two distinct symmetry-normalized orientations (not raw angles) for rectangles and triangles in `tests/test_generation.py` per T007 (partial)
- [X] T025 [P] Add tests to `tests/test_output.py` for a well-formed journal with an invalid digest or path, and for an unwritable output directory returning nonzero with a clear error per T006 and FR-010 (partial)

## Phase 7: Convergence

- [X] T026 Add a seed-override example (for example `docker run --rm -v "$PWD/data:/data" shape-dataset --train-seed 123 --held-out-seed 456`) to the generator code block in `README.md` section 2.5, or remove the sentence claiming the commands show how to override either seed, per T022 (partial)
