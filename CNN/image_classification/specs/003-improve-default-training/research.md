# Research: Improve Default Training

## Evidence and decision rule

**Decision**: Before running candidates, fix counts at 30, 60 and 120 epochs. Use one fixed generated training split, training seed 42, batch size 8 and the existing optimizer, architecture, transforms, ordering, CPU thread and deterministic settings. Measure only the epoch-loop elapsed wall time using a monotonic clock; separately measure unaugmented training correct counts after each run. Choose the shortest longer candidate whose count is at least 3 higher than the 30-epoch baseline and whose loop time is at most four times the baseline. If none qualifies, retain 30. Record failures as failures; do not substitute a passing candidate or invent timings.

**Rationale**: Three images correspond to 10 percentage points on this tiny training set and distinguish the candidate from a one-image fluctuation; a fourfold time bound limits the cost of the longer run. These are explicit engineering decision thresholds, not evidence of generalization or statistical significance. Selecting the shortest qualifying candidate bounds cost and avoids post-hoc tuning.

**Alternatives considered**: Always raising the count would disregard the user's fallback decision. Picking the highest held-out accuracy would use the held-out set for selection. Selecting by training count without a cost bound could make defaults unnecessarily slow.

## Isolated comparison

**Decision**: Run candidates using a temporary training-only harness that reuses the existing training dataset, model and augmentation and mirrors the real training loop. It must never instantiate or read the held-out dataset or overwrite user checkpoints. Keep candidate weights and raw training counts in private temporary storage, with no training-only accuracy or correct/total reports in logs, messages or versioned files. Predeclare candidates and the rule in the comparison record; record the selected count and a timestamped decision freeze without counts before any held-out evaluation. After the freeze, evaluate the saved weights for every candidate on both splits and publish each candidate's paired training and held-out correct/total counts and accuracies, alongside loop time and selection rationale. Verify the post-freeze training counts match the private selection measurements. Record generator seeds, hashes of sorted training PNGs, training configuration, image identity and runtime details. Failed or mismatched measurements block completion rather than changing the frozen decision based on held-out results.

**Rationale**: The existing `train()` assesses both sets and would expose held-out candidate results before selection. An isolated harness can prevent this while retaining the existing production paired-reporting contract.

**Alternatives considered**: Suppressing normal CLI output is insufficient because it still computes held-out results; changing the public CLI to expose an unpaired assessment weakens the existing contract.

The earlier 30-epoch run's held-out result is already known from feature 002, so the held-out set is not pristine. Do not use that observation, or any new held-out result, to choose the candidate; report this limitation with the final results.

## Validation and compatibility

**Decision**: Once the selection is fixed, update both the CLI and Python `train()` defaults if needed. Run the selected default twice on the same data and image, compare counts within one per split, and test explicit epoch overrides, invalid inputs, evaluation and prediction with an existing and newly created checkpoint. If no existing feature 002 checkpoint is available, preserve its unchanged image before modifications and generate one using that image's 30-epoch code only after the selection is fixed. Document measured cost and limitations.

**Rationale**: Both default definitions are currently independently specified; changing one alone creates inconsistent behavior. Paired evaluation and a fresh-process load test preserve feature 002 guarantees.

**Alternatives considered**: Choosing the value solely from an earlier observed run would not compare candidates under controlled conditions.
