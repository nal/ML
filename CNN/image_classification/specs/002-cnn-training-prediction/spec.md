# Feature Specification: CNN Training, Evaluation, and Prediction

**Feature Branch**: `feat/002-cnn-training-prediction`

**Created**: 2026-11-06

**Status**: Implemented

**Input**: Train, evaluate, and use a small CNN on the synthetic shape dataset from feature 001, using the evaluation, image processing and model, and saved-result requirements in `CNN_image_classification_research.md`.

## Clarifications

### Session 2026-11-06

- Q: How should training record the dataset seeds when the existing dataset does not include them? → A: Accept optional flags for each dataset seed and record omitted values as unknown.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Train a classifier and assess it (Priority: P1)

A user trains a classifier on the existing synthetic training images, receives an honest paired report of training and held-out accuracy, and saves the trained model for later use.

**Why this priority**: Training produces the model, and paired evaluation makes its limitations visible from the first run.

**Independent Test**: Generate or provide both sets, run training in the container, and verify the paired accuracy report and reusable saved model on the host.

**Acceptance Scenarios**:

1. **Given** the feature 001 training and held-out sets are available, **When** the user trains the model, **Then** the run uses only training images to update the model and reports both training and held-out accuracy together.
2. **Given** a completed training run, **When** the container exits, **Then** the saved model and required metadata remain available in the host-mounted data directory.
3. **Given** the same inputs, seed, configuration, and container image, **When** the user repeats CPU training, **Then** results are nearly identical within documented reproducibility limits.

### User Story 2 - Evaluate a saved classifier (Priority: P2)

A user loads a previously saved model and checks its accuracy on both sets without retraining.

**Why this priority**: Evaluation must be repeatable independently of the training session and must distinguish memorization from held-out performance.

**Independent Test**: Run evaluation against an existing compatible checkpoint and both datasets; compare the displayed counts and paired accuracy with predictions on the same images.

**Acceptance Scenarios**:

1. **Given** a compatible checkpoint and both sets, **When** the user runs evaluation, **Then** training and held-out accuracy and their correct/total counts appear together.
2. **Given** a missing or unreadable held-out set, **When** the user runs evaluation, **Then** the command fails clearly rather than reporting training accuracy alone as a successful evaluation.

### User Story 3 - Predict the shape in an image (Priority: P3)

A user supplies an image and saved model to obtain a predicted shape label without retraining.

**Why this priority**: Prediction makes the saved classifier useful beyond reporting accuracy on the supplied dataset.

**Independent Test**: Run prediction with an existing checkpoint and a readable image; verify that the reported label is one of the three supported classes.

**Acceptance Scenarios**:

1. **Given** a compatible checkpoint and a readable image, **When** the user runs prediction, **Then** the result identifies the predicted class as circle, rectangle, or triangle.
2. **Given** an invalid image or missing or incompatible checkpoint, **When** the user requests a prediction, **Then** the command fails with a clear explanation and does not claim a prediction.

### Edge Cases

- Missing, empty, unreadable, malformed, or incorrectly labeled training or held-out data causes a clear failure; a run must not silently omit invalid images or report a successful partial evaluation.
- A missing, corrupt, incompatible, or incomplete checkpoint fails clearly rather than loading an incorrect model or preprocessing configuration.
- An invalid training seed or invalid training configuration is rejected with an actionable error.
- An unwritable checkpoint destination produces a clear failure; the user is not told the model was saved successfully.
- A non-RGB input image is converted consistently to RGB before shared preprocessing, or rejected clearly if it cannot be decoded.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide separate command-line operations for training, evaluation, and prediction that run on CPU inside Docker and use feature 001's set/class directory layout.
- **FR-002**: Training MUST use the existing training set of 10 labeled images per class and the mandatory held-out set of 5 per class; held-out images MUST NOT be used for training, augmentation, or model selection.
- **FR-003**: Training, evaluation, and prediction MUST use one shared preprocessing definition: RGB input resized to 256 × 144 pixels (width × height), then converted with `ToImage()` and `ToDtype(torch.float32, scale=True)` to values in [0, 1], without additional normalization; the resize operation MUST use `Resize((144, 256))` (height, width).
- **FR-004**: Training MUST load and resize each training image once per run and cache the resulting tensors in memory instead of rereading or resizing them each epoch.
- **FR-005**: Each training epoch MUST apply light random rotation, horizontal and vertical flips, and slight color jitter to training inputs; evaluation and prediction MUST NOT apply augmentation.
- **FR-006**: The classifier MUST use two or three convolution/ReLU/pooling blocks, adaptive average pooling, and three outputs; training MUST use cross-entropy loss and Adam.
- **FR-007**: Training MUST use a fixed default seed, independently overridable by a command-line flag, to control Python, NumPy, and PyTorch randomness, including initialization, data ordering, and augmentation.
- **FR-008**: Wherever accuracy is reported, training and held-out accuracy MUST be reported together, identifying each set and its correct and total image counts; evaluation MUST be performed without training augmentation.
- **FR-009**: Training MUST save a single `shapes.pth` checkpoint to a host-mounted directory containing CPU-resident model weights and plain-data metadata for class order (`circle`, `rectangle`, `triangle`), input size, pixel scaling, the training and dataset seeds used, PyTorch version, training environment, and device. Training MUST accept optional command-line flags for each dataset seed and record each omitted seed as unknown rather than inventing it.
- **FR-010**: The checkpoint MUST load with `torch.load(..., weights_only=True)` and, together with the matching model definition in the project, support evaluation and prediction on CPU without retraining.
- **FR-011**: Prediction MUST preprocess the supplied image using the shared definition and report one of the three class labels using the checkpoint's class order.
- **FR-012**: Missing or invalid datasets, images, checkpoint files, configuration, or output paths MUST produce a clear error and a nonzero command exit status; an incomplete held-out set MUST NOT be silently treated as a successful evaluation.
- **FR-013**: The system MUST document that the dataset is a small synthetic learning demo, that training accuracy does not demonstrate generalization, and that held-out results are based on only 15 images.
- **FR-014**: Documentation MUST describe how to run each operation in Docker, how to set the training seed, where the checkpoint persists, and why repeated CPU runs may differ slightly despite fixed seeds.

### Key Entities *(include if feature involves data)*

- **Dataset set**: Training or held-out collection of labeled shape images, kept separate throughout the workflow.
- **Training run**: A configured, seeded CPU training session using training images and producing a checkpoint and paired accuracy results.
- **Model checkpoint**: A single saved model with weights and the metadata needed to interpret its outputs and reproduce preprocessing.
- **Evaluation result**: Correct and total predictions and accuracy for each of the training and held-out sets, reported together.
- **Prediction**: A class label produced for a supplied image using a compatible saved checkpoint.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can complete a training run with all 30 training and 15 held-out images and obtain a persisted model and a report containing both accuracies and both correct/total counts.
- **SC-002**: A user can load the saved model in a fresh session and evaluate all 45 images without retraining; each set's reported accuracy equals its correct count divided by its total.
- **SC-003**: Every successful prediction returns exactly one supported class label, and an unreadable image or incompatible checkpoint produces no successful prediction.
- **SC-004**: For a fixed dataset, seed, configuration, and container image, repeated CPU runs differ by at most one correctly classified image on each set, with reproducibility limits documented; bit-identical training results are not required.
- **SC-005**: Every successful reported accuracy is accompanied by the accuracy for the other set, so training accuracy is never presented alone as evidence of generalization.
- **SC-006**: All evaluation and prediction inputs receive the same resizing and scaling used for training, with no evaluation or prediction augmentation.

## Assumptions

- The feature 001 dataset and Docker runtime are available; training and held-out sets are generated before training and remain separate.
- Dataset seed metadata may be unavailable from an existing dataset; omitted values are recorded as unknown. Users are responsible for the accuracy of dataset seed values they provide.
- Training duration, epoch count, batch size, and default training seed will be chosen and documented during planning; no minimum held-out accuracy is promised for this tiny demo.
- The saved checkpoint is used with the matching project model definition. The host-mounted data directory provides persistence.
- MPS, native-device selection, and performance comparison are outside this feature's scope.
