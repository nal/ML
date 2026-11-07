# Implementation Plan: Matched-Core Benchmark

**Branch**: `006-matched-core-benchmark` | **Date**: 2026-11-07 | **Spec**: [spec.md](spec.md)

## Summary

Extend training with a validated CPU computation thread count, preserve all-core defaults, record the request alongside existing actual count, and split benchmark rows by thread and Docker VM allocation. A host-side Colima launcher obtains the running VM allocation and checks the Docker endpoint before passing the observation into the container; ordinary containers without verifiable host evidence report unknown. Measure and document the three configurations sequentially without GPU scaling.

## Technical Context

**Language/Version**: Python 3.14.10; shell for the host launcher  
**Primary Dependencies**: Existing pinned PyTorch, torchvision, Pillow and NumPy; Colima and Docker for the optional host workflow; no new Python dependency  
**Storage**: Existing version-1 JSON benchmark results and transactional checkpoint publication  
**Testing**: `unittest`, CLI and Docker integration checks; native Apple Silicon and MPS acceptance runs  
**Target Platform**: arm64 Docker CPU and native Apple Silicon macOS CPU/MPS  
**Project Type**: Python CLI with a host-side benchmark launcher  
**Performance Goals**: Report measured timings; no speedup target or extrapolation  
**Constraints**: Validate before data access or publication/recovery writes; preserve feature 004 data and defaults, paired accuracies, and sequential-access rules; thread settings apply only to training; do not modify Colima configuration from the application  
**Scale/Scope**: Small synthetic dataset, three environments, repeated local runs.

## Constitution Check

| Principle | Before research | After design |
|---|---|---|
| Simplicity | Pass: extend existing paths. | Pass: one small host launcher is needed to obtain evidence unavailable inside the container; no new dependency. |
| Reproducibility | Pass: retain seeds and pinned dependencies. | Pass: report thread counts and resource provenance; document scheduling and MPS limits. |
| Honest Evaluation | Pass: retain held-out reporting and measured timings. | Pass: separate resource configurations and report whole-GPU measurements unchanged. |
| Shared Preprocessing | Pass: retain existing pipeline. | Pass: no preprocessing or checkpoint schema change. |
| Conventional Commits | Pass: hooks apply. | Pass: no bypass planned. |

Gate: PASS before research and after design. No exceptions required.

## Project Structure

```text
src/shape_classifier/__main__.py  # training option, early validation and reporting
src/shape_classifier/device.py    # process availability and conservative VM evidence
src/shape_classifier/train.py     # training pool setup and benchmark entry
src/shape_classifier/benchmark.py # compatible validation, grouping and display
src/shape_classifier/publication.py # existing transactional publication
scripts/                           # host-side Colima benchmark launcher
tests/                             # CLI, device, results and benchmark tests
README.md                          # manual VM configuration, runs and results
specs/006-matched-core-benchmark/  # plan, research, data model, contract, quickstart
```

**Structure Decision**: Extend existing modules and publication protocol. The launcher queries Colima on the host, verifies the active Docker endpoint corresponds to the selected running Colima profile, and transports the observed count and provenance to its container invocation. If identity or observation is uncertain it supplies no count; the application warns and stores unknown. Never infer a VM count from container CPU visibility alone. Treat transported evidence as an observation from the launcher, not a security boundary; document that VM configuration and Docker context must not change during a run.

## Complexity Tracking

No constitution violations require justification.
