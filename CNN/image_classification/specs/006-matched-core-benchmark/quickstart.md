# Quickstart: Matched-Core Validation

Run from the project directory after implementation. Use the same generated dataset, seed, epochs and batch size for every run. Run commands one at a time. Preserve existing results and checkpoints before destructive test setup.

1. Build the existing classifier image and native environment using README instructions. Run `docker run --rm --entrypoint python shape-classifier -m unittest discover -s tests`. Verify thread validation, pool configuration, legacy results, grouping, VM evidence and publication tests pass.
2. On the host, inspect `colima list` and record the active profile's current CPU allocation. Follow the implemented README host-launcher instructions to stop the VM and restart it with 8 CPUs; this affects all containers. Confirm the Docker endpoint still matches that profile. The launcher must query and verify the allocation; do not manually substitute container-visible CPU counts.
3. Run Docker CPU through the documented launcher with `--cpu-threads 8`, then native CPU and native MPS sequentially:

   ```sh
   .venv/bin/python -m shape_classifier train --data-dir "$PWD/data" --checkpoint "$PWD/data/shapes.pth" --device cpu --cpu-threads 8
   .venv/bin/python -m shape_classifier train --data-dir "$PWD/data" --checkpoint "$PWD/data/shapes.pth" --device mps --cpu-threads 8
   .venv/bin/python -m shape_classifier summary --data-dir "$PWD/data"
   ```

   Confirm each reports 8 CPU-side threads, Docker reports verified VM allocation 8, and MPS is whole-GPU. Record actual measured results and caveats in README; never scale GPU times. Native MPS checks require a usable Apple GPU.
4. On the 8-CPU VM run the launcher with 4 threads: verify a mismatch warning and successful entry. Test a direct Docker run without host evidence: verify unknown and warning. Verify an excessive count, zero, negative and non-integer fail before changing checkpoint or results; also verify an omitted count uses the default.
5. Summarize a copy containing legacy and new entries. Confirm separate rows by actual thread and Docker allocation, default/explicit/mixed markers, paired accuracies, and no file changes from summary. Restore the VM's previous CPU allocation using the README procedure after testing.

See [CLI contract](contracts/cli.md) and [data model](data-model.md) for detailed expectations. Tests that configure inter-op threads must use fresh processes where required by PyTorch.
