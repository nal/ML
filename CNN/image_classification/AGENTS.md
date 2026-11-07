# Agent instructions

Rules for any coding agent (Claude Code, Codex) working in this project.

## Project

- A small CNN that classifies synthetic images of circles, rectangles, and triangles.
- Requirements and decisions: `CNN_image_classification_research.md`.
- Built with GitHub Spec Kit. Both integrations are installed: Claude Code (`/speckit-*`, skills in `.claude/skills/`) and Codex (`$speckit-*`, skills in `.agents/skills/`). Both share the same `specs/` artifacts, so only one agent should run a given Spec Kit step at a time.
- The git repository root is `ML/`, two levels above this folder. Git commands and hooks apply to the whole repository.

## Branches

- Feature branches are created by Spec Kit (`/speckit-specify` → `speckit-git-feature`) as **`feat/NNN-slug`** with sequential numbering, for example `feat/001-shape-classifier`.
- Do not rename Spec Kit branches: the `NNN` prefix links a branch to its `specs/NNN-slug/` folder.
- Settings: `.specify/extensions/git/git-config.yml`.

## Feature numbers

`specs/` is the single source of truth for feature numbers. This keeps branch numbers, spec folders and the README from drifting apart.

- A feature number exists only if `specs/NNN-slug/` exists. Only `/speckit-specify` assigns numbers. Never reserve a number in advance or create a `feat/NNN-…` branch by hand.
- Work that is not a Spec Kit feature (docs, tooling, chores, fixes outside a feature) uses an **unnumbered** branch, for example `docs/hld` or `chore/feature-numbering`.
- Each `spec.md` keeps ``**Feature Branch**: `feat/NNN-slug` `` and `**Status**:` set to one of `Draft`, `In Progress`, `Implemented`. Set `Implemented` when `/speckit-converge` reports Converged and the feature's checks pass.
- The README feature table is generated: run `python3 scripts/features.py --write` after adding a spec or changing a Status. Never edit the table by hand, and refer to planned work by name, not number.
- The pre-commit hook runs `python3 scripts/features.py --check`. If it fails, fix the cause (add the missing spec, rename the branch to an unnumbered one, or regenerate the table) instead of bypassing it.

## Commit messages

Every commit must follow [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/). A `commit-msg` hook rejects commits that don't.

Format:

```
type(scope): subject

optional body

optional footers
```

- **type** (required), one of: `feat`, `fix`, `docs`, `refactor`, `test`, `build`, `ci`, `chore`, `perf`, `style`, `revert`.
- **scope** (optional), preferably one of: `spec`, `plan`, `tasks`, `data`, `model`, `train`, `eval`, `predict`, `bench`, `docker`, `deps`. Other scopes are allowed when none fits.
- **subject**: imperative mood, lowercase start, no trailing period, about 72 characters or fewer for the whole first line.
- **Breaking changes**: add `!` after the type or scope (`feat(model)!: …`) and/or a `BREAKING CHANGE: …` footer.
- **Footers** such as `Co-Authored-By:` are allowed.
- One logical change per commit. Pick the type from what the diff actually does: Spec Kit artifacts and docs are `docs`, Dockerfile and dependency pins are `build`, new behavior is `feat`.

Examples:

```
docs(spec): add shape classifier specification
feat(data): add synthetic shape generator
feat(train): add CNN training loop
fix(predict): load checkpoint weights on CPU
build(docker): pin python:3.14.10-slim base image
test(eval): cover held-out accuracy reporting
```

Spec Kit auto-commits after constitution, specify, clarify, plan, tasks, analyze, and implement with `commit_style: conventional`. When the `speckit-git-commit` skill asks for a message, write it with the same rules.

## Commit hook

- Config: `.pre-commit-config.yaml` in this folder: `conventional-pre-commit` (`commit-msg` stage) and the feature-ledger check (`pre-commit` stage).
- Install once per clone, from the `ML/` repository root:

  ```
  uv tool install pre-commit
  pre-commit install -c CNN/image_classification/.pre-commit-config.yaml
  ```

- If a commit is rejected, fix the message or the ledger problem and commit again. Never bypass the hooks with `--no-verify`.
