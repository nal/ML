# Data Model: Device Benchmark

## Run context

Requested device is `auto`, `cpu`, or `mps`; resolved device is `cpu` or `mps`. Environment is `docker` or `native`. Context records Python and PyTorch versions and actual CPU training thread count. Docker VM CPU count and memory are positive values when reliably known, otherwise `unknown`; native entries use null for these fields.

## Dataset identity

A SHA-256 fingerprint covers sorted relative paths and file bytes of both validated train and held-out PNGs, with length-delimited records. It identifies the actual comparison data independent of absolute mount paths. Seed, epochs and batch size accompany it; positive epochs and batch size are required.

## Benchmark entry

One completed training run contains a UTC timestamp, run context, dataset fingerprint, seed, epoch count, batch size, final epoch training loss, correct and total counts plus derived accuracy for both splits, warm-up-excluded total and mean epoch seconds, and mean held-out inference seconds per image. Times and loss are finite and nonnegative; counts are valid and totals positive. Both warm-up-excluded values are null for a single epoch. Measurement is completed before the entry is committed.

## Results file

A versioned JSON object contains an ordered array of entries. Missing file means empty collection; malformed JSON, invalid entries or unsupported versions are errors and must remain untouched. Writers acquire a stable sidecar lock, read and validate the entire current document, append exactly one entry, then atomically replace the file. Readers use the same lock and resolve pending publication recovery first. An interrupted or failed run before commit creates no entry; results replacement is the commit point. A committed transaction is treated as successful even if termination arrives afterward.

## Comparison group

The key is dataset fingerprint, training seed, epoch count and batch size. Each group includes Docker CPU, native CPU and native MPS rows; each row reports run count and arithmetic means of available timing, final loss and paired accuracy figures. Null timing values are excluded from that metric's mean, with unavailable displayed when none exist. Distinct keys are visibly separate; empty results report no results yet.

## Model provenance

The existing checkpoint holds CPU-resident state dict and metadata: class order, input dimensions, scaling, training and dataset seeds, PyTorch version, environment and device. Validate preprocessing and provenance types/allowed values, but do not require current environment/device to match. Existing feature 002/003 Docker/CPU metadata remains valid.

## Publication transaction

A unique run ID ties the staged checkpoint, preserved prior checkpoint state, staged results and durable recovery journal to one transaction. A durable sidecar at the checkpoint destination identifies the journal so evaluation and prediction can discover pending recovery even when the data directory differs. Lock both results and checkpoint destinations in a consistent order; all classifier checkpoint readers participate in the checkpoint lock. States are prepared, checkpoint published, and results committed. Before results commit, recovery restores the old checkpoint or removes the newly created checkpoint; after commit, recovery keeps both outputs and cleans up. A caught results-save error must restore the old checkpoint and fail. If recovery cannot access or restore a destination, preserve the journal, refuse to expose the transaction as complete and report an actionable error until recovery succeeds. The implementation must tolerate arbitrary checkpoint locations and concurrent runs sharing a checkpoint.
