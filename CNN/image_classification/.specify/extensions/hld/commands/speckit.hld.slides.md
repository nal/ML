---
description: "Create or refresh docs/hld/slides.md, an animated Slidev deck built from the HLD"
---

# Generate HLD Slides

Turn `docs/hld/hld.md` into a [Slidev](https://sli.dev) presentation at `docs/hld/slides.md` that
walks a human audience through the system step by step.

## User Input

```text
$ARGUMENTS
```

Consider the user input before proceeding (if not empty), for example audience, duration or focus.

## Prerequisites

- `docs/hld/hld.md` must exist. If it doesn't, stop and tell the user to run `/speckit-hld-generate` first.
- The HLD is the only source of content. Do not add facts that are not in it.

## Execution

1. Load the template `.specify/extensions/hld/templates/slides-template.md`.
2. If `docs/hld/package.json` is missing, create it from the template's comment block
   (pinned `@slidev/cli` and `@slidev/theme-default`, scripts `dev`, `build`, `export`).
3. Build the deck. Slide budget: about one slide per HLD section, 12–20 slides in all.
4. Make it animate the process. Use these Slidev features:
   - `<v-clicks>` around bullet lists, so points appear one by one.
   - `v-click` on blocks or images, to reveal a diagram after the setup text.
   - **Build-up diagrams**: for pipelines, show the same Mermaid diagram on 2–4 consecutive
     slides, adding one stage each time. Mark the new stage with a highlight class
     (`classDef new fill:#fde68a,stroke:#d97706`).
   - **Animated edges** (Mermaid 11) for data flow: name the edge and set animation, for example
     ``A e1@==> B`` then ``e1@{ animate: true }``.
   - `v-mark` to underline or circle key numbers in tables.
   - `layout: two-cols` to put a diagram beside its explanation.
   - Speaker notes in a trailing `<!-- … -->` comment on each slide, 1–3 sentences.
5. Keep Mermaid blocks as fenced ```` ```mermaid ```` with an optional `{scale: 0.8}` to fit.
6. Validate: `cd docs/hld && npm install && npx slidev build slides.md --out /tmp/hld-slides-dist`.
   Fix any slide that fails to build. Do not commit `node_modules/` or `dist/`.

## Report

- Path written, slide count, how to present (`cd docs/hld && npm install && npm run dev`).
- Suggested commit: `docs(hld): <what changed>` (Conventional Commits; see `AGENTS.md`).
