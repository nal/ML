# Quickstart Validation

Prerequisites: Docker daemon running and a writable host directory. Run from the project root after implementation.

```sh
docker build -t shape-dataset .
mkdir -p data
docker run --rm -v "$PWD/data:/data" shape-dataset
```

Expect 10 images per training class and 5 per held-out class, organized as described in [data-model.md](data-model.md), and the files remain on the host. Run the same command again to check repeat behavior. Unrelated files in the mounted directory remain untouched. This default-run checkpoint can be used before the seed override story is complete; verify counts and preservation at this point.

```sh
docker run --rm -v "$PWD/data:/data" shape-dataset --train-seed 123 --held-out-seed 456
docker run --rm --entrypoint python shape-dataset -m unittest discover -s tests
```

The automated checks must verify counts, PNG dimensions and geometry, per-class variation, color contrast, preservation and collision handling, fault-injected recovery at each publication boundary on first and repeat runs, equal-seed rejection, independent seed changes, and byte-identical output from repeated seeds in the same image. The Docker build includes `tests/` for this command. See [CLI contract](contracts/cli.md) for failure behavior. This small synthetic dataset is a learning demo, not evidence of real-world performance.
