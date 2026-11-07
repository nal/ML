#!/usr/bin/env python3
"""Feature ledger: specs/ is the single source of truth for feature numbers.

    python scripts/features.py --check   # fail if numbers, branches, specs or README disagree
    python scripts/features.py --write   # regenerate the README feature table from specs/

Rules (see AGENTS.md, "Feature numbers"):
- A feature number exists only if specs/NNN-slug/ exists; only /speckit-specify assigns one.
- Every <prefix>/NNN-slug branch (local or remote-tracking) has a matching specs/NNN-slug/.
- Numbers are unique, and each spec.md names its branch and a known Status.
- The README table between the feature markers is generated, never edited by hand.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPECS = ROOT / 'specs'
README = ROOT / 'README.md'
GIT_CONFIG = ROOT / '.specify' / 'extensions' / 'git' / 'git-config.yml'
START, END = '<!-- features:start -->', '<!-- features:end -->'
STATUSES = ('Draft', 'In Progress', 'Implemented')
DIR_RE = re.compile(r'^(\d{3,})-[a-z0-9]+(?:-[a-z0-9]+)*$')


def branch_prefix():
    if GIT_CONFIG.is_file():
        match = re.search(r'^branch_prefix:\s*"?([^"\s#]*)"?', GIT_CONFIG.read_text(), re.M)
        if match and match.group(1):
            return match.group(1).strip('/')
    return 'feat'


def field(text, pattern):
    match = re.search(pattern, text, re.M)
    return match.group(1).strip() if match else None


def load_specs(errors):
    specs, seen = [], {}
    for directory in sorted(p for p in SPECS.iterdir() if p.is_dir()) if SPECS.is_dir() else []:
        match = DIR_RE.match(directory.name)
        if not match:
            errors.append(f'specs/{directory.name}: folder name must be NNN-slug (lowercase, hyphens)')
            continue
        number = match.group(1)
        if number in seen:
            errors.append(f'feature number {number} is used twice: specs/{seen[number]} and specs/{directory.name}')
        seen[number] = directory.name
        spec_file = directory / 'spec.md'
        if not spec_file.is_file():
            errors.append(f'specs/{directory.name}: missing spec.md')
            continue
        text = spec_file.read_text()
        spec = {
            'dir': directory.name,
            'number': number,
            'title': field(text, r'^# Feature Specification:\s*(.+)$'),
            'branch': field(text, r'^\*\*Feature Branch\*\*:\s*`([^`]+)`'),
            'status': field(text, r'^\*\*Status\*\*:\s*(.+)$'),
        }
        for key, label in (('title', '"# Feature Specification: …" heading'),
                           ('branch', '"**Feature Branch**: `…`" line'),
                           ('status', '"**Status**: …" line')):
            if not spec[key]:
                errors.append(f'specs/{directory.name}/spec.md: missing {label}')
        if spec['status'] and spec['status'] not in STATUSES:
            errors.append(f'specs/{directory.name}/spec.md: Status "{spec["status"]}" must be one of {", ".join(STATUSES)}')
        expected_branch = f'{branch_prefix()}/{directory.name}'
        if spec['branch'] and spec['branch'] != expected_branch:
            errors.append(f'specs/{directory.name}/spec.md: Feature Branch is `{spec["branch"]}`, expected `{expected_branch}`')
        specs.append(spec)
    return specs


def git(*args):
    try:
        return subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None


def git_branches():
    """Map branch name (remote prefix stripped) to the refs that carry it."""
    out = git('for-each-ref', '--format=%(refname)', 'refs/heads', 'refs/remotes') or ''
    branches = {}
    for ref in out.split():
        if ref.startswith('refs/heads/'):
            name = ref[len('refs/heads/'):]
        elif ref.startswith('refs/remotes/') and not ref.endswith('/HEAD'):
            name = ref[len('refs/remotes/'):].split('/', 1)[-1]
        else:
            continue
        branches.setdefault(name, []).append(ref)
    return branches


def main_line():
    """Commits on main's first-parent line: a branch whose tip is here has no commits of its own yet."""
    for ref in ('refs/heads/main', 'refs/remotes/origin/main'):
        out = git('rev-list', '--first-parent', ref)
        if out:
            return set(out.split())
    return set()


def check_branches(specs, errors):
    prefix = branch_prefix()
    pattern = re.compile(rf'^{re.escape(prefix)}/((\d{{3,}})-.+)$')
    project = (git('rev-parse', '--show-prefix') or '').strip()
    in_tree = {spec['dir'] for spec in specs}
    by_number = {spec['number']: spec['dir'] for spec in specs}
    unstarted = main_line()
    for name, refs in sorted(git_branches().items()):
        match = pattern.match(name)
        if not match:
            continue
        folder, number = match.groups()
        if by_number.setdefault(number, folder) != folder:
            errors.append(f'feature number {number} is used by both {folder} and {by_number[number]}')
            continue
        if folder in in_tree:
            continue
        if any(git('cat-file', '-e', f'{ref}:{project}specs/{folder}/spec.md') is not None for ref in refs):
            continue
        tips = {(git('rev-parse', ref) or '').strip() for ref in refs}
        if tips <= unstarted:
            continue  # just created from main, spec not written yet
        errors.append(f'branch {name} has no specs/{folder}/spec.md. Numbered branches are only for '
                      f'Spec Kit features: add the spec, or use an unnumbered branch (docs/…, chore/…)')


def render(specs):
    lines = [START,
             '<!-- Generated from specs/*/spec.md by scripts/features.py --write. Do not edit by hand. -->',
             '',
             '| # | Feature | Branch | Status |',
             '|---|---|---|---|']
    for spec in specs:
        lines.append(f'| {spec["number"]} | [{spec["title"]}](specs/{spec["dir"]}/spec.md) '
                     f'| `{spec["branch"]}` | {spec["status"]} |')
    done = sum(spec['status'] == 'Implemented' for spec in specs)
    lines += ['', f'{done} of {len(specs)} specified features implemented.', END]
    return '\n'.join(lines)


def readme_block(text, errors):
    start, end = text.find(START), text.find(END)
    if start == -1 or end == -1 or end < start:
        errors.append(f'README.md: missing {START} … {END} markers')
        return None
    return start, end + len(END)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check', action='store_true', help='validate the ledger and README (for the pre-commit hook)')
    mode.add_argument('--write', action='store_true', help='regenerate the README feature table')
    args = parser.parse_args(argv)

    errors = []
    specs = load_specs(errors)
    text = README.read_text()
    span = readme_block(text, errors)
    if args.write:
        if span:
            README.write_text(text[:span[0]] + render(specs) + text[span[1]:])
            print(f'README.md feature table updated ({len(specs)} features)')
    else:
        check_branches(specs, errors)
        if span and text[span[0]:span[1]] != render(specs):
            errors.append('README.md feature table is out of date: run `python3 scripts/features.py --write` '
                          '(from CNN/image_classification) and stage README.md')
    for error in errors:
        print(f'feature ledger: {error}', file=sys.stderr)
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
