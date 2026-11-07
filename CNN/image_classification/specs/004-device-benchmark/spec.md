# Feature Specification: Device Benchmark

**Feature Branch**: `feat/004-device-benchmark`

**Created**: 2026-11-07

**Status**: Draft

**Input**: User description: "feature 004 device benchmark". Expanded from the planned feature 004 description in `README.md` §7: add an optional native macOS mode and a device performance comparison, as defined in the "Technical stack" (native macOS and device selection) and "Performance comparison" sections of `CNN_image_classification_research.md`. Docker remains the default runtime.

## Clarifications

### Session 2026-11-07

- Q: Which CPU thread policy should benchmark runs use: keep 1 thread (deterministic), use all available cores, or add a thread-count option defaulting to 1? → A: Use all available cores for every training run.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Choose the compute device explicitly (Priority: P1)

A user runs training, evaluation or prediction and chooses where the work runs: automatically, on the CPU, or on the Mac's GPU (MPS). If the user asks for the GPU and it is not available, for example inside Docker, the command stops with a clear message instead of quietly using the CPU. Every run states which environment and device it actually used.

**Why this priority**: Without explicit, truthful device selection no benchmark can be trusted. A silent fallback would make a "GPU" result actually measure the CPU. Today every run claims "docker, cpu" even outside Docker.

**Independent Test**: In Docker, run training with each device choice. Automatic and CPU succeed and report Docker and CPU; GPU fails clearly without producing a result or overwriting the saved model. On a native Mac with GPU support, automatic resolves to the GPU and reports native and GPU.

**Acceptance Scenarios**:

1. **Given** the Docker environment, **When** the user trains with device `auto`, **Then** the run uses the CPU and reports environment Docker and device CPU.
2. **Given** the Docker environment, **When** the user trains, evaluates or predicts with device `mps`, **Then** the command fails with a message saying the GPU is unavailable in this environment, and no checkpoint or result entry is written.
3. **Given** a native Mac where the GPU is available, **When** the user runs any command with device `auto`, **Then** it uses the GPU and reports environment native and device MPS.
4. **Given** any environment, **When** the user runs a command with device `cpu`, **Then** it uses the CPU.
5. **Given** any run, **When** it starts, **Then** it reports the resolved device, environment, Python version and PyTorch version.
6. **Given** a user who does not pass a device, **When** they run any command, **Then** behavior is the same as device `auto`.

---

### User Story 2 - Run natively on the Mac with the same versions (Priority: P1)

A user sets up an optional native environment on the Mac that uses exactly the same Python and package versions as Docker. They can generate, train, evaluate and predict there, using the same data folder as Docker, so both environments work on identical images.

**Why this priority**: The GPU is only reachable outside Docker. The native mode is a precondition for two of the three benchmark configurations.

**Independent Test**: Follow the documented native setup, confirm the reported versions match the Docker image, train on the same data folder Docker uses, and evaluate the resulting model in Docker.

**Acceptance Scenarios**:

1. **Given** the documented native setup, **When** it completes, **Then** Python and every pinned package report the same versions as in Docker. The only allowed difference is the platform build of PyTorch (CPU-only build in Docker, standard build with GPU support natively).
2. **Given** a dataset generated in Docker, **When** the user trains natively against the same data folder, **Then** training uses those images unchanged.
3. **Given** a model trained natively on the GPU, **When** the user evaluates or predicts with it in Docker on the CPU, **Then** it loads and works.
4. **Given** a model saved by feature 002 or 003, **When** the user evaluates or predicts with it after this feature, **Then** it still loads and works.

---

### User Story 3 - Record and compare performance across configurations (Priority: P2)

A user trains under three configurations, Docker CPU, native CPU and native GPU, with the same data, seeds, model, epoch count and batch size. Each run adds one entry to a shared results file. A summary command prints a comparison table, so the user can see which configuration is fastest and whether accuracy differs.

**Why this priority**: This is the feature's analytical goal. It builds on Stories 1 and 2.

**Independent Test**: Run training once in each configuration against the same data folder, then run the summary command and confirm one row per configuration with timing, accuracy and environment details.

**Acceptance Scenarios**:

1. **Given** a successful training run, **When** it finishes, **Then** one entry is added to the results file containing environment, device, Python and PyTorch versions, CPU thread count, and for Docker runs the CPU count and memory available to the Docker VM. The entry also contains total training time and mean time per epoch, both excluding the first epoch; inference time per held-out image; final training loss; and training and held-out accuracy.
2. **Given** entries for all three configurations, **When** the user runs the summary command, **Then** it prints a table with one row per configuration showing the number of runs and the timing and accuracy figures.
3. **Given** entries for only some configurations, **When** the user runs the summary command, **Then** it shows those configurations and marks the missing ones as not yet measured.
4. **Given** a GPU run, **When** times are recorded, **Then** they include all GPU work submitted during the timed interval, so GPU times are not understated.
5. **Given** a run that fails or is interrupted, **When** it stops, **Then** no entry is added for it.

---

### User Story 4 - Read the results honestly (Priority: P3)

A user reads the documentation and the summary and understands what the numbers do and do not show: the GPU may be no faster, or slower, for this tiny model; accuracy may differ slightly between devices; and Docker may have fewer CPU cores than the Mac.

**Why this priority**: Constitution principle III requires honest reporting, but this story only adds value once results exist.

**Independent Test**: Read the documentation and a printed summary and check that each of these caveats is stated.

**Acceptance Scenarios**:

1. **Given** results where the GPU is slower than the CPU, **When** they are summarized and documented, **Then** they are reported as measured, without being called an error or left out.
2. **Given** results from different devices, **When** accuracy differs between them, **Then** the documentation explains that GPU and CPU arithmetic are not bit-identical.
3. **Given** the benchmark documentation, **When** a user reads it, **Then** it states the reproducibility limits on the GPU and on multithreaded CPU runs, and the dataset's small, synthetic nature.

### Edge Cases

- A run with exactly one epoch cannot exclude a warm-up epoch. The per-epoch and warm-up-excluded figures are recorded as unavailable, not as zero, and the run still succeeds.
- The native environment reports a GPU as present but unusable, for example on an old OS version. Device `mps` fails clearly; `auto` uses the CPU and says so.
- The results file is missing. The first successful run creates it. If the summary is requested with no file or no entries, it prints a clear "no results yet" message and exits successfully.
- The results file is malformed or was written by an incompatible version. The summary reports the problem clearly and does not crash; training does not overwrite or discard existing entries.
- Docker and native runs write to the same results file. Entries from both are kept, and concurrent runs do not corrupt the file.
- The Docker VM's CPU and memory allocation cannot be determined. The entry records it as unknown rather than guessing.
- A checkpoint's metadata records an environment or device other than the current one. It still loads, since the checkpoint is saved device-neutral, but incompatible preprocessing or class order is still rejected.
- Results from runs with different data, seeds, epochs or batch sizes exist in the same file. The summary does not mix them into one comparison without making that visible.

## Requirements *(mandatory)*

### Functional Requirements

**Device selection and run reporting**

- **FR-001**: Training, evaluation and prediction MUST accept a device choice of `auto`, `cpu` or `mps`, defaulting to `auto`.
- **FR-002**: `auto` MUST use the GPU when it is available and usable, otherwise the CPU. Inside Docker it MUST always resolve to the CPU.
- **FR-003**: `mps` MUST fail with a clear, actionable error when the GPU is unavailable. It MUST NOT silently fall back to the CPU, and it MUST NOT write a checkpoint or results entry.
- **FR-004**: Every run MUST report, at start, the resolved device, the actual environment (Docker or native), and the Python and PyTorch versions. The environment MUST be detected, not assumed.

**Native environment**

- **FR-005**: An optional native macOS environment MUST be documented and reproducible, using the same pinned Python version (3.14.10) and the same single shared set of pinned package versions as Docker. The only difference allowed is the platform build of PyTorch.
- **FR-006**: The native environment MUST be able to run dataset generation, training, evaluation, prediction and the summary, using the same project data folder as Docker.
- **FR-007**: Docker MUST remain the default runtime, and every existing documented Docker command MUST keep working unchanged apart from the added optional device choice.

**Checkpoint compatibility**

- **FR-008**: Saved models MUST stay device-neutral: saved from CPU-resident weights and loadable on any supported device in any environment.
- **FR-009**: Saved model metadata MUST record the environment and device the model was actually trained with. Loading MUST NOT reject a model only because its recorded environment or device differs from the current one. Loading MUST still reject incompatible preprocessing, input size, class order or malformed provenance.
- **FR-010**: Models saved by features 002 and 003 MUST continue to load for evaluation and prediction.

**Performance recording**

- **FR-011**: Each successful training run MUST add exactly one entry to a machine-readable results file in the project data folder. Existing entries MUST NOT be modified or removed.
- **FR-012**: Each entry MUST record: environment; device; Python and PyTorch versions; CPU thread count; for Docker runs the CPU count and memory available to the Docker VM, or "unknown"; seed, epoch count, batch size and an identifier of the training data used; total training time and mean time per epoch, both excluding the first epoch; mean inference time per held-out image; final training loss; training and held-out accuracy with correct and total counts; and a timestamp.
- **FR-013**: Timings on the GPU MUST be taken only after all queued GPU work for the timed interval has completed.
- **FR-014**: Held-out data MUST be used only for measuring accuracy and inference time after training. It MUST NOT influence training, model selection or any configuration choice.
- **FR-015**: Every training run on the CPU MUST use all CPU cores available to its environment, replacing the current single-thread setting. Inside Docker that means the cores allocated to the Docker VM. No thread-count option is added. The thread count used MUST be reported at the start of the run and recorded in each entry. Other reproducibility measures (fixed seeds, deterministic algorithms where supported) MUST remain in place.
- **FR-016**: A failed or interrupted run MUST NOT add an entry, and concurrent writers MUST NOT corrupt the results file.

**Summary**

- **FR-017**: A summary command MUST print a comparison table with one row per configuration (environment and device). Each row shows the number of runs and the mean timing, inference and accuracy figures. Configurations with no runs are shown as not yet measured.
- **FR-018**: The summary MUST only compare runs that share the same training data, seed, epoch count and batch size, or MUST visibly separate groups that differ.
- **FR-019**: The summary MUST present training accuracy and held-out accuracy together.

**Documentation and honesty**

- **FR-020**: Documentation MUST explain the native setup, the device choice, how to run the three configurations and the summary, and how to read the results.
- **FR-021**: Documentation and summary MUST report results as measured, including a GPU that is slower or no faster. Documentation MUST state that GPU and CPU results are not bit-identical, that multithreaded CPU runs may differ slightly between repeats and between machines with different core counts, that Docker may have fewer CPU cores or less memory than the Mac, and that the dataset is a small synthetic demo.

### Key Entities

- **Device choice**: The user's requested device (`auto`, `cpu`, `mps`) and the device it resolved to.
- **Run environment**: Docker or native, plus Python and PyTorch versions, CPU thread count and, for Docker, the CPU and memory allocated to the VM.
- **Benchmark entry**: One successful training run's environment, configuration (data identifier, seed, epochs, batch size), timings, loss, paired accuracy and timestamp.
- **Results file**: The append-only collection of benchmark entries, stored in the shared data folder.
- **Comparison summary**: Per-configuration aggregation of entries that share the same training data and settings.
- **Model provenance**: Checkpoint metadata, extended to record the actual training environment and device.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In Docker, 100% of runs that request the GPU fail with a clear message and leave the saved model and results file unchanged. Device `auto` and `cpu` succeed.
- **SC-002**: Every run's start-up line correctly names its environment and device in both Docker and native runs, with no run claiming Docker when it is native or the reverse.
- **SC-003**: A user can go from a fresh clone to a working native environment, with matching versions, by following the documentation in under 15 minutes, excluding download time.
- **SC-004**: After one training run in each of the three configurations on the same data, the summary shows all three with run counts, timings that exclude the warm-up epoch, inference time per image, final loss and paired training and held-out accuracy.
- **SC-005**: A model trained in any configuration can be evaluated and used for prediction in every other configuration, and models saved by features 002 and 003 still load.
- **SC-006**: Two consecutive successful runs add exactly two entries, and a failed or interrupted run adds none.
- **SC-008**: Every CPU run's entry records a thread count equal to the number of cores available to its environment, and the documentation reports the observed repeat-run variation for CPU runs.
- **SC-007**: The documentation states every caveat listed in User Story 4, and the published comparison reports measured numbers even if the GPU is slower.

## Assumptions

- The Mac is Apple silicon (M1 Pro) running macOS 15 or newer, with GPU support in the standard PyTorch build. The research document records macOS 27.0.1 and confirms that PyTorch 2.15.0 with MPS is available for Python 3.14.
- The existing data folder, generated datasets (30 training, 15 held-out images) and default training settings (seed 42, 60 epochs, batch size 8) are reused. This feature does not change the model, preprocessing, augmentation or dataset.
- Results are recorded automatically on every successful training run, not behind an opt-in flag, as the research document states ("each training run records").
- The results file lives in the data folder so both environments write to the same file and it persists outside the container.
- Users may repeat runs per configuration. The summary averages them and shows the count rather than picking one run.
- Inference time is measured on the held-out images after training, in the same run, so it adds no extra command.
- Plotting is optional and out of scope. The summary is a printed table.
- Neither GPU runs nor multithreaded CPU runs are expected to be bit-reproducible. Switching CPU training from one thread to all cores is a deliberate change from feature 003's behavior, chosen so that the speed comparison is fair. Repeat CPU runs on the same machine and data are expected to stay close, within one correct image per split as in feature 003, but this is a target to measure and document, not a guarantee.
- The epoch default of 60 from feature 003 was chosen under single-thread training. It is kept unchanged; re-selecting it is out of scope.
