# Quickstart Validation

Use a fresh, writable host directory; generated files and checkpoints are overwritten only in that directory. Preserve a compatible feature 002 checkpoint separately for regression testing, or preserve the unchanged feature 002 image before modifying the code so it can generate that checkpoint after the decision is frozen.

```sh
docker build -t shape-classifier .
mkdir -p data-feature-003
docker run --rm -v "$PWD/data-feature-003:/data" shape-classifier --train-seed 42 --held-out-seed 43
```

Before looking at candidate held-out results, follow [research.md](research.md) using a temporary training-only harness and record the predeclared protocol in `comparison.md`. Verify the harness never accesses the held-out split and matches the production optimization loop. Keep candidate counts, times and weights private without emitting unpaired accuracy; freeze only the selected default and timestamp in the record before proceeding. Then evaluate each saved candidate on both splits and publish paired counts and accuracies, loop times, environment, data identity and rationale. Confirm the training counts match the private selection measurements. If the separate feature 002 checkpoint is unavailable, create it with unchanged 30-epoch code only after the freeze.

After applying the selected default, rebuild and validate the production flow:

```sh
docker build -t shape-classifier .
docker run --rm -v "$PWD/data-feature-003:/data" --entrypoint python shape-classifier -m shape_classifier train --checkpoint /data/first.pth
docker run --rm -v "$PWD/data-feature-003:/data" --entrypoint python shape-classifier -m shape_classifier train --checkpoint /data/second.pth
docker run --rm -v "$PWD/data-feature-003:/data" --entrypoint python shape-classifier -m shape_classifier evaluate --checkpoint /data/first.pth
docker run --rm -v "$PWD/data-feature-003:/data" --entrypoint python shape-classifier -m shape_classifier predict /data/held-out/circle/01.png --checkpoint /data/first.pth
docker run --rm --entrypoint python shape-classifier -m unittest discover -s tests
docker run --rm --entrypoint python shape-classifier -m pip check
```

Both training runs report 30 and 15 totals together; correct counts differ by no more than one per set. Test explicit 30 and another positive epoch count, reject zero, negative and non-integer values, and evaluate and predict with the separate existing checkpoint. Confirm CLI and Python defaults agree, the generator still works and README documents the observed timing and small-data caveats. See [CLI contract](contracts/cli.md) and [data model](data-model.md).
