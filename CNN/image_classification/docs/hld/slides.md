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

<div class="opacity-60 pt-4">2026-11-07 · features 001–005 · commit 83b41d9</div>

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
- Runs in **Docker on the CPU** by default, or **natively on the Mac's CPU or GPU (MPS)**
- **Benchmarks** every training run and compares the three configurations

</v-clicks>

<div v-click class="pt-6 opacity-70">
Out of scope today: real photos, more classes, network serving, concurrent runs.
</div>

<!--
It's a learning project. The value is in the process (reproducibility, honest evaluation), not in accuracy.
-->

---

# Guiding principles

| Principle | In the design |
|---|---|
| <span v-mark.underline.orange="1">Simplicity</span> | 2 small packages, ~5k-parameter CNN, `unittest` |
| <span v-mark.underline.orange="2">Reproducibility</span> | Seeds 42 / 43 / 42, one shared set of pins, deterministic where supported |
| <span v-mark.underline.orange="3">Honest evaluation</span> | Held-out accuracy always shown; slower GPU results still published |
| <span v-mark.underline.orange="4">Shared preprocessing</span> | One pipeline for train, evaluate and predict |
| <span v-mark.underline.orange="5">Conventional Commits</span> | `commit-msg` hook, plus a feature-number check |

<!--
These five come from the Spec Kit constitution. Every spec and plan was checked against them.
-->

---

# System context

```mermaid {scale: 0.85}
flowchart LR
  user([Developer])
  subgraph docker["Docker · CPU only"]
    gen["shape_dataset"]
    clf["shape_classifier"]
  end
  subgraph native["Native macOS"]
    nclf["shape_classifier<br/>CPU or MPS"]
  end
  data[("data/ folder")]
  user e1@==> gen
  gen e2@==> data
  data e3@==> clf
  data e4@==> nclf
  e1@{ animate: true }
  e2@{ animate: true }
  e3@{ animate: true }
  e4@{ animate: true }
```

<v-clicks>

- Same code and package versions in both environments
- The `data/` folder is the **only** shared state: PNGs, `shapes.pth`, `benchmark-results.json`
- Commands touching the same outputs run **one at a time**

</v-clicks>

<!--
The two packages never call each other. They only agree on the folder layout. Docker can't reach the Mac's GPU, which is why the native mode exists.
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
  B e2@==> C["Train<br/>60 epochs, timed"]:::new
  C e3@==> D["Assess<br/>train + held-out"]:::new
  e1@{ animate: true }
  e2@{ animate: true }
  e3@{ animate: true }
```

Augmentation every epoch: rotate ±10°, flip, jitter color. Each epoch is timed; then score **both** sets.

---

# The pipeline · 4 of 4

```mermaid
flowchart LR
  classDef new fill:#fde68a,stroke:#d97706,color:#000
  A["Generate"] e1@==> B["Preprocess"]
  B e2@==> C["Train"]
  C e3@==> D["Assess"]
  D e4@==> E[("shapes.pth<br/>+ benchmark entry")]:::new
  E e5@==> F["Predict<br/>image → class"]:::new
  E e6@==> G["Summary<br/>compare devices"]:::new
  e1@{ animate: true }
  e2@{ animate: true }
  e3@{ animate: true }
  e4@{ animate: true }
  e5@{ animate: true }
  e6@{ animate: true }
```

Every training run publishes a portable checkpoint **and** one benchmark entry.

<!--
That's the whole system. The next slides zoom into each stage.
-->

---
layout: two-cols
---

# Choosing the device

```mermaid {scale: 0.55}
flowchart TD
  R(["--device auto · cpu · mps"]) --> E{"in Docker?"}
  E -- yes --> DC{"asked for mps?"}
  DC -- yes --> X["fail, nothing written"]
  DC -- no --> CPU["cpu"]
  E -- no --> P{"MPS works?"}
  P -- yes --> NM{"asked for cpu?"}
  NM -- yes --> CPU
  NM -- no --> MPS["mps"]
  P -- no --> NC{"asked for mps?"}
  NC -- yes --> X
  NC -- no --> CPU
```

::right::

<v-clicks>

- Resolved **before** any data is read or file written
- MPS is probed with a real operation, not just "available"
- Asking for `mps` where it can't run **fails**. It never quietly uses the CPU
- Every run prints its real environment, device and versions

</v-clicks>

<!--
A silent fallback would make a "GPU" benchmark actually measure the CPU. That's why explicit mps fails loudly.
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
  subgraph sc["shape_classifier · 002–004"]
    cmain["CLI"] --> cdev[device]
    cmain --> ctrain[train]
    cmain --> cpred[predict]
    cmain --> cbench[benchmark]
    ctrain --> cdata[data]
    ctrain --> cmodel[model]
    ctrain --> cpub[publication]
    cpub --> cckpt[checkpoint]
    cpub --> cbench
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
- `device` decides where work runs; `publication` writes checkpoint and results safely
- `benchmark` validates entries and prints the comparison

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
  U->>CLI: train --device auto
  CLI->>CLI: seed everything · all CPU cores · deterministic where supported
  CLI->>DS: load 30 train + 15 held-out
  loop 60 epochs × 4 batches
    CLI->>M: augmented batch on the device
    M-->>CLI: logits
    CLI->>O: loss → backward → step
  end
  CLI->>DS: score unaugmented train + held-out
  CLI->>M: time a held-out pass per image
  CLI->>CLI: publish shapes.pth + benchmark entry
  CLI-->>U: Training x/30 · Held-out y/15
```

<div v-click>

The first epoch is excluded from timing (warm-up); MPS is synchronized before each timer read.

</div>

---

# Publishing checkpoint and results

```mermaid {scale: 0.65}
sequenceDiagram
  participant T as train
  participant J as Journal
  participant C as shapes.pth
  participant R as results.json
  T->>T: stage new checkpoint, back up old one
  T->>J: write journal + sidecar
  Note over T: block Ctrl-C / SIGTERM
  T->>C: atomic replace
  T->>R: append entry (commit point)
  Note over T: unblock signals
  T->>J: clean up
```

<v-clicks>

- Before the commit point: the old checkpoint comes back and no entry exists
- After it: the run is complete, even if the process is killed right away
- `evaluate`, `predict` and `summary` finish any interrupted publication first

</v-clicks>

<!--
Two files can't be replaced in one atomic step, so a journal makes the pair recoverable, across Docker and native paths.
-->

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
- Loads on **any** device, whichever environment trained it; 002/003 checkpoints still work
- Rejects the file if the class order, input size, scaling or provenance fields are wrong
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

# Results: device benchmark

Default settings (seed 42, 60 epochs, batch 8), same data, M1 Pro (feature 004).

| Configuration | Training time* | Inference / image | Training | Held-out |
|---|---:|---:|---:|---:|
| Docker CPU (2 threads) | 24.6 s | 2.42 ms | 19/30 | 6/15 |
| Native CPU (10 threads) | 9.3 s | 1.20 ms | 20/30 | 6/15 |
| Native MPS | <span v-mark.circle.green="1">**6.9 s**</span> | 0.57 ms | 18/30 | 6/15 |

<div class="text-sm opacity-60">* excluding the first (warm-up) epoch</div>

<v-clicks at="2">

- MPS was fastest here, but for a model this small that isn't guaranteed
- Docker had only 2 of 10 cores, so its row mixes environment and core count
- Accuracy is the same on held-out: devices change speed, not what the model learns

</v-clicks>

<!--
Native CPU was run twice: identical accuracy and loss, times 2.3 percent apart.
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
- **Explicit device, no silent fallback** → benchmarks measure what they claim
- **Dataset fingerprint as the grouping key** → only like is compared with like
- **Checkpoint first, results last, with a journal** → a failed save never changes the old model

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
  004 device benchmark : native macOS : --device flag : benchmark summary
  005 high-level design : this deck : HLD document
```

<div v-click>

Open question: held-out accuracy is near chance on every device. Would more data help more than more epochs?

</div>

---
layout: center
class: text-center
---

# Questions?

<div class="opacity-70">

Document: `docs/hld/hld.md` · Regenerate: `/speckit-hld-generate`, then `/speckit-hld-slides`

</div>
