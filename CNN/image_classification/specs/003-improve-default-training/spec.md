# Feature Specification: Improve Default Training

**Feature Branch**: `feat/003-improve-default-training`

**Created**: 2026-11-06

**Status**: Draft

**Input**: User description: "Decide on the weak model. You can open a small follow-up feature to raise the default number of training epochs"

## Clarifications

### Session 2026-11-06

- Q: What should happen if longer training does not improve the training-set result enough to justify its extra time? → A: Keep the 30-epoch default and document the comparison.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Train with a more effective default (Priority: P1)

A user runs training without specifying the number of epochs and gets a model trained with an evidence-informed default. The default increases beyond the current 30 epochs only if the training comparison justifies its extra time. The result still reports both training and held-out accuracy and saves a reusable checkpoint.

**Why this priority**: The current default produced only 16 correct out of 30 training examples and 7 out of 15 held-out examples in the observed run. A longer default is a small, understandable change to investigate underfitting.

**Independent Test**: Run default training on the existing generated data, verify the documented selected epoch count is used, the checkpoint persists, and both complete accuracy reports are shown.

**Acceptance Scenarios**:

1. **Given** both valid dataset splits, **When** a user trains without an epoch override, **Then** training uses the documented selected default and reports training and held-out correct counts and accuracy together.
2. **Given** a successful default run, **When** the user evaluates its saved model, **Then** the model loads successfully and evaluation reports both splits.
3. **Given** the same dataset, seed, configuration and environment, **When** the user repeats default training, **Then** the correct counts differ by no more than one image per split.

### User Story 2 - Control and understand training duration (Priority: P2)

A user can retain a shorter run or choose another positive epoch count and understand the tradeoff between extra training and elapsed time.

**Why this priority**: A higher epoch count consumes more time, and existing users need control over that cost.

**Independent Test**: Specify a positive epoch override and verify the requested count is used; verify invalid counts fail clearly and documentation describes the default and override.

**Acceptance Scenarios**:

1. **Given** a positive epoch override, **When** training starts, **Then** it uses that count instead of the default.
2. **Given** zero, a negative value or a non-integer epoch count, **When** training is requested, **Then** the command fails clearly without a successful result.
3. **Given** the training instructions, **When** a user reads them, **Then** they can find the selected default, the override and the observed time tradeoff.

### Edge Cases

- A longer run may fail or be interrupted; it must not be reported as a successful completed run.
- Additional epochs may not improve held-out accuracy, or may make it worse; report the actual result without claiming generalization.
- Existing checkpoint loading, prediction, and explicitly configured training runs remain compatible.
- Missing or invalid datasets and unwritable checkpoint paths continue to fail clearly.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The default training run MUST use a documented fixed number of epochs selected using training-set evidence and a practical training-duration tradeoff. Increase the default beyond 30 only if the comparison justifies the extra time; otherwise retain 30 and document the finding.
- **FR-002**: The choice of default MUST compare the existing 30-epoch baseline with at least one longer candidate under the same generated training data, seed and other training settings. Record candidate epoch counts, training correct counts and elapsed training time; select a fixed default before inspecting held-out results for the candidates.
- **FR-003**: Held-out data MUST NOT influence training, augmentation, model selection or selection of the default epoch count. After the choice is fixed, report its training and held-out correct counts and accuracy together, including unfavorable results.
- **FR-004**: Users MUST be able to override the epoch count with any positive integer, including the previous default of 30. Invalid counts MUST fail clearly.
- **FR-005**: Training MUST continue to save a reusable checkpoint only after a successful run, and existing compatible checkpoints MUST continue to work for evaluation and prediction.
- **FR-006**: Default training MUST retain the existing fixed seed, shared preprocessing, training-only augmentation, paired accuracy reporting and CPU reproducibility behavior.
- **FR-007**: Documentation MUST state the chosen default, how to override it, the observed training-time tradeoff and the limitations of the small synthetic dataset and 15-image held-out set.
- **FR-008**: The feature MUST preserve existing dataset generation, evaluation and prediction interfaces; changes to model architecture, dataset generation and device support are outside scope.

### Key Entities

- **Training configuration**: Epoch count, seed and existing training settings, including the default and user override.
- **Training comparison**: Fixed dataset and settings, candidate epoch counts, training correct counts, elapsed time and the selection decision.
- **Evaluation result**: Paired training and held-out correct counts and accuracy for the chosen default.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A default run completes using the documented selected count, saves a reusable model and reports results for all 30 training and 15 held-out images.
- **SC-002**: The documented comparison includes the 30-epoch baseline and at least one longer candidate, with a recorded training count and elapsed time for each; the chosen default is fixed before held-out results are inspected.
- **SC-003**: A user can explicitly run 30 epochs and another positive count, while zero, negative and non-integer counts are rejected.
- **SC-004**: Two default runs with the same dataset, seed, settings and environment differ by at most one correct image on each split.
- **SC-005**: Evaluation and prediction work with a compatible existing checkpoint and the new default checkpoint; all successful accuracy reports include both splits.

## Assumptions

- The observed 16/30 training and 7/15 held-out result is a baseline observation, not a guarantee for every generated dataset.
- A longer run is a plausible way to address underfitting, but improvement is not guaranteed; if training-only evidence does not justify a longer default, record that finding rather than misrepresenting improvement.
- The existing 30/15 generated dataset and CPU runtime are available. The held-out set is too small to support a reliable claim of real-world improvement.
- The exact epoch count is intentionally determined during planning and validation from training-only evidence rather than guessed in this specification.
