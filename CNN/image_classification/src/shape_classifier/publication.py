"""Recoverable checkpoint and results publication for sequential commands.

Concurrent access to the same outputs is unsupported and is not detected.
"""
import json
import os
import shutil
import signal
import tempfile
from pathlib import Path
from .benchmark import read_results, validate_entry


def _sync_dir(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _atomic_json(path, obj):
    path = Path(path)
    fd, name = tempfile.mkstemp(prefix='.benchmark-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(obj, f, allow_nan=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(name, path)
        _sync_dir(path.parent)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def _commit_results(path, entries):
    _atomic_json(path, {'version': 1, 'entries': entries})


def _sidecar(checkpoint):
    return Path(str(checkpoint) + '.transaction')


def _recover(journal):
    journal = Path(journal)
    if not journal.exists():
        raise RuntimeError(f'Pending benchmark journal is unavailable: {journal}')
    try:
        state = json.loads(journal.read_text())
        checkpoint = (journal.parent / state['checkpoint']).resolve()
        backup = checkpoint.parent / state['backup'] if state['backup'] else None
        result = journal.parent / 'benchmark-results.json'
        committed = any(e['run_id'] == state['run_id'] for e in read_results(result))
        if not committed:
            if backup:
                if not backup.exists():
                    raise OSError('checkpoint backup is unavailable')
                # Copy, rather than consume, the backup until the journal is removed:
                # recovery can be retried if interrupted during recovery itself.
                fd, temp = tempfile.mkstemp(prefix='.restore-', dir=checkpoint.parent)
                os.close(fd)
                try:
                    shutil.copyfile(backup, temp)
                    with open(temp, 'rb') as f:
                        os.fsync(f.fileno())
                    os.replace(temp, checkpoint)
                finally:
                    if os.path.exists(temp):
                        os.unlink(temp)
            elif checkpoint.exists():
                checkpoint.unlink()
            _sync_dir(checkpoint.parent)
        sidecar = _sidecar(checkpoint)
        if sidecar.exists():
            sidecar.unlink()
            _sync_dir(checkpoint.parent)
        journal.unlink()
        _sync_dir(journal.parent)
        if backup and backup.exists():
            backup.unlink()
    except Exception as exc:
        raise RuntimeError(f'Cannot recover pending benchmark transaction {journal}: {exc}') from exc


def recover_results(root):
    journal = Path(root).resolve() / '.benchmark-transaction.json'
    if journal.exists():
        _recover(journal)


def recover_checkpoint(checkpoint):
    sidecar = _sidecar(Path(checkpoint).resolve())
    if sidecar.exists():
        try:
            journal = (sidecar.parent / json.loads(sidecar.read_text())['journal']).resolve()
        except (OSError, ValueError, KeyError) as exc:
            raise RuntimeError(f'Cannot locate checkpoint recovery journal: {exc}') from exc
        _recover(journal)


def publish(root, checkpoint, write_checkpoint, entry):
    root = Path(root).resolve()
    checkpoint = Path(checkpoint).resolve()
    journal = root / '.benchmark-transaction.json'
    results = root / 'benchmark-results.json'
    sidecar = _sidecar(checkpoint)
    validate_entry(entry)
    recover_results(root)
    recover_checkpoint(checkpoint)
    entries = read_results(results)
    if any(e['run_id'] == entry['run_id'] for e in entries):
        raise ValueError('duplicate run ID')
    fd, staged = tempfile.mkstemp(prefix='.checkpoint-', dir=checkpoint.parent)
    os.close(fd)
    backup = None
    try:
        write_checkpoint(Path(staged))
        with open(staged, 'rb') as f:
            os.fsync(f.fileno())
        if checkpoint.exists():
            fd, backup = tempfile.mkstemp(prefix='.checkpoint-backup-', dir=checkpoint.parent)
            os.close(fd)
            shutil.copyfile(checkpoint, backup)
            with open(backup, 'rb') as f:
                os.fsync(f.fileno())
        state = {'run_id': entry['run_id'], 'checkpoint': os.path.relpath(checkpoint, root),
                 'backup': Path(backup).name if backup else None}
        _atomic_json(journal, state)
        _atomic_json(sidecar, {'journal': os.path.relpath(journal, checkpoint.parent)})
        old_mask = None
        if hasattr(signal, 'pthread_sigmask'):
            old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT, signal.SIGTERM})
        try:
            os.replace(staged, checkpoint)
            _sync_dir(checkpoint.parent)
            _commit_results(results, entries + [entry])
        except BaseException:
            committed = any(e['run_id'] == entry['run_id'] for e in read_results(results))
            _recover(journal)
            if not committed:
                raise
        else:
            _recover(journal)
        finally:
            if old_mask is not None:
                signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)
    finally:
        if os.path.exists(staged):
            os.unlink(staged)
        if backup and not journal.exists() and os.path.exists(backup):
            os.unlink(backup)
