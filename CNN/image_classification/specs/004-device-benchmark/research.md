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

**Decision**: Hash sorted relative paths and bytes of both validated dataset splits with an unambiguous encoding. Group by this fingerprint, seed, epochs and batch size. Store a versioned JSON document, validate it fully, and serialize readers and writers with an advisory lock on a separate stable file. Under the lock, write a same-directory temporary file and atomically replace the results file only after a successful run; never replace malformed or unsupported input.

**Rationale**: A path is mutable, the held-out set affects measured accuracy, and locking the replaced file itself loses mutual exclusion. Atomic replacement prevents partial JSON and preserves prior entries.

**Alternatives considered**: Path or seed alone as data identity; unlocked append or lock on the replaced inode; silently resetting malformed files. These fail comparison or durability requirements. Shared-volume locking must be validated on the supported Docker/macOS mount.

## Checkpoints and evaluation

**Decision**: Preserve the existing checkpoint schema and CPU state dict; record actual environment and device, validate known provenance values while accepting existing Docker/CPU metadata, and map to CPU before moving to the requested device. Retain the existing preprocessing and train/held-out separation.

**Rationale**: The current format already supports portable weights, but its metadata validator incorrectly demands Docker/CPU.

**Alternatives considered**: Device-specific serialized tensors or ignoring all metadata (portability or validation loss).
