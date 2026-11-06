# Research: CNN Training, Evaluation, and Prediction

## Dependencies and runtime

**Decision**: Keep Python 3.14.10 and Pillow 13.0.0; pin `torch==2.15.0+cpu`, `torchvision==0.29.2+cpu`, `numpy==2.5.4` and all transitive packages exactly in the existing shared requirements file. Resolve CPU-tagged wheels from the official CPU index and other packages from PyPI. Validate a clean Docker build, `pip check`, imports and a transforms/model smoke test on arm64 before implementation is considered complete.

**Rationale**: The [official CPU torch wheel index](https://download.pytorch.org/whl/cpu/torch/) lists the Linux aarch64 Python 3.14 CPU build and the [torchvision CPU index](https://download.pytorch.org/whl/cpu/torchvision/) lists 0.29.2 CPU builds. [PyPI metadata](https://pypi.org/pypi/torchvision/0.29.2/json) declares torch ≥2.14 and excludes Python 3.14.1, not 3.14.10. Metadata alone does not prove the resolved binaries work together.

**Alternatives considered**: Unpinned dependencies violate reproducibility; generic PyPI torch builds can resolve unwanted accelerator packages.

## CLI compatibility

**Decision**: Preserve `python -m shape_dataset` as the Docker entrypoint and existing direct flags; use `docker run --entrypoint python ... -m shape_classifier {train,evaluate,predict}` for classifier operations.

**Rationale**: Existing generator users and docs keep working, and the classifier has an explicit interface without a migration.

**Alternatives considered**: Replacing the default entrypoint with required subcommands breaks feature 001 invocation.

## Preprocessing and augmentation

**Decision**: Convert decoded images to RGB, apply a shared v2 pipeline `Resize((144, 256))`, `ToImage()`, `ToDtype(torch.float32, scale=True)` without normalization; cache each training tensor once. Apply training-only random rotation ±10°, horizontal and vertical flips with probability 0.5 each, and brightness/contrast/saturation jitter 0.1 to cached tensors. Keep evaluation and prediction unaugmented.

**Rationale**: Matches the supplied contract; [torchvision documentation](https://docs.pytorch.org/vision/stable/transforms.html) describes the v2 transforms and scaled float range. Fixed small magnitudes are a documented starting point, not a claim of optimality.

**Alternatives considered**: Per-epoch image loading violates the cache requirement; augmentation during evaluation distorts the accuracy measurement.

## Training and honest evaluation

**Decision**: Use seed 42, 30 epochs, batch size 8 and Adam learning rate 0.001 by default, overridable for epochs, batch size and seed. Seed Python, NumPy and torch before model/loader creation; use one CPU thread and deterministic algorithms where available. Use two convolution/ReLU/pooling blocks followed by adaptive average pooling and a three-class linear head. Evaluate unaugmented training cache and held-out data after the final epoch with evaluation mode and no gradients; never use held-out results for checkpoint selection.

**Rationale**: This is a small, reproducible starting point with separate final assessment. Deterministic settings reduce variability but do not promise identical results across builds or platforms ([PyTorch reproducibility documentation](https://docs.pytorch.org/docs/stable/notes/randomness.html)). Check SC-004 against repeated runs in the same built image.

**Alternatives considered**: Early stopping on held-out accuracy violates the constitution; a more elaborate architecture or tuning process exceeds scope.

## Checkpoint and provenance

**Decision**: Save a single CPU state dict and primitive metadata (`str(torch.__version__)`, plain strings, integers and lists); load with `weights_only=True`, validate expected fields, preprocessing and class order, and reject incompatible checkpoints. Optional dataset-seed flags default independently to `unknown`; do not infer them from generator defaults because the existing manifest does not store seeds. Save atomically to `/data/shapes.pth`.

**Rationale**: The weights-only contract enables portable loading, while metadata makes prediction interpretation explicit. See [PyTorch serialization guidance](https://docs.pytorch.org/docs/stable/notes/serialization.html#torch-load-with-weights-only-true).

**Alternatives considered**: Loading arbitrary serialized model objects or inventing seed provenance is unsafe or misleading.
