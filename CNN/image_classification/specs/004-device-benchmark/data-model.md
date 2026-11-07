# Data Model: Device Benchmark

## Run context

Requested device is `auto`, `cpu`, or `mps`; resolved device is `cpu` or `mps`. Environment is `docker` or `native`. Context records Python and PyTorch versions and actual CPU training thread count. Docker VM CPU count and memory are positive values when reliably known, otherwise `unknown`; native entries use null for these fields.

## Dataset identity

A SHA-256 fingerprint covers sorted relative paths and file bytes of both validated train and held-out PNGs, with length-delimited records. It identifies the actual comparison data independent of absolute mount paths. Seed, epochs and batch size accompany it; positive epochs and batch size are required.

## Benchmark entry

One completed training run contains a UTC timestamp, run context, dataset fingerprint, seed, epoch count, batch size, final epoch training loss, correct and total counts plus derived accuracy for both splits, warm-up-excluded total and mean epoch seconds, and mean held-out inference seconds per image. Times and loss are finite and nonnegative; counts are valid and totals positive. Both warm-up-excluded values are null for a single epoch. Measurement is completed before the entry is committed.

## Results file

A versioned JSON object contains an ordered array of entries. Missing file means empty collection; malformed JSON, invalid entries or unsupported versions are errors and must remain untouched. With sequential access, a writer reads and validates the entire current document, appends exactly one entry, then atomically replaces the file. Readers resolve pending publication recovery first. Users must not overlap commands accessing the same results or checkpoint; concurrent access is unsupported and is not guaranteed to be detected. An interrupted or failed run before commit creates no entry; results replacement is the commit point. A committed transaction is treated as successful even if termination arrives afterward.

## Comparison group

The key is dataset fingerprint, training seed, epoch count and batch size. Each group includes Docker CPU, native CPU and native MPS rows; each row reports run count and arithmetic means of available timing, final loss and paired accuracy figures. Null timing values are excluded from that metric's mean, with unavailable displayed when none exist. Distinct keys are visibly separate; empty results report no results yet.

## Model provenance

The existing checkpoint holds CPU-resident state dict and metadata: class order, input dimensions, scaling, training and dataset seeds, PyTorch version, environment and device. Validate preprocessing and provenance types/allowed values, but do not require current environment/device to match. Existing feature 002/003 Docker/CPU metadata remains valid.

## Publication transaction

A unique run ID ties the staged checkpoint, preserved prior checkpoint state, staged results and durable recovery journal to one transaction. A durable sidecar at the checkpoint destination identifies the journal so evaluation and prediction can discover pending recovery even when the data directory differs. When the checkpoint and journal are both inside the shared data directory, the checkpoint sidecar records the journal path relative to the sidecar directory. A checkpoint reader resolves it from the sidecar location, including for nested checkpoints and prediction without a data-directory argument; this relative path remains valid under either the Docker mount or the native path. For a checkpoint outside that directory, record an explicit recovery location resolvable in the accessing environment; if it cannot be resolved or accessed, fail clearly and preserve the journal until recovery is possible. No cross-process locking or automatic concurrency detection is required for supported sequential use. States are prepared, checkpoint published, and results committed. Before results commit, recovery restores the old checkpoint or removes the newly created checkpoint; after commit, recovery keeps both outputs and cleans up. A caught results-save error must restore the old checkpoint and fail. If recovery cannot access or restore a destination, preserve the journal, refuse to expose the transaction as complete and report an actionable error until recovery succeeds. The implementation must tolerate arbitrary checkpoint locations for sequential commands.
