# Feature Specification: Generate Synthetic Shape Dataset

**Feature Branch**: `feat/001-generate-shape-dataset`

**Created**: 2026-11-06

**Status**: Implemented

**Input**: Generate the training and held-out synthetic shape datasets described in the project research document.

## Clarifications

### Session 2026-11-06

- Q: What should happen if the output folders already contain images from an earlier generation run? → A: Replace previously generated images and preserve unrelated files.
- Q: How should we verify that images vary within each shape class? → A: Every class in each set must have at least two distinct positions, sizes, and colors, and at least two distinct rotations for rectangles and triangles.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate both datasets (Priority: P1)

A user generates labeled shape images that persist on their host and can later support a classification experiment.

**Why this priority**: Both sets are essential to the intended learning experiment and honest later evaluation.

**Independent Test**: Run generation with defaults and inspect the resulting folders and images.

**Acceptance Scenarios**:

1. **Given** a writable host-mounted data directory, **When** the user runs generation, **Then** it contains 10 training and 5 held-out images for each of the three classes.
2. **Given** a completed run, **When** the user inspects the images, **Then** each is a 1920 × 1080 PNG with one filled shape on a contrasting solid background, organized by set and class.

### User Story 2 - Reproduce or vary datasets (Priority: P2)

A user repeats a generation run or selects different seeds to obtain reproducible alternatives.

**Why this priority**: Repeatability makes experiments comparable while seed overrides enable new examples.

**Independent Test**: Generate into separate empty locations with identical and changed seeds, then compare image bytes.

**Acceptance Scenarios**:

1. **Given** the same seeds and generation environment, **When** generation is repeated, **Then** corresponding images are byte-identical.
2. **Given** an overridden seed for one set, **When** generation runs, **Then** that set reflects the selected seed and the other set remains reproducible from its own seed.

### Edge Cases

- Identical training and held-out seeds are rejected with a clear error so the mandatory sets remain independently seeded.
- Invalid seeds or an unwritable output location produce a clear failure rather than a reported successful dataset.
- Previously generated images are replaced on a repeat run; unrelated files are preserved.
- Candidate colors below the contrast threshold and triangles below the angle limit are rejected and resampled.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Generation MUST produce both a training set of 10 images per class and a held-out set of 5 images per class, for circle, rectangle, and triangle.
- **FR-002**: Each image MUST be a 1920 × 1080 PNG containing one filled shape on a solid background.
- **FR-003**: Rectangles MUST have varying width and height, and squares MUST be permitted. Triangles MUST have every interior angle at least approximately 20 degrees.
- **FR-004**: Each class in each set MUST contain at least two distinct positions, sizes, and shape colors; rectangles and triangles MUST also have at least two distinct rotations per class per set. Shapes MUST remain visible after resizing to 256 × 144. Circle rotation has no visible effect.
- **FR-005**: Each background color MUST be randomly selected, and each shape color MUST meet a documented minimum brightness or color-distance threshold against its background; candidates below the threshold MUST be resampled.
- **FR-006**: Each set MUST use a fixed default seed distinct from the other set, and users MUST be able to override each seed independently through command-line flags. Equal seeds MUST be rejected.
- **FR-007**: The same seeds and generation environment MUST yield byte-identical corresponding images; changing one set's seed MUST NOT change the other set.
- **FR-008**: Images MUST persist in a host-mounted data directory, grouped into separate folders for each set and class.
- **FR-009**: Generation MUST run in Docker using `python:3.14.10-slim` and exact dependency versions in a shared dependency file.
- **FR-010**: A successful repeat run MUST replace previously generated images and leave exactly the required generated images per set and class, preserving unrelated files; invalid input and output failures MUST be reported clearly.
- **FR-011**: The held-out set MUST be separately identifiable for later use and MUST NOT be used for training.

### Key Entities *(include if feature involves data)*

- **Dataset set**: Training or held-out collection, identified by its role and independently selected seed.
- **Shape image**: A labeled image belonging to one set and one class, with shape geometry and foreground and background colors.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A successful default run provides 45 readable images: 30 training and 15 held-out, with the required count for each class.
- **SC-002**: All generated images meet the specified dimensions, format, shape, contrast, and triangle angle constraints.
- **SC-006**: Every class in each set contains at least two distinct positions, sizes, and shape colors, and rectangles and triangles also have at least two distinct rotations.
- **SC-003**: Two runs with the same seeds in the same environment produce matching bytes for 100% of corresponding images.
- **SC-004**: Changing either seed leaves 100% of the other set's corresponding images unchanged.
- **SC-005**: Users can find every image by its set and class after the generation environment exits.

## Assumptions

- The user supplies a writable host directory and a working Docker runtime.
- The implementation will document a numerical contrast threshold and minimum visible shape size, chosen to satisfy the stated visual requirements.
- Generation is a small synthetic learning demo; it does not establish real-world performance. Training, evaluation, and MPS are outside this feature's scope.
