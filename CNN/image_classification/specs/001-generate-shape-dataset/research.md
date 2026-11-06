# Research: Synthetic Shape Dataset

## Drawing and geometry

**Decision**: Draw filled RGB circles and polygons with Pillow. Sample positions and dimensions with all geometry inside the canvas. Rotate rectangle vertices; sample triangle vertices and reject any whose interior angles are below 20°. Require every shape to contain a disk of radius at least 120 source pixels, and verify this from geometry before rasterization; this corresponds to 16 pixels at 256 × 144. Generate square rectangles with nonzero probability. Sample colors and placements independently of class, with no class-specific palette or region.

**Rationale**: This preserves visible interiors even for narrow shapes and avoids clipping. Pillow supports filled ellipse and polygon drawing ([Pillow documentation](https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html)).

**Alternatives considered**: Bounding-box minimum alone permits nearly invisible slivers; outlines do not meet the spec.

## Contrast

**Decision**: Require foreground/background relative luminance contrast ratio ≥ 3:1, computed from sRGB channels using the standard linearization and ratio formula ([W3C formula](https://www.w3.org/WAI/WCAG21/Techniques/general/G18)); resample foreground colors when below the threshold.

**Rationale**: An explicit luminance threshold gives a measurable visibility rule. This is a design threshold, not an accessibility conformance claim.

**Alternatives considered**: RGB Euclidean distance can accept colors with nearly equal perceived brightness.

## Seeds and encoding

**Decision**: Use separate `random.Random` instances with integer defaults 42 (training) and 43 (held-out), fixed iteration order, deterministic names, RGB mode and fixed PNG save settings. Pin Python and Pillow. Byte identity applies to repeated runs in the same built environment.

**Rationale**: Independent streams prevent one seed from affecting the other; Python documents seeded reproducibility and version limitations ([Python documentation](https://docs.python.org/3/library/random.html#notes-on-reproducibility)).

**Alternatives considered**: One shared random stream couples the sets; unseeded randomness cannot reproduce images.

## Safe repeat runs

**Decision**: Serialize publishers using a process-released advisory lock. Validate manifest and journal paths, reject traversal, symlinks, malformed or duplicate entries and untracked destination collisions. Stage images under the data root, then atomically publish a versioned recovery journal before changing destinations. The journal records each validated destination’s prior state (absent or owned with digest), desired digest and staged path, plus owned stale paths and their prior digests. On startup, recover a pending transaction before starting another: accept each destination only if it still matches its recorded prior or desired state, then resume replacements and stale removals, atomically publish the new manifest, and remove the journal and staging. Reject unexpected changes, corrupt or missing transaction data with actionable errors; never delete untracked files. Manifest publication and cleanup are idempotent. Test interruptions around each mutation, including first-run and repeat-run publication. Guarantee recovery from process interruption, not power loss without explicit durability measures.

**Rationale**: Deterministic names alone cannot distinguish a user's file from a generated one. Staging avoids destroying the previous dataset when generation itself fails.

**Alternatives considered**: Clearing class folders deletes unrelated data; blindly overwriting fixed names can destroy user files.

## Per-set variation and verification

**Decision**: Track each sampled shape's final raster-space position, size, foreground color and orientation (orientation modulo the shape's rotational symmetries). Before publishing each class, deterministically resample candidates as needed until at least two values of each applicable property exist; circles have no orientation requirement. Measure position by bounding-box center, size by bounding-box dimensions, and rectangle and triangle orientation by their actual geometry, using a documented canonical representation. Verify geometric attributes before drawing and verify output pixels independently where practical.

**Rationale**: Random sampling alone does not guarantee the minimum variation for every seed. Canonical geometric values avoid treating a symmetric equivalent rotation as a distinct visible orientation.

**Alternatives considered**: Assuming variation is overwhelmingly likely does not satisfy the requirement for every successful run.

## Validation strategy

**Decision**: Implement standard-library unittest checks under `tests/`, included in the Docker build, with unit coverage for geometry and contrast, and integration coverage for image counts, seeded byte identity, per-set variation, safe reruns, collision rejection, interrupted-publication recovery and seed errors. Provide a separate default-run checkpoint before seed overrides are available.

**Rationale**: Reproducibility and crash recovery need repeatable checks, including failures injected at publication boundaries.

**Alternatives considered**: Manual visual inspection cannot reliably verify geometry or repeatability.
