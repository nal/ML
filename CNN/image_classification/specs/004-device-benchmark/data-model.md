# Data Model: Device Benchmark

## Run context

Requested device is `auto`, `cpu`, or `mps`; resolved device is `cpu` or `mps`. Environment is `docker` or `native`. Context records Python and PyTorch versions and actual CPU training thread count. Docker VM CPU count and memory are positive values when reliably known, otherwise `unknown`; native entries use null for these fields.

## Dataset identity

A SHA-256 fingerprint covers sorted relative paths and file bytes of both validated train and held-out PNGs, with length-delimited records. It identifies the actual comparison data independent of absolute mount paths. Seed, epochs and batch size accompany it; positive epochs and batch size are required.

## Benchmark entry

One completed training run contains a UTC timestamp, run context, dataset fingerprint, seed, epoch count, batch size, final epoch training loss, correct and total counts plus derived accuracy for both splits, warm-up-excluded total and mean epoch seconds, and mean held-out inference seconds per image. Times and loss are finite and nonnegative; counts are valid and totals positive. Both warm-up-excluded values are null for a single epoch. Measurement is completed before the entry is committed.

## Results file

A versioned JSON object contains an ordered array of entries. Missing file means empty collection; malformed JSON, invalid entries or unsupported versions are errors and must remain untouched. Writers acquire a stable sidecar lock, read and validate the entire current document, append exactly one entry, then atomically replace the file. Readers use the same lock. An interrupted or failed run before commit creates no entry; atomic replacement is the commit point.

## Comparison group

The key is dataset fingerprint, training seed, epoch count and batch size. Each group includes Docker CPU, native CPU and native MPS rows; each row reports run count and arithmetic means of available timing, final loss and paired accuracy figures. Null timing values are excluded from that metric's mean, with unavailable displayed when none exist. Distinct keys are visibly separate; empty results report no results yet.

## Model provenance

The existing checkpoint holds CPU-resident state dict and metadata: class order, input dimensions, scaling, training and dataset seeds, PyTorch version, environment and device. Validate preprocessing and provenance types/allowed values, but do not require current environment/device to match. Existing feature 002/003 Docker/CPU metadata remains valid.
