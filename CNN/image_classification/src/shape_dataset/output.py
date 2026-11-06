"""Journalled publication of generator-owned files."""
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tempfile
from contextlib import contextmanager
from .config import CLASSES, SETS

MANIFEST = '.shape-dataset-manifest.json'
JOURNAL = '.shape-dataset-journal.json'
STAGE = '.shape-dataset-stage'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def path_for(root, name):
    if not isinstance(name, str):
        raise ValueError('Invalid image path')
    parts = PurePosixPath(name).parts
    if len(parts) != 3 or parts[0] not in SETS or parts[1] not in CLASSES or not parts[2].endswith('.png') or parts[2] in ('.', '..') or name != '/'.join(parts):
        raise ValueError(f'Invalid image path: {name}')
    p = root
    for part in parts:
        p = p / part
        if p.is_symlink():
            raise ValueError(f'Symlink is not allowed: {p}')
    return p


def atomic_json(path, value):
    if path.is_symlink():
        raise ValueError(f'Symlink is not allowed: {path}')
    fd, name = tempfile.mkstemp(prefix='.shape-tmp-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as file:
            json.dump(value, file, sort_keys=True)
        os.replace(name, path)
    finally:
        if os.path.exists(name): os.unlink(name)


def read_json(path):
    if path.is_symlink(): raise ValueError(f'Symlink is not allowed: {path}')
    return json.loads(path.read_text())


def manifest_paths(root):
    path = root / MANIFEST
    if not path.exists() and not path.is_symlink(): return []
    data = read_json(path)
    if not isinstance(data, dict) or data.get('version') != 1 or not isinstance(data.get('paths'), list): raise ValueError('Invalid ownership manifest')
    paths = data['paths']
    for name in paths: path_for(root, name)
    if len(set(paths)) != len(paths): raise ValueError('Duplicate manifest path')
    return paths


def recover(root):
    journal_path = root / JOURNAL
    if not journal_path.exists() and not journal_path.is_symlink(): return
    journal = read_json(journal_path)
    if not isinstance(journal, dict) or journal.get('version') != 1 or not isinstance(journal.get('entries'), list) or not isinstance(journal.get('stale'), list): raise ValueError('Invalid recovery journal')
    entries, stale = journal['entries'], journal['stale']
    seen = set()
    for item in entries + stale:
        if not isinstance(item, dict): raise ValueError('Invalid journal entry')
        name = item.get('path'); path_for(root, name)
        if name in seen: raise ValueError('Duplicate journal path')
        seen.add(name)
        for key in (('prior', 'desired') if item in entries else ('prior',)):
            v = item.get(key)
            if not (key == 'prior' and v is None) and (not isinstance(v, str) or len(v) != 64 or any(c not in '0123456789abcdef' for c in v)): raise ValueError('Invalid journal digest')
    stage = root / STAGE
    if stage.is_symlink() or (stage.exists() and not stage.is_dir()): raise ValueError('Unsafe recovery staging directory')
    # Validate all states before any change.
    for item in entries:
        dest = path_for(root, item['path']); staged = path_for(stage, item['path'])
        current = digest(dest) if dest.exists() else None
        if current not in (item['prior'], item['desired']): raise ValueError(f'Unexpected destination content: {dest}')
        if current != item['desired'] and (not staged.is_file() or digest(staged) != item['desired']): raise ValueError(f'Missing or invalid staged image: {staged}')
    for item in stale:
        dest = path_for(root, item['path'])
        if dest.exists() and digest(dest) != item['prior']: raise ValueError(f'Unexpected stale file content: {dest}')
    for item in entries:
        dest = path_for(root, item['path'])
        if dest.exists() and digest(dest) == item['desired']: continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        fd, temp = tempfile.mkstemp(prefix='.shape-tmp-', dir=dest.parent)
        os.close(fd)
        try:
            shutil.copyfile(path_for(stage, item['path']), temp)
            os.replace(temp, dest)
        finally:
            if os.path.exists(temp): os.unlink(temp)
    for item in stale:
        dest = path_for(root, item['path'])
        if dest.exists(): dest.unlink()
    atomic_json(root / MANIFEST, {'version': 1, 'paths': [item['path'] for item in entries]})
    if stage.exists(): shutil.rmtree(stage)
    journal_path.unlink()


@contextmanager
def locked(root):
    root.mkdir(parents=True, exist_ok=True)
    lock = root / '.shape-dataset.lock'
    if lock.is_symlink(): raise ValueError('Unsafe lock path')
    with lock.open('a') as file:
        fcntl.flock(file, fcntl.LOCK_EX)
        yield


def publish(root, images):
    root = Path(root)
    with locked(root):
        recover(root)
        owned = set(manifest_paths(root))
        stage = root / STAGE
        if stage.is_symlink() or stage.exists(): raise ValueError('Unexpected staging directory; inspect it before retrying')
        entries = []
        for name in images:
            dest = path_for(root, name)
            if dest.exists() and name not in owned: raise ValueError(f'Untracked destination collision: {dest}')
            entries.append({'path': name, 'prior': digest(dest) if dest.exists() else None, 'desired': hashlib.sha256(images[name]).hexdigest()})
        stale = []
        for name in sorted(owned - images.keys()):
            dest = path_for(root, name)
            if dest.exists(): stale.append({'path': name, 'prior': digest(dest)})
        stage.mkdir()
        try:
            for name, data in images.items():
                dest = path_for(stage, name); dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(data)
            atomic_json(root / JOURNAL, {'version': 1, 'entries': entries, 'stale': stale})
        except BaseException:
            if not (root / JOURNAL).exists(): shutil.rmtree(stage)
            raise
        recover(root)
