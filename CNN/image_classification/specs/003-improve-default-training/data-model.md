# Data Model: Improve Default Training

## Training configuration

- Fixed comparison: epochs 30, 60, 120; training seed 42; batch size 8; existing optimizer, architecture, transforms and deterministic one-thread CPU settings.
- Production default: selected count, either 30, 60 or 120. A positive integer override remains valid independently.

## Comparison record

- Identity: dataset generator seeds, SHA-256 digest for each sorted training PNG path and contents, image ID and Python/PyTorch versions.
- Before selection: privately retain each candidate's weights, integer training correct count, monotonic epoch-loop elapsed seconds and run status; do not publish training-only counts or accuracy.
- Decision: frozen rule, selected epoch count and timestamp, recorded after candidate measurements and before held-out evaluation without training counts.
- Published candidates: after the decision freeze, one record each of epoch count, training and held-out correct/total counts and accuracy, monotonic epoch-loop elapsed seconds and run status; include the selection rationale and verify training counts match the private measurements.
- A failed candidate is recorded as failed and blocks the selection until resolved; no partial result is treated as successful.

## Final evaluation

- After the decision is recorded, run normal training and collect both training and held-out correct/total counts and accuracy, checkpoint path and repeat-run counts.
- Held-out images and results do not enter the comparison or selection state.

## Checkpoint

- Existing CPU weights and metadata contract remains unchanged; both old compatible checkpoints and newly saved checkpoints work with evaluation and prediction.
