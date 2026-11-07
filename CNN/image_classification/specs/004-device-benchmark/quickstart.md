# Quickstart: Device Benchmark Validation

These commands validate the feature after implementation. Prerequisites: Docker with an arm64 Linux runtime, Apple silicon macOS 15+ with usable MPS for the GPU scenarios, and `uv` for native setup. Run from the project directory. See [CLI contract](contracts/cli.md) and [data model](data-model.md) for output and measurement semantics.

## Docker baseline

```sh
docker build -t shape-classifier .
mkdir -p data
docker run --rm -v "$PWD/data:/data" shape-classifier
docker run --rm --entrypoint python shape-classifier -m unittest discover -s tests
docker run --rm --entrypoint python shape-classifier -m pip check
docker run --rm -v "$PWD/data:/data" --entrypoint python shape-classifier -m shape_classifier train --device cpu
```

Expect Docker/CPU and versions at startup, paired accuracies, a checkpoint and one results entry. Repeat training to verify a second entry. Run the following with `train`, `evaluate`, and `predict` (include the image path for prediction); each must fail clearly without changing the checkpoint or results:

```sh
docker run --rm -v "$PWD/data:/data" --entrypoint python shape-classifier -m shape_classifier train --device mps
```

## Native setup and comparison

```sh
brew install python@3.14  # or brew upgrade python@3.14
/opt/homebrew/bin/python3.14 --version  # must be 3.14.10
uv venv --python /opt/homebrew/bin/python3.14
uv pip install --index-strategy unsafe-best-match -r requirements.txt
uv pip install --no-build-isolation --no-deps .
uv pip check
.venv/bin/python -m shape_classifier train --data-dir "$PWD/data" --checkpoint "$PWD/data/shapes.pth" --device cpu
.venv/bin/python -m shape_classifier train --data-dir "$PWD/data" --checkpoint "$PWD/data/shapes.pth" --device mps
.venv/bin/python -m shape_classifier summary --data-dir "$PWD/data"
```

Verify Python and installed package versions against Docker, allowing only the documented PyTorch platform build difference. The summary should show three rows in the same group with counts, warm-up-excluded timing, inference, loss and paired accuracies. Repeat with `--epochs 1`: excluded timings must be unavailable, not zero. Run `auto` natively and in Docker to verify actual device reporting. Evaluate a native-trained checkpoint in Docker and a previously saved feature 002/003 checkpoint natively; predict with both. Use explicit `--checkpoint` for native evaluation and prediction.

Run Docker CPU, native CPU and native MPS training one at a time, waiting for each command to finish; then verify all entries survive in valid JSON. Do not overlap training, summary, evaluation or prediction commands that access the same results or checkpoint: concurrent access is unsupported and may not be detected. Test summary with a missing file, and test summary and training with a malformed or unsupported file: it must remain unchanged. Verify results-publication failures using the automated failure-injection tests: existing checkpoint bytes and prior results must remain unchanged, including when no checkpoint existed initially. Exercise interrupted publication before and after the results commit point and verify recovery on the next sequential command; test shared and separate checkpoint paths, including recovery across Docker and native mounts. An inaccessible recovery destination must produce a clear error and retain recovery information. A GPU slowdown is a valid measurement. Compare repeat CPU results and document observed variation; arithmetic and thread scheduling can differ, VM resources may be smaller, and this small synthetic dataset does not establish real-world performance.
