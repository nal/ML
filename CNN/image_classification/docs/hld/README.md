# High-Level Design

| File | What it is |
|---|---|
| [`hld.md`](hld.md) | The system-wide High-Level Design, with Mermaid diagrams. Renders directly on GitHub. |
| [`slides.md`](slides.md) | A [Slidev](https://sli.dev) presentation of the same design, with step-by-step reveals and animated data-flow diagrams. |
| `package.json` | Pinned Slidev version for the deck. |

## Present the slides

Requires Node.js 20 or newer.

```bash
cd docs/hld
npm install
npm run dev      # opens http://localhost:3030; arrow keys or space to step through
```

Other outputs:

```bash
npm run build    # static site in docs/hld/dist/ (for example for GitHub Pages)
npm run export   # PDF; needs `npm i -D playwright-chromium` once
```

Press `o` for the slide overview and `p` for presenter mode with speaker notes.

## Regenerate after a feature

Both files come from the local Spec Kit extension `hld` (`.specify/extensions/hld/`):

| Step | Claude Code | Codex |
|---|---|---|
| Refresh the HLD from the code and every `specs/*` folder | `/speckit-hld-generate` | `$speckit-hld-generate` |
| Rebuild the deck from the HLD | `/speckit-hld-slides` | `$speckit-hld-slides` |

After `/speckit-implement`, Spec Kit offers to run `/speckit-hld-generate` through an optional
`after_implement` hook. Commit the result as `docs(hld): …`.

Templates to adjust structure or style:

- `.specify/extensions/hld/templates/hld-template.md`
- `.specify/extensions/hld/templates/slides-template.md`
