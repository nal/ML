# Data Model

## Dataset set

- Role: `train` or `held-out`; each contains `circle`, `rectangle`, and `triangle` directories.
- Seed: integer, default 42 or 43 respectively; values must differ.
- Count: 10 per class for training, 5 per class for held-out.

## Shape image

- RGB PNG, 1920 × 1080; exactly one filled shape and one solid background.
- Shape is entirely within the image and contains an inscribed disk of radius ≥120 pixels; triangle angles ≥20°. Rectangle widths and heights vary, including possible equality.
- Foreground and background meet relative luminance contrast ≥3:1.
- Each set/class has at least two distinct raster-space bounding-box centers, bounding-box dimensions, and foreground colors. Rectangles and triangles also have two distinct geometric orientations after accounting for rotational symmetry; circles are exempt. Candidates are resampled deterministically until these constraints hold.
- Deterministic path `SET/CLASS/NN.png`, with zero-padded indices beginning at 01.

## Ownership manifest

- Versioned file `.shape-dataset-manifest.json` at data root; lists only relative generated image paths.
- Paths must be unique, confined to the expected set/class directories, and not symlinks; invalid manifests fail safely. Existing untracked destinations are never overwritten.
- Lifecycle: absent on a new output root; a validated journal is published before any destination change. The manifest is atomically published after image replacements and stale removals; journal and staging are then removed. Recovery resumes an interrupted transaction before a new one begins, including after manifest publication. No full-directory atomicity is promised.

## Recovery journal

- Versioned transaction record contains validated relative paths, each destination’s prior state (absent or owned with digest), desired digest and staged image path; stale owned paths include prior digests.
- A process-released advisory lock serializes publication and recovery. Recovery only modifies a destination that matches its recorded prior or desired state, and stops on unexpected content, invalid paths or missing staged data. Already removed stale files and already published desired files are accepted as completed operations.
- A journal is atomically installed before destination mutations, retained through manifest publication, and removed only after completion. Recovery guarantees cover process interruption; power-loss durability is not promised.
