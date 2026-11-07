---
theme: default
title: "[PROJECT NAME]: High-Level Design"
info: Generated from docs/hld/hld.md by /speckit-hld-slides
transition: slide-left
mdc: true
drawings:
  persist: false
---

<!--
  docs/hld/package.json (create if missing):
  {
    "name": "hld-slides",
    "private": true,
    "type": "module",
    "scripts": {
      "dev": "slidev slides.md --open",
      "build": "slidev build slides.md",
      "export": "slidev export slides.md"
    },
    "devDependencies": {
      "@slidev/cli": "53.0.0",
      "@slidev/theme-default": "0.25.0"
    }
  }

  Animation toolbox:
  - <v-clicks> … </v-clicks>        reveal list items one by one
  - <div v-click> … </div>          reveal a block on the next click
  - <span v-mark.circle.orange>x</span>  hand-drawn highlight
  - build-up diagram: repeat a Mermaid diagram over several slides, adding one stage each time
  - animated edge (Mermaid 11):  A e1@==> B   then   e1@{ animate: true }
-->

# [PROJECT NAME]

High-Level Design

<div class="opacity-60">[date] · commit [sha]</div>

<!-- Speaker notes: one-sentence pitch of the system. -->

---

# What it does

<v-clicks>

- [Point 1]
- [Point 2]
- [Point 3]

</v-clicks>

---

# The pipeline, step 1

```mermaid
flowchart LR
  classDef new fill:#fde68a,stroke:#d97706,color:#000
  A[Stage 1]:::new
```

---

# The pipeline, step 2

```mermaid
flowchart LR
  classDef new fill:#fde68a,stroke:#d97706,color:#000
  A[Stage 1] e1@==> B[Stage 2]:::new
  e1@{ animate: true }
```

---
layout: two-cols
---

# Diagram with explanation

```mermaid {scale: 0.8}
sequenceDiagram
  actor U as User
  participant C as CLI
  U->>C: command
```

::right::

<v-clicks>

- [What happens first]
- [What happens next]

</v-clicks>

---
layout: center
---

# Questions?
