# Feature Specification: Matched-Core Benchmark

**Feature Branch**: `feat/006-matched-core-benchmark`

**Created**: 2026-11-07

**Status**: Implemented

**Input**: User description: "Matched-core benchmark: add an optional CPU thread-count option to training (--cpu-threads N, default: all available cores as in feature 004) so benchmark configurations can use the same number of CPU cores. Target comparison on this M1 Pro (8 performance + 2 efficiency CPU cores, 16-core GPU): Docker CPU with the Colima VM set to 8 CPUs, native CPU with 8 threads, and native MPS using the whole GPU with CPU-side work limited to 8 threads. Changing the Docker VM CPU count is a documented manual step (colima stop/start --cpu 8) that affects all containers; the app only detects and reports it and warns when the Docker VM CPU count differs from the requested thread count. A requested thread count above the available cores fails clearly. Each benchmark entry records the requested and actual thread count and the Docker VM CPU count; the summary shows thread count per row and never averages runs with different thread counts together. MPS GPU cores cannot be limited and GPU results are never extrapolated or scaled: MPS is reported as measured, as a different processor type, not as "N cores". Documentation explains why GPU-core matching and time extrapolation are not supported."

**Relationship to feature 004**: This feature amends [004 FR-015](../004-device-benchmark/spec.md). There, CPU training always used all available cores and no thread-count option was offered. That remains the default; this feature adds an optional override.

## Clarifications

### Session 2026-11-07

- Q: When a container can see its own CPU limit but cannot verify the Docker VM’s total CPU allocation, what should the benchmark record for the VM CPU count? → A: Record the VM count as unknown and warn.
- Q: What should the requested thread count limit during training? → A: CPU computation thread pools used by training; background and system threads may exist.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Train with a chosen number of CPU threads (Priority: P1)

A user trains with an explicit CPU thread count, for example 8, instead of every available core. The run configures its CPU computation thread pools to that count, reports it at start-up, and records it with the results. Without the option, training behaves exactly as in feature 004.

**Why this priority**: This is the one new capability. Every matched comparison depends on it.

**Independent Test**: Natively, train once with 8 threads and once without the option. The first run reports and records 8 threads; the second reports and records all available cores (10 on this Mac) and otherwise matches feature 004 behavior.

**Acceptance Scenarios**:

1. **Given** a native Mac with 10 available cores, **When** the user trains with 8 threads, **Then** start-up reports 8 threads and the benchmark entry records 8 requested and 8 used.
2. **Given** any environment, **When** the user trains without the option, **Then** training uses all available cores, as in feature 004, and the entry records that no specific count was requested.
3. **Given** a request for more threads than the environment has cores (for example 8 in a 2-CPU Docker VM), **When** training starts, **Then** it fails with a message stating the requested and available counts, before any data is loaded or any file is written.
4. **Given** a request for zero, a negative or a non-integer thread count, **When** training is requested, **Then** the command fails clearly without a result.
5. **Given** a GPU (MPS) run with 8 threads, **When** it trains, **Then** CPU computation thread pools used for CPU-side work are limited to 8 threads while the GPU is used in full, and the entry records 8 threads for the CPU side only.

---

### User Story 2 - Run Docker with a matching number of cores (Priority: P1)

A user reconfigures the Docker VM to 8 CPUs by following a documented manual step, then trains in Docker with 8 threads. The run confirms the VM has the expected number of CPUs, or warns clearly when it doesn't.

**Why this priority**: The current comparison mixes the effect of the environment with the effect of Docker having only 2 cores. Matching Docker's cores is what separates the two.

**Independent Test**: Follow the documented step to give the Docker VM 8 CPUs, train in Docker with 8 threads, and confirm the run reports and records 8 VM CPUs with no warning. Then train with 4 threads on the same VM and confirm a mismatch warning appears while the run still completes.

**Acceptance Scenarios**:

1. **Given** the documentation, **When** a user follows the Docker VM step, **Then** they learn how to set the VM's CPU count, that it restarts the VM and affects every container on the machine, and how to return to the previous setting.
2. **Given** a Docker VM with 8 CPUs, **When** the user trains in Docker with 8 threads, **Then** the run reports 8 VM CPUs and 8 threads, with no warning.
3. **Given** a Docker VM whose CPU count differs from a requested thread count that does not exceed process-available CPUs, **When** training starts, **Then** a warning names both numbers and explains that the comparison is not core-matched, and training continues.
4. **Given** a Docker VM whose CPU count cannot be determined, **When** training starts with a thread count, **Then** a warning says the VM's CPU count could not be verified, and the entry records it as unknown.
5. **Given** any training run, **When** the application runs, **Then** it never changes the Docker VM's configuration itself.

---

### User Story 3 - Compare matched configurations in the summary (Priority: P2)

A user has run Docker CPU, native CPU and native GPU training, each with 8 threads, on the same data and settings. The summary shows each configuration with its thread count, keeps runs with different thread counts apart, and presents the GPU row as whole-GPU, measured results.

**Why this priority**: This is the result the user wants to read. It depends on Stories 1 and 2.

**Independent Test**: With entries for Docker CPU at 8 and 2 threads, native CPU at 8 and 10 threads, and native GPU at 8 threads, run the summary. Check that every thread count has its own row, no row averages across thread counts, and the GPU row is labeled as using the whole GPU.

**Acceptance Scenarios**:

1. **Given** entries for one configuration at two different thread counts, **When** the summary runs, **Then** it shows two separate rows, each with its own run count and averages.
2. **Given** Docker entries recorded with different Docker VM CPU counts, **When** the summary runs, **Then** they appear in separate rows that show the VM CPU count.
3. **Given** a GPU entry, **When** the summary shows it, **Then** the row states that the GPU was used in full, shows the CPU-side thread count separately, and its times are exactly as measured, with no scaling or extrapolation.
4. **Given** entries written by feature 004, which have no requested thread count, **When** the summary runs, **Then** they are still shown, grouped by the thread count they actually used and marked as using the default.
5. **Given** a configuration with no entries, **When** the summary runs, **Then** it is still marked as not yet measured, as in feature 004.

---

### User Story 4 - Understand what can and cannot be matched (Priority: P3)

A user reads the documentation and understands why only CPU cores can be matched, why the GPU can't be limited to a number of cores, and why GPU times are never scaled to emulate fewer cores.

**Why this priority**: It prevents the misleading comparison this feature was designed to avoid, but adds value only once results exist.

**Independent Test**: Read the documentation and check that each listed explanation is present, along with a measured matched-core comparison.

**Acceptance Scenarios**:

1. **Given** the documentation, **When** a user reads the benchmark section, **Then** it explains that GPU cores cannot be limited, that GPU and CPU cores are not equivalent units, and that scaling GPU times (for example multiplying by 2 to emulate 8 GPU cores) is not valid, with the reasons.
2. **Given** the documentation, **When** a user reads it, **Then** it explains that a thread count limits how many threads run, but does not pin them to specific cores such as the 8 performance cores.
3. **Given** completed matched-core runs, **When** the documentation reports them, **Then** it shows the measured Docker CPU, native CPU and native GPU results at the same thread count, without extrapolated values.

### Edge Cases

- A thread count equal to the available cores behaves like the default, but the entry records it as explicitly requested.
- The Docker VM's CPU count is changed between runs. Each entry records the VM CPU count it ran with, and the summary keeps runs with different VM CPU counts apart; historical unverified counts are labeled and kept separate from launcher observations.
- The Docker VM has more CPUs than requested (for example 10 CPUs and 8 threads). The run warns about the mismatch but completes; the extra VM CPUs may still affect timing through other processes.
- The requested count exceeds the native core count (for example 12 on a 10-core Mac). The command fails clearly, as in Docker.
- A results file contains entries from feature 004 and from this feature. All remain valid and readable, and nothing is rewritten.
- Evaluation and prediction keep their existing threading. The option applies to training, including its timed held-out inference pass.
- On a GPU run, the held-out inference pass uses the GPU; only its CPU-side work is limited by the thread count.

## Requirements *(mandatory)*

### Functional Requirements

**Thread-count option**

- **FR-001**: Training MUST accept an optional CPU thread count, a positive integer. Without it, training MUST use all available cores, exactly as in feature 004.
- **FR-002**: A requested count greater than the cores available to the environment MUST fail with a message stating both numbers, before any data is loaded or any checkpoint or results entry is written. Zero, negative and non-integer values MUST fail clearly.
- **FR-003**: When a count is given, CPU computation thread pools used during training, including augmentation, optimization and the timed held-out inference pass, MUST be configured to use no more than that count. Background and system threads may exist. The configured CPU computation thread count MUST be reported at start-up and recorded as the actual thread count.
- **FR-004**: On GPU runs, the thread count MUST limit only CPU-side work. The GPU MUST be used in full, and the application MUST NOT claim or attempt to limit GPU cores.
- **FR-005**: The option MUST apply to training only. Evaluation and prediction MUST keep their existing behavior.

**Docker VM cores**

- **FR-006**: Documentation MUST give the manual steps to set the Docker VM's CPU count (for example to 8), state that this restarts the VM and affects every container on the machine, and show how to restore the previous setting.
- **FR-007**: The application MUST NOT change the Docker VM's configuration.
- **FR-008**: In Docker, when a valid thread count is given and the VM's CPU count differs from it, start-up MUST print a warning naming both numbers and stating that the run is not core-matched, and training MUST proceed. A request exceeding the CPUs available to the process fails under FR-002 and does not also require a mismatch warning.
- **FR-009**: When the Docker VM's CPU count cannot be determined, start-up MUST warn that it could not be verified, and the entry MUST record it as unknown. A container CPU limit alone MUST NOT be treated as the VM CPU count.

**Recording and summary**

- **FR-010**: Each new benchmark entry MUST record the requested thread count (or that the default was used), the thread count actually used, and, for Docker runs, the VM CPU count (or unknown).
- **FR-011**: Entries written by feature 004 MUST remain valid and readable without being rewritten. They MUST be treated as having used the default, with their recorded thread count as the actual count.
- **FR-012**: The summary MUST show the thread count on every row, and MUST NOT average runs that differ in thread count or, for Docker, in VM CPU count. Each distinct combination MUST be its own row, with its own run count. Docker entries with historical unverified allocation MUST be kept separate from launcher-observed allocation even when the recorded counts match.
- **FR-013**: The summary MUST keep feature 004's grouping by dataset, seed, epochs and batch size, its paired training and held-out accuracy, and its "not yet measured" marking for configurations with no entries.
- **FR-014**: GPU rows MUST be labeled as using the whole GPU, with the CPU-side thread count shown separately. GPU times MUST be shown exactly as measured; the summary and documentation MUST NOT scale, extrapolate or otherwise convert them to emulate a different number of GPU cores.

**Documentation**

- **FR-015**: Documentation MUST explain how to run the matched comparison (Docker VM at 8 CPUs, Docker CPU at 8 threads, native CPU at 8 threads, native GPU at 8 CPU-side threads), and that runs must be performed one at a time, as in feature 004.
- **FR-016**: Documentation MUST explain why GPU cores cannot be matched or limited, why GPU and CPU cores are not equivalent units, why scaling GPU times to emulate fewer cores is not valid, and that thread counts do not pin work to specific cores.
- **FR-017**: Documentation MUST report a measured matched-core comparison at the same thread count across the three configurations, with feature 004's caveats.

### Key Entities

- **Thread request**: The optional thread count a user asks for, or the default (all available cores).
- **Thread usage**: The configured CPU computation thread count for a run, reported at start-up and recorded; background and system threads are excluded.
- **Docker VM allocation**: The number of CPUs available to the Docker VM, or unknown; never changed by the application.
- **Benchmark entry (extended)**: Feature 004's entry, plus the thread request and Docker VM CPU count. Older entries stay valid.
- **Summary row (extended)**: One configuration at one thread count and, for Docker, one VM CPU count, with run count and averages.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A training run with an explicit thread count reports and records exactly that count in 100% of runs, and a run without one behaves as in feature 004.
- **SC-002**: Every request for more threads than available fails before writing anything, leaving the checkpoint and results file unchanged.
- **SC-003**: After the documented Docker VM step, a Docker run with a matching thread count completes with no warning, and every valid mismatched run shows a warning; an excessive request fails under FR-002.
- **SC-004**: With Docker CPU, native CPU and native GPU each run at 8 threads on the same data and settings, the summary shows all three at 8 threads, with no row combining different thread counts.
- **SC-005**: A results file containing feature 004 entries is read and summarized without errors and without being modified.
- **SC-006**: The documentation contains every explanation in User Story 4 and a measured matched-core comparison, with no scaled or extrapolated GPU values anywhere in the documentation or summary.

## Assumptions

- The reference machine is the M1 Pro used in feature 004: 10 CPU cores (8 performance, 2 efficiency), a 16-core GPU, and Docker running in a Colima VM (currently 2 CPUs, 4 GiB).
- 8 is the recommended matched count because it equals the number of performance cores, but any count up to the available cores is allowed.
- The Docker VM can be given at most as many CPUs as the Mac has cores. Reconfiguring it is a manual, user-approved action outside the application.
- The matched-core measurements in the documentation are taken after the user has reconfigured the Docker VM. Until then, Docker runs at 8 threads fail clearly, as required.
- Thread pinning to specific cores is out of scope; the operating system decides which cores run the threads.
- Results stay in feature 004's results file. New fields are added in a backward-compatible way, so existing entries remain valid.
- The default epochs, model, preprocessing and dataset are unchanged.
