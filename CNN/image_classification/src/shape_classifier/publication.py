"""Coordinate benchmark and checkpoint publication under stable advisory locks."""
import contextlib
import fcntl
import json
import os
import shutil
import signal
import tempfile
import uuid
from pathlib import Path
from .benchmark import read_results, validate_entry


@contextlib.contextmanager
def locked(*paths):
    handles = []
    try:
        for path in sorted({str(Path(p).resolve()) for p in paths}):
            f = open(path, 'a+b')
            handles.append(f)
            fcntl.flock(f, fcntl.LOCK_EX)
        yield
    finally:
        for f in reversed(handles):
            fcntl.flock(f, fcntl.LOCK_UN)
            f.close()


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
        if os.path.exists(name): os.unlink(name)


def _commit_results(path, entries):
    _atomic_json(path, {'version': 1, 'entries': entries})


def _sidecar(checkpoint):
    return Path(str(checkpoint) + '.transaction')


def _checkpoint_lock(checkpoint):
    return Path(str(checkpoint) + '.lock')


def _result_lock(root):
    return Path(root) / '.benchmark.lock'


def _recover_locked(journal):
    journal = Path(journal)
    if not journal.exists():
        return
    try:
        state = json.loads(journal.read_text())
        checkpoint = (journal.parent / state['checkpoint']).resolve()
        backup = (checkpoint.parent / state['backup']) if state['backup'] else None
        result = journal.parent / 'benchmark-results.json'
        committed = any(e['run_id'] == state['run_id'] for e in read_results(result))
        if not committed:
            if backup:
                if not backup.exists(): raise OSError('checkpoint backup is unavailable')
                os.replace(backup, checkpoint)
            elif checkpoint.exists():
                checkpoint.unlink()
            _sync_dir(checkpoint.parent)
        if backup and backup.exists(): backup.unlink()
        sidecar = _sidecar(checkpoint)
        if sidecar.exists(): sidecar.unlink()
        journal.unlink()
        _sync_dir(journal.parent)
    except Exception as exc:
        raise RuntimeError(f'Cannot recover pending benchmark transaction {journal}: {exc}') from exc



def recover_results(root):
    root = Path(root).resolve()
    journal = root / '.benchmark-transaction.json'
    while True:
        with locked(_result_lock(root)):
            if not journal.exists():
                return
            try:
                state = json.loads(journal.read_text())
                checkpoint = (root / state['checkpoint']).resolve()
            except (OSError, ValueError, KeyError) as exc:
                raise RuntimeError(f'Cannot locate benchmark recovery checkpoint: {exc}') from exc
        with locked(_result_lock(root), _checkpoint_lock(checkpoint)):
            if journal.exists():
                current = json.loads(journal.read_text())
                if (root / current['checkpoint']).resolve() == checkpoint:
                    _recover_locked(journal)


def recover_checkpoint(checkpoint):
    checkpoint = Path(checkpoint).resolve()
    sidecar = _sidecar(checkpoint)
    # Writers also take the checkpoint lock; retry if the sidecar changes while acquiring locks.
    while sidecar.exists():
        try:
            journal = (sidecar.parent / json.loads(sidecar.read_text())['journal']).resolve()
        except (OSError, ValueError, KeyError) as exc:
            raise RuntimeError(f'Cannot locate checkpoint recovery journal: {exc}') from exc
        with locked(_checkpoint_lock(checkpoint), _result_lock(journal.parent)):
            if sidecar.exists():
                _recover_locked(journal)


class PendingTransaction(Exception):
    pass


def _publish_once(root, checkpoint, write_checkpoint, entry):
    root = Path(root).resolve()
    checkpoint = Path(checkpoint).resolve()
    journal = root / '.benchmark-transaction.json'
    results = root / 'benchmark-results.json'
    sidecar = _sidecar(checkpoint)
    validate_entry(entry)
    recover_results(root)
    recover_checkpoint(checkpoint)
    with locked(_result_lock(root), _checkpoint_lock(checkpoint)):
        if journal.exists(): raise PendingTransaction()
        if sidecar.exists(): raise PendingTransaction()
        entries = read_results(results)
        if any(e['run_id'] == entry['run_id'] for e in entries):
            raise ValueError('duplicate run ID')
        fd, staged = tempfile.mkstemp(prefix='.checkpoint-', dir=checkpoint.parent)
        os.close(fd)
        backup = None
        try:
            write_checkpoint(Path(staged))
            with open(staged, 'rb') as f: os.fsync(f.fileno())
            if checkpoint.exists():
                fd, backup = tempfile.mkstemp(prefix='.checkpoint-backup-', dir=checkpoint.parent)
                os.close(fd)
                shutil.copyfile(checkpoint, backup)
                with open(backup, 'rb') as f: os.fsync(f.fileno())
            state = {'run_id': entry['run_id'], 'checkpoint': os.path.relpath(checkpoint, root),
                     'backup': Path(backup).name if backup else None}
            # A journal without a sidecar is discoverable from the results directory.
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
                _recover_locked(journal)
                if not committed:
                    raise
            finally:
                if old_mask is not None: signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)
            _recover_locked(journal)
        finally:
            if os.path.exists(staged): os.unlink(staged)
            # Preserve backups if a journal still needs recovery.
            if backup and not journal.exists() and os.path.exists(backup): os.unlink(backup)


def publish(root, checkpoint, write_checkpoint, entry):
    while True:
        try:
            return _publish_once(root, checkpoint, write_checkpoint, entry)
        except PendingTransaction:
            continue
