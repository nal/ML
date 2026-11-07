---
theme: default
title: "Synthetic Shape Classifier: High-Level Design"
info: Generated from docs/hld/hld.md by /speckit-hld-slides
transition: slide-left
mdc: true
drawings:
  persist: false
---

# Synthetic Shape Classifier

High-Level Design

<div class="opacity-60 pt-4">2026-11-07 · features 001–003 · commit a1efeb2</div>

<!--
A tiny, fully reproducible machine-learning pipeline: generate pictures of shapes, train a small CNN, classify new pictures.
-->

---

# What it does

<v-clicks>

- **Generates** 45 synthetic 1920×1080 images: circles, rectangles and triangles
- **Trains** a tiny CNN (5,187 parameters) on 30 of them
- **Reports** accuracy on the 15 held-out images it never saw
- **Classifies** any new image into one of the three shapes
- Runs on the **CPU in Docker** and is reproducible from fixed seeds

</v-clicks>

<div v-click class="pt-6 opacity-70">
Out of scope today: GPU/MPS (feature 004), real photos, more classes, network serving.
</div>

<!--
It's a learning project. The value is in the process (reproducibility, honest evaluation), not in accuracy.
-->

---

# Guiding principles

| Principle | In the design |
|---|---|
| <span v-mark.underline.orange="1">Simplicity</span> | 2 small packages, ~5k-parameter CNN, `unittest` |
| <span v-mark.underline.orange="2">Reproducibility</span> | Seeds 42 / 43 / 42, pinned packages, deterministic PyTorch |
| <span v-mark.underline.orange="3">Honest evaluation</span> | Held-out accuracy always shown, never used to choose settings |
| <span v-mark.underline.orange="4">Shared preprocessing</span> | One pipeline for train, evaluate and predict |
| <span v-mark.underline.orange="5">Conventional Commits</span> | Enforced by a `commit-msg` hook |

<!--
These five come from the Spec Kit constitution. Every spec and plan was checked against them.
-->

---

# System context

```mermaid {scale: 0.85}
flowchart LR
  user([Developer])
  subgraph docker["Docker · python:3.14.10-slim · CPU"]
    gen["shape_dataset"]
    clf["shape_classifier"]
  end
  data[("data/ volume")]
  user e1@==> gen
  gen e2@==> data
  data e3@==> clf
  clf e4@==> user
  e1@{ animate: true }
  e2@{ animate: true }
  e3@{ animate: true }
  e4@{ animate: true }
```

<v-clicks>

- Two commands, one image, one mounted folder
- The `data/` folder is the **only** shared state: PNGs and `shapes.pth`

</v-clicks>

<!--
The two packages never call each other. They only agree on the folder layout.
-->

---

# The pipeline · 1 of 4

```mermaid
flowchart LR
  classDef new fill:#fde68a,stroke:#d97706,color:#000
  A["Generate<br/>45 PNGs"]:::new
```

Seeds **42** (training) and **43** (held-out) → byte-identical images every run.

<!--
We build the pipeline one stage at a time.
-->

---

# The pipeline · 2 of 4

```mermaid
flowchart LR
  classDef new fill:#fde68a,stroke:#d97706,color:#000
  A["Generate<br/>45 PNGs"] e1@==> B["Load + preprocess<br/>3×144×256"]:::new
  e1@{ animate: true }
```

Resize to 256×144, scale to [0, 1]. **The same code** is used later for prediction.

---

# The pipeline · 3 of 4

```mermaid
flowchart LR
  classDef new fill:#fde68a,stroke:#d97706,color:#000
  A["Generate<br/>45 PNGs"] e1@==> B["Load + preprocess<br/>3×144×256"]
  B e2@==> C["Train<br/>60 epochs, augmented"]:::new
  C e3@==> D["Assess<br/>train + held-out"]:::new
  e1@{ animate: true }
  e2@{ animate: true }
  e3@{ animate: true }
```

Augmentation every epoch: rotate ±10°, flip, jitter color. Then score **both** sets.

---

# The pipeline · 4 of 4

```mermaid
flowchart LR
  classDef new fill:#fde68a,stroke:#d97706,color:#000
  A["Generate"] e1@==> B["Preprocess"]
  B e2@==> C["Train"]
  C e3@==> D["Assess"]
  D e4@==> E[("shapes.pth")]:::new
  E e5@==> F["Predict<br/>image → class"]:::new
  e1@{ animate: true }
  e2@{ animate: true }
  e3@{ animate: true }
  e4@{ animate: true }
  e5@{ animate: true }
```

The checkpoint carries weights **and** metadata, and loading it validates both.

<!--
That's the whole system. The next slides zoom into each stage.
-->

---

# Building blocks

```mermaid {scale: 0.65}
flowchart LR
  subgraph ds["shape_dataset · 001"]
    dmain["CLI"] --> dgen[generate]
    dgen --> dgeo[geometry]
    dgen --> dcol[colors]
    dmain --> dout["output"]
  end
  subgraph sc["shape_classifier · 002–003"]
    cmain["CLI"] --> ctrain[train]
    cmain --> cpred[predict]
    ctrain --> cdata[data]
    ctrain --> cmodel[model]
    ctrain --> cckpt[checkpoint]
    cpred --> cckpt
    cdata --> ctf[transforms]
    cpred --> ctf
  end
  dout e1@==>|folder layout| cdata
  e1@{ animate: true }
```

<v-clicks>

- `shape_dataset` knows nothing about ML
- `transforms` is the single shared preprocessing definition
- `checkpoint` is the only place that reads or writes `shapes.pth`

</v-clicks>

---
layout: two-cols
---

# Generating a shape

```mermaid {scale: 0.6}
flowchart TD
  S(["seed"]) --> G["sample geometry"]
  G --> R{"angles ≥ 20°<br/>inner circle ≥ 120 px?"}
  R -- no --> G
  R -- yes --> C["colors, contrast ≥ 3:1"]
  C --> V{"set varied enough?"}
  V -- no --> G
  V -- yes --> D["draw PNG"]
```

::right::

<v-clicks>

- Separate random generators for training and held-out, so one seed never affects the other set
- Rejection sampling: redraw until **every** rule holds
- 120 px inner circle ≈ 16 px after resizing, so the shape stays visible
- Variation check: every set has at least 2 distinct positions, sizes, colors and orientations
- Squares are allowed as rectangles (about 1 in 8)

</v-clicks>

---

# Publishing safely

```mermaid {scale: 0.7}
sequenceDiagram
  participant G as Generator
  participant J as Journal
  participant S as Stage
  participant D as data/
  G->>G: exclusive lock
  G->>J: finish any interrupted run
  G->>S: write all new PNGs
  G->>J: atomic journal (SHA-256 per file)
  loop each image
    G->>D: atomic replace
  end
  G->>D: new manifest, remove stale owned files
  G->>J: delete journal + stage
```

<div v-click>

Kill the process at any point and the next run **finishes the job**. Files the generator didn't create are never touched.

</div>

---

# Training and assessment

```mermaid {scale: 0.6}
sequenceDiagram
  actor U as Developer
  participant CLI
  participant DS as ShapeDataset
  participant M as CNN
  participant O as Adam
  U->>CLI: train
  CLI->>CLI: seed everything · 1 thread · deterministic
  CLI->>DS: load 30 train + 15 held-out
  loop 60 epochs × 4 batches
    CLI->>M: augmented batch
    M-->>CLI: logits
    CLI->>O: loss → backward → step
  end
  CLI->>DS: score unaugmented train + held-out
  CLI->>CLI: atomic save shapes.pth
  CLI-->>U: Training x/30 · Held-out y/15
```

---

# The model

```mermaid
flowchart LR
  I["3×144×256"] e1@==> C1["Conv 16<br/>ReLU · Pool"]
  C1 e2@==> C2["Conv 32<br/>ReLU · Pool"]
  C2 e3@==> G["Global avg<br/>pool → 32"]
  G e4@==> FC["Linear<br/>32 → 3"]
  FC e5@==> O(["circle<br/>rectangle<br/>triangle"])
  e1@{ animate: true }
  e2@{ animate: true }
  e3@{ animate: true }
  e4@{ animate: true }
  e5@{ animate: true }
```

<v-clicks>

- **5,187** trainable parameters
- Adam, learning rate 0.001, batch 8, **60 epochs**
- Global pooling makes the head independent of the image size

</v-clicks>

---
layout: two-cols
---

# Predicting

```mermaid {scale: 0.6}
sequenceDiagram
  actor U as Developer
  participant CK as checkpoint
  participant T as preprocess
  participant M as CNN
  U->>CK: predict image.png
  CK->>CK: load weights_only<br/>validate metadata
  CK->>T: image
  T->>M: 3×144×256
  M-->>U: "circle"
```

::right::

<v-clicks>

- `torch.load(weights_only=True)`, mapped to CPU
- Rejects the file if the class order, input size, device or provenance fields are wrong
- The class name comes from the **checkpoint's** class order, not from the code

</v-clicks>

---

# Results: honest numbers

Epoch count chosen **from training data only**, frozen, *then* held-out evaluated (feature 003).

| Epochs | Training | Held-out | Loop time |
|---:|---:|---:|---:|
| 30 | 16/30 (0.53) | 7/15 (0.47) | 21.6 s |
| **60** | **19/30 (0.63)** | <span v-mark.circle.red="1">**6/15 (0.40)**</span> | 45.7 s |
| 120 | 24/30 (0.80) | 5/15 (0.33) | 87.5 s |

<v-clicks at="2">

- Training accuracy rises; held-out does not, which points to **overfitting** on 30 images
- One held-out image ≈ 6.7 points, so the differences are within noise
- Held-out ≈ 0.4 vs 0.33 for random guessing: a teaching model, not a reliable classifier

</v-clicks>

<!--
We publish unfavorable numbers on purpose. That's constitution principle III.
-->

---

# Key decisions

<v-clicks>

- **Rejection sampling** with angle, size and contrast rules → every shape is recognizable
- **Separate seeds** per set → independent, reproducible sets
- **Lock + journal + manifest** → reruns and crashes never corrupt data
- **CPU wheels, everything pinned** → small, reproducible image
- **One preprocessing pipeline, no normalization** → no train/serve mismatch
- **Validated checkpoint metadata** → clear errors instead of silent wrong answers
- **Epochs chosen by a pre-declared rule** → no held-out leakage

</v-clicks>

<div v-click class="pt-4 opacity-70">Full log with links: docs/hld/hld.md §11</div>

---

# Evolution

```mermaid {scale: 0.8}
timeline
  title Feature history
  001 dataset : Docker image : seeded generator : safe publishing
  002 classifier : preprocessing : CNN + training : checkpoint : predict
  003 training default : epoch comparison : 30 → 60
  004 device benchmark (planned) : native MPS : --device flag : speed comparison
```

<div v-click>

Next: feature 004 must relax the checkpoint's fixed `environment = docker` and `device = cpu` metadata.

</div>

---
layout: center
class: text-center
---

# Questions?

<div class="opacity-70">

Document: `docs/hld/hld.md` · Regenerate: `/speckit-hld-generate`, then `/speckit-hld-slides`

</div>
