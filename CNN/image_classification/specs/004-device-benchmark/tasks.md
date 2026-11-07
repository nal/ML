# Tasks: Device Benchmark

**Input**: `specs/004-device-benchmark/` design artifacts  
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/cli.md`  
**Organization**: Tasks follow user stories and include tests for the specification's independent and failure scenarios. Write each story's tests before its implementation. Paths are relative to the project directory.

## Phase 1: Setup

- [X] T001 Verify Python and Docker ignore patterns in `.gitignore` and `.dockerignore`, adding only missing critical patterns.
- [X] T002 Inspect existing CLI, dataset, checkpoint and regression tests in `src/shape_classifier/` and `tests/test_classifier.py` to preserve current commands and compatibility.

## Phase 2: Foundational

- [X] T003 Establish reusable test fixtures for validated train/held-out datasets and legacy checkpoints in `tests/test_classifier.py`.
- [X] T004 Add device resolution and startup/error tests in `tests/test_device.py`, including Docker, usable/unusable native MPS, explicit CPU and omitted device.

## Phase 3: User Story 1 — Choose the compute device (P1, MVP)

**Goal**: Train, evaluate and predict on a truthful resolved device with portable checkpoints.

**Independent test**: In Docker, auto and CPU work; explicit MPS fails before writes for all commands. On a usable native Mac, auto selects MPS. Startup reports actual environment, device and versions.

- [X] T005 [US1] Implement shared run context and device resolution in `src/shape_classifier/device.py`: requested device `auto`, `cpu`, or `mps`; resolved device `cpu` or `mps`; environment `docker` or `native`; actual MPS usability probe and Docker CPU-only selection.
- [X] T006 [P] [US1] Add checkpoint provenance, malformed metadata and legacy/cross-device compatibility tests in `tests/test_checkpoint.py`.
- [X] T007 [US1] Update `src/shape_classifier/checkpoint.py` to save CPU-resident weights with actual environment/device, accept valid legacy Docker/CPU metadata, reject malformed provenance or incompatible class order/input size/scaling, and load via CPU.
- [X] T008 [US1] Update `src/shape_classifier/train.py` and `src/shape_classifier/predict.py` to move models, inputs and labels to the resolved device while retaining shared preprocessing, fixed seeds and deterministic algorithms where supported.
- [X] T009 [US1] Add `--device {auto,cpu,mps}` defaulting to `auto`, startup context reporting and early failure before writes to train/evaluate/predict in `src/shape_classifier/__main__.py`.
- [X] T010 [US1] Run device and checkpoint scenarios including existing CLI regressions in `tests/test_device.py`, `tests/test_checkpoint.py` and `tests/test_classifier.py`.

## Phase 4: User Story 2 — Native Mac with shared versions (P1)

**Goal**: Use one exact dependency inventory in Docker and native macOS against the same data and checkpoints.

**Independent test**: Follow native setup, compare installed Python and package versions to Docker, train against Docker-generated data, and evaluate the checkpoint on Docker CPU.

- [X] T011 [US2] Update `requirements.txt` with a single shared set of exact package pins and platform markers selecting Linux CPU and native macOS standard PyTorch/torchvision builds; retain the same package versions.
- [X] T012 [P] [US2] Update `Dockerfile` only as needed to install the shared pins and retain the default CPU image and existing entrypoint.
- [X] T013 [US2] Document pinned Python 3.14.10, native virtual environment installation, shared data/checkpoint paths, generation and all classifier commands in `README.md`.
- [X] T014 [US2] Validate Docker and native package versions, dependency health, shared images and cross-environment checkpoint loading using `specs/004-device-benchmark/quickstart.md`; record actual platform limitations if native hardware is unavailable.

## Phase 5: User Story 3 — Record and compare performance (P2)

**Goal**: Atomically publish successful measurements and display comparable grouped results.

**Independent test**: Train in each available configuration on the same data and settings; summary shows separate rows, counts, timing, loss and paired accuracies; missing configurations are marked.

- [X] T015 [P] [US3] Add measurement tests in `tests/test_benchmark.py` for warm-up exclusion, one epoch unavailable times, MPS synchronization, held-out inference and paired counts, CPU thread reporting and dataset identity.
- [X] T016 [P] [US3] Add results and summary tests in `tests/test_results.py` for empty/malformed/incompatible files, grouping, missing configurations, nullable timing and arithmetic means.
- [X] T017 [P] [US3] Add publication failure and interruption/recovery tests in `tests/test_publication.py` for sequential commands, including shared and distinct checkpoint paths, interruption immediately before and after the results commit point, and a results-save failure preserving prior checkpoint bytes or prior absence. Test interruption in Docker followed by native recovery and the reverse for shared paths, prediction recovery from a nested checkpoint without a data-directory argument across mounts, and inaccessible external recovery locations.
- [X] T018 [US3] Implement dataset SHA-256 fingerprint over sorted relative paths and bytes of both validated splits with length-delimited records in `src/shape_classifier/data.py`.
- [X] T019 [US3] Implement CPU thread and reliable Docker resource detection in `src/shape_classifier/device.py`: all available CPU cores for CPU training; report actual thread count; record VM CPU/memory as positive values when known or `unknown`, native values null.
- [X] T020 [US3] Add synchronized epoch timing excluding first epoch, final epoch loss and held-out per-image inference timing in `src/shape_classifier/train.py`; retain held-out isolation and paired accuracy assessment.
- [X] T021 [US3] Implement versioned results validation and grouping in `src/shape_classifier/benchmark.py`: UTC timestamp, context, fingerprint, seed, epochs, batch size, times, loss and paired correct/total counts; positive epochs/batch size, positive totals, valid counts, finite nonnegative metrics and null warm-up times for one epoch.
- [X] T022 [US3] Implement sequential publication, durable journal and checkpoint-side recovery discovery in `src/shape_classifier/publication.py`; remove the existing advisory-lock mechanism and do not promise concurrent access or automatic detection. Stage outputs, preserve the previous checkpoint, publish checkpoint then results as commit point, resolve the journal relative to the checkpoint sidecar directory for shared-data paths across Docker/native mounts without requiring a data-directory argument, and report inaccessible external recovery locations without discarding the journal.
- [X] T023 [US3] Integrate sequential publication and recovery with checkpoint reads and writes in `src/shape_classifier/checkpoint.py`, `src/shape_classifier/train.py` and `src/shape_classifier/__main__.py`; remove their existing advisory-lock dependencies, defer ordinary termination signals around publication, roll back on results-save failure and record exactly one entry per committed run.
- [X] T024 [US3] Add `summary --data-dir` and grouped three-configuration table in `src/shape_classifier/__main__.py` and `src/shape_classifier/benchmark.py`, with run counts, mean available timings/loss and paired accuracy, clear empty/error states and no mixing of different dataset fingerprints, seeds, epochs or batch sizes.
- [X] T025 [US3] Run targeted measurement, summary, failure-injection and sequential recovery tests in `tests/test_benchmark.py`, `tests/test_results.py` and `tests/test_publication.py`.

## Phase 6: User Story 4 — Read results honestly (P3)

**Goal**: Explain measured results and reproducibility limits without implying GPU speedup or generalization.

**Independent test**: Read README and summary with a slower GPU result; verify it is shown and all required caveats are present.

- [X] T026 [US4] Add measured-result caveats to summary output in `src/shape_classifier/benchmark.py`: small synthetic demo, device arithmetic differences, resource differences and potentially slower GPU.
- [X] T027 [US4] Document three comparable runs performed sequentially, the unsupported overlapping access and lack of guaranteed detection, summary interpretation, observed CPU repeat-run variation, MPS/multithread nondeterminism, Docker resource limits and small synthetic dataset in `README.md`; retain results even when MPS is slower.
- [X] T028 [US4] Validate summary caveats and README claims against actual measurements using `specs/004-device-benchmark/quickstart.md`.

## Phase 7: Polish and Cross-Cutting Validation

- [X] T029 Run full regression and dependency checks in Docker as documented in `specs/004-device-benchmark/quickstart.md`.
- [X] T030 Run native CPU/MPS and cross-environment acceptance scenarios in `specs/004-device-benchmark/quickstart.md`, recording unavailable hardware or unresolved failures explicitly.
- [X] T031 Review implementation against `specs/004-device-benchmark/spec.md`, `specs/004-device-benchmark/contracts/cli.md`, and `specs/004-device-benchmark/data-model.md`; resolve mismatches and run `python3 scripts/features.py --check`.

## Dependencies & Execution Order

Setup → foundation → US1 → US2 → US3 → US4 → final validation. US2 needs US1 for native device execution and portable checkpoints. US3 needs both for the three-way comparison; US4 needs US3's output. Each phase has its own independent validation checkpoint. Tests precede their implementations. Tasks touching the same files run sequentially.

### Parallel opportunities

- US1: T004 establishes device tests in the foundation before T005 implements resolution; T006 covers checkpoint tests before checkpoint integration.
- US2: T012 can proceed independently of T011's edits but Docker build validation waits for both; T013 follows dependency choices.
- US3: T015, T016 and T017 can be authored independently before implementation; T018 and T019 affect separate modules after tests. Publication integration waits for T021 and T022.
- US4: README and summary changes touch separate files, but T027 records measurements only after the benchmark runs exist.

## Implementation Strategy

Deliver US1 as the MVP and verify Docker failure behavior and native device selection. Then add native setup and cross-device compatibility, followed by recording/summary and honest interpretation. Finish with full Docker and native validation; do not mark platform-specific checks complete without executing them.

## Phase 8: Convergence

- [X] T032 Record Docker VM CPU count and memory in benchmark entries when discoverable from inside the container (available CPUs and `/proc/meminfo` MemTotal when no tighter cgroup limit applies), falling back to `unknown` only when they cannot be determined, in `src/shape_classifier/device.py`, with tests in `tests/test_benchmark.py` per FR-012, US3/AC1 (partial)
- [X] T033 Make publication recovery verify that the recorded checkpoint location is resolvable and accessible before restoring or removing outputs, and fail clearly while preserving the journal and sidecar when it is not, in `src/shape_classifier/publication.py`; add the inaccessible external recovery location test in `tests/test_publication.py` per data-model: publication transaction, T017, T022 (partial)
- [X] T034 Measure repeated CPU training runs with identical data and settings and document the observed repeat-run variation in `README.md` per SC-008, T027 (partial)
- [X] T035 Run Docker CPU, native CPU and native MPS training sequentially at default settings on the same data and replace the README smoke comparison with the resulting summary (warm-up-excluded timing, inference per image, loss and paired accuracy) in `README.md` per SC-004, SC-007, T028, T030 (partial)
- [X] T036 Format the summary as an aligned table with unambiguous column headers in `src/shape_classifier/benchmark.py`, updating `tests/test_results.py` per FR-017 (partial)
