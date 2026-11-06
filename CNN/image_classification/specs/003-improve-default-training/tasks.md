---
description: "Implementation tasks for an evidence-informed training default"
---

# Tasks: Improve Default Training

**Input**: `specs/003-improve-default-training/` specification, plan, research, data model, CLI contract and quickstart.

**Format**: `- [ ] Tnnn [P?] [USn?] action with path`. `[P]` identifies work on separate files with no unfinished dependencies; comparison runs must be sequential to avoid timing interference.

## Phase 1: Setup

- [X] T001 Build the existing CPU image from `Dockerfile` and generate a fresh isolated host-mounted dataset per `specs/003-improve-default-training/quickstart.md` with generator seeds 42 and 43; preserve existing user data.
- [X] T002 Preserve a compatible feature 002 checkpoint in an isolated validation location or preserve the unchanged feature 002 image from `Dockerfile` if no checkpoint is available; do not generate a checkpoint or evaluate held-out data before the selection is frozen.

## Phase 2: Foundational

- [X] T003 Create `specs/003-improve-default-training/comparison.md` before candidate runs, recording the predeclared 30/60/120 candidates, seed 42, batch size 8, fixed settings and decision rule: shortest candidate with at least 3 additional correct training predictions and loop time at most four times the 30-epoch baseline, else 30.
- [X] T004 Build a temporary training-only harness under a temporary directory using `src/shape_classifier/train.py`, `src/shape_classifier/data.py`, `src/shape_classifier/model.py` and `src/shape_classifier/transforms.py` as references; mirror seeding, loader, augmentation, optimizer and CPU settings; verify it cannot read held-out images or overwrite user checkpoints.
- [X] T005 Run the 30-, 60- and 120-epoch candidates sequentially in the same Docker image using the harness from T004; retain each candidate’s weights, integer training correct count, monotonic epoch-loop time and status in private temporary storage without printing or publishing unpaired training counts or accuracy; record generator seeds, sorted training PNG paths and SHA-256 digests, image ID, Python/PyTorch versions and settings in `specs/003-improve-default-training/comparison.md`; resolve failures before selection.
- [X] T006 Apply the predeclared rule and freeze the selected epoch count and timestamp, without training counts, in `specs/003-improve-default-training/comparison.md` before any new held-out evaluation; document that the earlier feature 002 held-out result is already known and was excluded from the decision.

- [X] T007 After T006 is frozen, evaluate each privately retained candidate on both splits and publish each candidate’s paired training and held-out correct/total counts and accuracies, loop time and selection rationale in `specs/003-improve-default-training/comparison.md`; confirm training counts match the private measurements, and stop on mismatch without revising the selection based on held-out results.

## Phase 3: User Story 1 — Train with an evidence-informed default (Priority: P1, MVP)

**Goal**: Use the selected default consistently, save a usable checkpoint and report paired results.

**Independent test**: Run default training twice on the same fixed data and image; verify the selected count, persisted checkpoint, paired 30/15 counts and reproducibility tolerance.

- [X] T008 [US1] Apply the T006 selected count consistently to the default arguments in `src/shape_classifier/train.py` and `src/shape_classifier/__main__.py`, retaining 30 if no longer candidate qualifies; preserve architecture, preprocessing, augmentation, seed and checkpoint behavior.
- [X] T009 [US1] Rebuild `Dockerfile` and execute the default training flow twice per `specs/003-improve-default-training/quickstart.md`; verify both report paired 30/15 correct counts and accuracies, persist distinct CPU checkpoints, and differ by at most one correct image per split; record paired final results in `specs/003-improve-default-training/comparison.md` after the frozen decision.
- [X] T010 [US1] If no legacy checkpoint was preserved, generate one only after T006 using the unchanged feature 002 image preserved in T002; validate evaluation and prediction with that checkpoint and the new checkpoint using `specs/003-improve-default-training/contracts/cli.md`; confirm compatible loading, paired evaluation, supported prediction and preserved generator entrypoint.

## Phase 4: User Story 2 — Control and understand training duration (Priority: P2)

**Goal**: Preserve positive epoch overrides and document the actual default and training-time tradeoff.

**Independent test**: Run explicit 30 and another positive epoch count, reject zero, negative and non-integer counts, and find the chosen default and timing comparison in the instructions.

- [X] T011 [P] [US2] Verify CLI and Python training defaults agree with T006 and that explicit 30 and another positive `--epochs` value are honored while zero, negative and non-integer values fail without a success result, using `src/shape_classifier/__main__.py` and `src/shape_classifier/train.py`.
- [X] T012 [P] [US2] Update `README.md` step 3 with the selected default, `--epochs` override, actual measured epoch-loop time tradeoff from `specs/003-improve-default-training/comparison.md`, small synthetic dataset caveat, 15-image held-out limitation and previously observed held-out result limitation.

## Phase 5: Polish & Cross-Cutting Concerns

- [X] T013 Run the existing Docker unittest suite and `pip check` per `specs/003-improve-default-training/quickstart.md`; resolve regressions and verify no user-facing training accuracy appears without held-out accuracy.
- [X] T014 Review `specs/003-improve-default-training/comparison.md` against `specs/003-improve-default-training/data-model.md` and the decision rule, confirm README and both defaults match the frozen decision, and verify all acceptance scenarios and checkpoints remain valid.

## Dependencies & Execution Order

- T001 and T002 prepare separate validation inputs; complete both before the comparison.
- T003 → T004 → T005 → T006 → T007 is mandatory: do not inspect any new candidate held-out results before the selection is recorded. Candidate timing runs are sequential.
- US1 follows T007: T008 → T009 → T010. US2 follows the frozen selection and default integration: T011 and T012 can proceed independently after T008, but story validation completes after both.
- T013 and T014 follow both stories. Resolve any failure before marking its task complete.

## Parallel Examples

- **US1**: The changes to the two default definitions in T008 can be prepared separately only after T006; integrate and verify them together before T009. Candidate runs must not overlap.
- **US2**: After T008, T011 validation and T012 README work touch separate files and can proceed independently, provided T012 uses the frozen comparison record.

## Implementation Strategy

Complete setup and freeze the training-only decision first. Deliver US1 as the MVP with a checkpoint and paired, repeatable results; then verify overrides and document the tradeoff in US2. Finish with the existing regression suite and a cross-artifact review. A retained 30-epoch default is a valid outcome when no candidate meets the rule.
