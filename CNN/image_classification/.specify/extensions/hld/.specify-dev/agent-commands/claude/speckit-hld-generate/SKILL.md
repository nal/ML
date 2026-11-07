---
name: speckit-hld-generate
description: Create or refresh docs/hld/hld.md, the system-wide High-Level Design with Mermaid diagrams
compatibility: Requires spec-kit project structure with .specify/ directory
metadata:
  author: local
  source: hld:commands/speckit.hld.generate.md
---

# Generate High-Level Design

Write or refresh `docs/hld/hld.md`: one system-wide, human-oriented High-Level Design for the
project **as it exists now**. Feature specs under `specs/` each describe one change; the HLD
combines them with the code into a single picture of the current system.

## User Input

```text
$ARGUMENTS
```

Consider the user input before proceeding (if not empty), for example a focus area or audience.

## Audience and style

- Readers are people: new contributors, reviewers, stakeholders. Not agents.
- Diagrams first, then short prose that explains *why*. Prefer one clear diagram to three paragraphs.
- Describe responsibilities, flows, data and decisions. Do not paste code. Name modules and
  CLI commands only where it helps a reader find them.
- Every factual claim must be traceable to the code, a spec artifact, or the constitution.
  Never invent components, numbers or results. Mark gaps as `> **Open question:** …`.

## Inputs (read all that exist)

1. `.specify/memory/constitution.md`: principles and constraints.
2. Project requirements document(s) at the project root (for example `*_research.md`) and `README.md`.
3. Every `specs/*/spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/*`, plus extra
   records such as `comparison.md`. Note which feature introduced each decision.
4. Source code under `src/`, entry points (`__main__.py`), `Dockerfile`, dependency pins, `tests/`.
5. The existing `docs/hld/hld.md`, if present. Keep its structure and any human edits that
   are still true; update anything the code or specs now contradict.

## Execution

1. Load the template `.specify/extensions/hld/templates/hld-template.md`.
2. Fill every section. Drop a section only if it truly does not apply, and say so in one line.
3. Diagrams:
   - Use fenced ```` ```mermaid ```` blocks only, so GitHub renders them.
   - Stay within syntax GitHub's renderer supports: `flowchart`, `sequenceDiagram`,
     `classDiagram`, `stateDiagram-v2`, `erDiagram`, `timeline`. Do **not** use animated edges
     (`e1@{ animate: true }`) or other Mermaid 11-only syntax here; those belong in the slides.
   - Keep each diagram under ~15 nodes. Split rather than cram.
   - Quote labels that contain punctuation: `A["Resize (144×256)"]`.
4. Decision log: one row per significant decision, linking to the `research.md` section it came from.
5. Update the header metadata: date (today, ISO), the commit (`git rev-parse --short HEAD`), and
   the list of features covered.
6. Validate: if `npx` is available, render each Mermaid block to check its syntax, for example
   `npx -y @mermaid-js/mermaid-cli -i docs/hld/hld.md -o /tmp/hld-check.md`. Fix any block that fails.
7. If `docs/hld/slides.md` exists, tell the user to run `/speckit-hld-slides` (Codex:
   `$speckit-hld-slides`) so the deck matches.

## Report

- Path written, sections changed, open questions found.
- Suggested commit: `docs(hld): <what changed>` (Conventional Commits; see `AGENTS.md`).