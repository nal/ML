---
description: "Implementation tasks for the matched-core benchmark"
---

# Tasks: Matched-Core Benchmark

**Input**: `specs/006-matched-core-benchmark/` design documents  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md

**Organization**: Tasks are grouped by user story. `[P]` identifies tasks on separate files that have no dependency on other incomplete tasks in the same parallel group.

## Phase 1: Setup

- [ ] T001 Review existing CLI, device detection, results publication and tests in `src/shape_classifier/` and `tests/` against `specs/006-matched-core-benchmark/quickstart.md`; retain existing dependencies and sequential publication behavior.

## Phase 2: Foundational

- [ ] T002 Inventory CPU computation pools used by training, augmentation and held-out inference in `src/shape_classifier/train.py` and `src/shape_classifier/transforms.py`; determine how each is limited or demonstrate it is inactive or serial, including PyTorch inter-op initialization and repeated in-process calls, and record the findings in `specs/006-matched-core-benchmark/research.md`.

## Phase 3: User Story 1 — Choose CPU threads (P1, MVP)

**Goal**: Configure, report and record a training-only CPU computation thread count while preserving the default.

**Independent test**: Train with eight threads and with the option omitted; confirm the reported and recorded counts and default behavior. Invalid or excessive requests fail before loading data or writing files; MPS limits CPU-side pools only.

### Tests

- [ ] T003 [P] [US1] Add CLI and publication tests in `tests/test_classifier.py` and `tests/test_publication.py` for explicit, omitted, zero, negative, non-integer and excessive counts, including unchanged checkpoint, results and recovery files on rejection and unchanged evaluation/prediction interfaces.
- [ ] T004 [P] [US1] Add training pool and result-entry tests in `tests/test_results.py` for configured CPU pools, startup count, default and explicit requests, MPS CPU-side behavior, and repeated calls or fresh subprocesses as required by inter-op initialization.

### Implementation

- [ ] T005 [US1] Add training-only `--cpu-threads N` parsing and early validation in `src/shape_classifier/__main__.py`: N is a positive integer no greater than process-available CPUs; report requested and available counts on excess before data loading or recovery/publication writes.
- [ ] T006 [US1] Configure all active training CPU computation pools identified in T002 before their initialization in `src/shape_classifier/train.py`; preserve the all-available default, report the configured count, enforce explicit count agreement, and leave GPU allocation and evaluation/prediction threading unchanged.
- [ ] T007 [US1] Extend entries in `src/shape_classifier/train.py` with `requested_cpu_threads`: "positive integer or null for default; absent in legacy entries also means default"; keep `cpu_threads` as the existing positive configured count and preserve transactional publication.
- [ ] T008 [US1] Extend validation in `src/shape_classifier/benchmark.py` for the new nullable request field while accepting legacy entries unchanged; reject invalid new values and preserve the existing version-1 format.

**Checkpoint**: Run the US1 tests and an explicit/default training comparison before proceeding.

## Phase 4: User Story 2 — Match Docker VM allocation (P1)

**Goal**: Verify and report Colima allocation when possible and warn otherwise, without changing VM configuration in the application.

**Independent test**: On an 8-CPU Colima VM, launch with 8 threads and verify a known matching allocation; launch with 4 and verify a mismatch warning. A direct or unverifiable run records unknown and warns.

### Tests

- [ ] T009 [P] [US2] Add allocation evidence and warning tests in `tests/test_device.py` for verified matching/mismatching values, missing or malformed evidence, container restrictions, and the unknown fallback.
- [ ] T010 [P] [US2] Add host-launcher tests in `tests/test_colima_launcher.py` using mocked Colima status and Docker endpoint responses for matching profiles, overridden endpoints, stopped or ambiguous profiles, malformed and unsupported responses, and no VM configuration changes.

### Implementation

- [ ] T011 [US2] Implement `scripts/matched-core-docker.sh` to query the running Colima profile's machine-readable CPU allocation and socket, compare the effective Docker endpoint, and pass validated launch-time observation and provenance into the container; fail closed to unknown on uncertainty and never change the VM.
- [ ] T012 [US2] Replace container-visible CPU inference in `src/shape_classifier/device.py` with conservative validation of launcher evidence; `docker_cpus` is an "existing positive integer or \"unknown\" for Docker; retain existing native representation" and unverifiable evidence is unknown.
- [ ] T013 [US2] Integrate the observation in `src/shape_classifier/__main__.py` and `src/shape_classifier/train.py`: report VM allocation, warn for unknown and for a known mismatch with an explicit request, continue valid runs, and record the observation per entry.
- [ ] T014 [US2] Document in `README.md` how to inspect, manually stop/restart Colima with 8 CPUs, run the launcher, restore the original allocation, and account for the restart affecting all containers and for no VM/context changes during a run.

**Checkpoint**: Run launcher and device tests; verify real Colima behavior when the reference environment is available and its reconfiguration has been authorized.

## Phase 5: User Story 3 — Compare matched configurations (P2)

**Goal**: Produce truthful, backward-compatible rows separated by actual resource settings.

**Independent test**: Summarize mixed old and new entries for multiple thread and VM counts; verify separate rows, legacy default labels, missing configurations, paired accuracies, and unchanged whole-GPU measurements without modifying the results file.

### Tests

- [ ] T015 [P] [US3] Add mixed legacy/new schema and no-rewrite coverage in `tests/test_results.py`, including absent, null, valid and invalid request fields and retained legacy Docker allocation values.
- [ ] T016 [P] [US3] Add summary grouping and display tests in `tests/test_benchmark.py` for differing actual threads and known/unknown VM counts, default/explicit/mixed provenance, whole-GPU times, paired accuracies and missing configurations.

### Implementation

- [ ] T017 [US3] Extend grouping in `src/shape_classifier/benchmark.py` using existing dataset, seed, epochs, batch size, environment and device plus actual `cpu_threads` and Docker `docker_cpus`, treating unknown as distinct and leaving legacy records untouched.
- [ ] T018 [US3] Extend summary output in `src/shape_classifier/benchmark.py` to show per-row actual CPU threads, Docker allocation, default/explicit/mixed request provenance, run counts and paired accuracies; label MPS whole GPU and preserve measured times without scaling or extrapolation.

**Checkpoint**: Run summary tests against mixed results and verify that reading the file does not mutate it.

## Phase 6: User Story 4 — Explain and report the comparison (P3)

**Goal**: Document a measured comparison and the limits of matching CPU and GPU resources.

**Independent test**: Read `README.md` and verify all explanations and measured same-thread results for Docker CPU, native CPU and native MPS are present, with paired accuracies and feature 004 caveats.

- [ ] T019 [US4] Explain in `README.md` why GPU cores cannot be limited or equated to CPU cores, why GPU times cannot be extrapolated to fewer cores, why thread counts do not pin work to performance cores, and the synthetic dataset and reproducibility limitations.
- [ ] T020 [US4] Follow `specs/006-matched-core-benchmark/quickstart.md` on the reference M1 Pro after authorized manual Colima reconfiguration; run Docker CPU, native CPU and native MPS sequentially at 8 CPU threads on identical settings, and record the actual measured values and paired accuracies in `README.md` without extrapolation; restore the prior VM allocation.

## Phase 7: Polish and Cross-Cutting Validation

- [ ] T021 Run the classifier test suite and `python3 scripts/features.py --check` using `tests/` and `scripts/features.py`; resolve regressions while preserving existing checkpoints, benchmark files and publication semantics.
- [ ] T022 Complete all runnable scenarios in `specs/006-matched-core-benchmark/quickstart.md`, including invalid-count no-write checks, legacy summary and real hardware acceptance; record any environment-dependent blockers rather than inventing measurements.

## Dependencies & Execution Order

- Setup T001 → foundational T002 → US1 T003–T008.
- US2 T009–T014 depends on US1 for the training option and entry integration. T009 and T010 are parallel; T011 and T012 may proceed in parallel after their tests, then T013 integrates both. T014 may proceed alongside implementation after the launcher interface is settled.
- US3 T015–T018 depends on the US1 entry schema and US2 allocation semantics. T015 and T016 are parallel; T017 precedes T018.
- US4 T019–T020 depends on working US1–US3 for the measured comparison; T019 can be drafted after T014 while other stories are implemented. T020 requires real hardware and authorized manual VM changes.
- Polish T021–T022 follows all stories; test tasks precede the implementation they exercise.

## Parallel Examples

- US1: T003 and T004 cover independent test files; implement T005 and T006 after tests and coordinate their interface before T007.
- US2: T009 and T010 can be written together; T011 and T012 affect different files after their test contracts are understood.
- US3: T015 and T016 can be written together; grouping and display tasks share `benchmark.py` and must be sequenced.
- US4: T019 can be drafted after T014 while other stories are underway; T020 follows completed execution paths and cannot run in parallel with benchmark runs.

## Implementation Strategy

Deliver US1 first as the MVP and validate its explicit/default and invalid-input paths. Add verified VM reporting, then resource-aware summary grouping, then the measured comparison and explanatory documentation. Complete the final validation and `$speckit-converge` before marking the feature implemented. The reference-machine benchmark is required for feature completion; missing hardware or authorization is a blocker to record, not a reason to fabricate data.
