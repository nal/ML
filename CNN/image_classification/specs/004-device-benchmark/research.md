# Research: Device Benchmark

## Device resolution

**Decision**: Detect the container environment, force `auto` to CPU there, and probe MPS availability and a small actual operation on native hosts. Resolve before loading or writing outputs; explicit unusable MPS fails with an actionable error. Move model, inputs and labels to the resolved device.

**Rationale**: Availability alone may not establish usability, and a silent fallback invalidates results. Existing CLI currently reports Docker and CPU unconditionally.

**Alternatives considered**: Trust `is_available()` alone; silently fall back for explicit MPS. Neither satisfies the failure and usability requirements.

## Shared dependencies

**Decision**: Keep one exact-version requirements source with platform markers selecting Linux CPU and native macOS standard PyTorch builds. Verify resolved installed versions and `pip check` in each environment, including all transitive pins. Use the pinned Python version and existing Docker image.

**Rationale**: Current `+cpu` pins are unsuitable on macOS; platform-specific wheel builds allow one version inventory.

**Alternatives considered**: Separate requirements files (drift risk); generic Linux torch wheel (may not be CPU-only). Wheel availability and the resolver must be verified on both target platforms during implementation.

## Threads and timing

**Decision**: Determine CPUs actually available to the process using affinity and applicable cgroup limits where reliably discoverable, use that count for CPU training threads, and report the resulting PyTorch thread count. Record Docker VM resources only when reliably discoverable, otherwise `unknown`. Synchronize MPS before and after every timed interval; exclude the complete first epoch. Time a separate held-out inference pass, divided by image count, without including training assessment.

**Rationale**: Host CPU counts can misstate container limits; queued GPU operations otherwise understate duration. One epoch yields null excluded times.

**Alternatives considered**: One thread (contradicts clarified requirement); wall clock without synchronization (misleading); infer VM allocation from host counts (unreliable).

## Comparable, durable results

**Decision**: Hash sorted relative paths and bytes of both validated dataset splits with an unambiguous encoding. Group by this fingerprint, seed, epochs and batch size. Store a versioned JSON document and validate it fully. Require users to run all commands accessing the shared results or checkpoint sequentially; overlapping access is unsupported and need not be detected. Write a same-directory temporary file and atomically replace the results file only after a successful run; never replace malformed or unsupported input.

**Rationale**: A path is mutable and the held-out set affects measured accuracy. Atomic replacement prevents partial JSON and preserves prior entries in supported sequential use. A native macOS exclusive advisory lock and a Docker process using the Colima shared mount both acquired the same lock in an observed test, so that mechanism cannot coordinate cross-environment writers.

**Alternatives considered**: Path or seed alone as data identity; in-place append; silently resetting malformed files; advisory locks as a cross-environment concurrency guarantee. These fail comparison or durability requirements or do not work on the tested mount. Supported use deliberately excludes overlapping access.

## Checkpoints and evaluation

**Decision**: Preserve the existing checkpoint schema and CPU state dict; record actual environment and device, validate known provenance values while accepting existing Docker/CPU metadata, and map to CPU before moving to the requested device. Retain the existing preprocessing and train/held-out separation.

**Rationale**: The current format already supports portable weights, but its metadata validator incorrectly demands Docker/CPU.

**Alternatives considered**: Device-specific serialized tensors or ignoring all metadata (portability or validation loss).

## Publishing checkpoint and results

**Decision**: Stage the CPU checkpoint in its destination directory and the validated updated JSON in the results directory. For sequential access, preserve the old checkpoint (or its absence) and record a recoverable transaction before publishing. Publish the checkpoint first and atomically replace the results last; that replacement is the success commit point. If results publication fails, restore the previous checkpoint or remove the newly created one and report failure. Defer ordinary termination signals across the short publication section; before the commit point an interruption leaves no result entry, while after it the run is committed. On subsequent access, recover an incomplete transaction before exposing outputs, assuming no other command is accessing those outputs. When checkpoint and journal are both inside the shared data directory, record the journal path relative to the checkpoint sidecar directory; readers resolve it from the sidecar without requiring a data-directory argument, even for nested checkpoints, across Docker and native mounts. For checkpoints outside the shared directory, retain an explicit recovery location; if it is not resolvable in the accessing environment, fail clearly and preserve recovery information until it is accessible. Use unique run identifiers in the journal and results to distinguish committed transactions during recovery. Do not report successful rollback if restoration fails; retain recovery information and report an actionable error.

**Rationale**: The clarified requirement protects an existing checkpoint when results cannot be saved, while existing checkpoint paths may be outside the data directory or on another filesystem. Two separate file replacements are not a single atomic operation; a durable journal and recovery are necessary for abrupt termination. Recovery cannot restore a checkpoint while its filesystem is inaccessible, so fail clearly and retry recovery when accessible. Avoid claiming instantaneous two-file atomicity.

**Alternatives considered**: Results first can leave an entry for a failed checkpoint write; checkpoint first without backup changes the checkpoint on a results error; plain rollback without a journal loses recovery information after a crash. A database or mandatory relocation of existing checkpoint paths adds dependencies or breaks the existing CLI.
