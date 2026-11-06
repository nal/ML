# Implementation Plan: Generate Synthetic Shape Dataset

**Branch**: `feat/001-generate-shape-dataset` | **Date**: 2026-11-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-generate-shape-dataset/spec.md`

## Summary

Generate 45 labeled, filled shape images in two independently seeded sets using Pillow in Docker. Preserve unrelated host files during repeat runs using a validated ownership manifest and recoverable publication journal; enforce per-set variation and test geometry, colors, output, interrupted publication, and byte reproducibility.

## Technical Context

**Language/Version**: Python 3.14.10

**Primary Dependencies**: Pillow 13.0.0, exactly pinned in a shared requirements file; Python standard library

**Storage**: Host-mounted directory with PNG files, an ownership manifest, and a temporary recovery journal

**Testing**: Python unittest, including geometry, filesystem and end-to-end reproducibility checks

**Target Platform**: Docker arm64 Linux, `python:3.14.10-slim`

**Project Type**: Command-line dataset generator

**Performance Goals**: Complete a 45-image run; no latency target specified

**Constraints**: Independent seeds, reproducible bytes in the same pinned environment, safe host persistence

**Scale/Scope**: 30 training and 15 held-out images; no training, evaluation, or MPS

## Constitution Check

- Simplicity: PASS. One generator, standard library and Pillow; manifest is required to preserve unrelated files.
- Reproducibility: PASS. Separate fixed, overridable seeds; pinned runtime and dependency; deterministic iteration and PNG output.
- Honest evaluation: PASS. Separate held-out directory; no training or evaluation included; document demo limitations.
- Shared preprocessing: PASS, not applicable to generation; no training transform introduced.
- Conventional commits: PASS, required for any commits.
- Technical constraints: PASS. Docker default and Pillow; no model dependencies introduced before needed.

**Post-design gate**: PASS. The manifest and staging are justified by safe reruns; no unresolved constitutional violations.

## Project Structure

### Documentation (this feature)

```text
specs/001-generate-shape-dataset/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/cli.md
```

### Source Code (project root)

```text
Dockerfile
requirements.txt
.python-version
pyproject.toml
src/shape_dataset/       # generation and CLI
tests/                   # unit and end-to-end tests
README.md
```

**Structure Decision**: A small single-package CLI with tests; the mounted data directory is runtime output, not source.

## Complexity Tracking

| Added complexity | Why needed | Simpler alternative rejected |
|---|---|---|
| Ownership manifest, staged files, recovery journal and advisory lock | Identify owned files, preserve unrelated files and resume interrupted publication while serializing writers. | Replacing fixed paths in place cannot distinguish unrelated files and can leave partial output without recovery information. |
