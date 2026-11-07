"""Validated benchmark entries and grouped comparison output."""
import json
import math
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean


def excluded_times(times):
    return (sum(times[1:]), mean(times[1:])) if len(times) > 1 else (None, None)


def read_results(path):
    path = Path(path)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        if not isinstance(data, dict) or data.get('version') != 1 or not isinstance(data.get('entries'), list):
            raise ValueError('unsupported result format')
        for entry in data['entries']:
            validate_entry(entry)
        return data['entries']
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise ValueError(f'Invalid benchmark results {path}: {exc}') from exc


def validate_entry(e):
    if not isinstance(e, dict):
        raise ValueError('entry must be an object')
    for key in ('run_id', 'timestamp', 'environment', 'device', 'python_version', 'pytorch_version', 'data_id'):
        if not isinstance(e.get(key), str) or not e[key]:
            raise ValueError(f'invalid {key}')
    try:
        timestamp = datetime.fromisoformat(e['timestamp'])
    except ValueError as exc:
        raise ValueError('invalid UTC timestamp') from exc
    if timestamp.tzinfo is None or timestamp.utcoffset() != timedelta(0):
        raise ValueError('invalid UTC timestamp')
    if e['environment'] not in ('native', 'docker') or e['device'] not in ('cpu', 'mps') or (e['environment'], e['device']) == ('docker', 'mps'):
        raise ValueError('invalid environment or device')
    for key in ('epochs', 'batch_size', 'cpu_threads'):
        if type(e.get(key)) is not int or e[key] <= 0:
            raise ValueError(f'invalid {key}')
    if type(e.get('seed')) is not int:
        raise ValueError('invalid seed')
    for split in ('train', 'held_out'):
        c, t = e[f'{split}_correct'], e[f'{split}_total']
        if type(c) is not int or type(t) is not int or t <= 0 or not 0 <= c <= t:
            raise ValueError('invalid accuracy counts')
    for key in ('training_seconds', 'epoch_seconds', 'inference_seconds', 'loss'):
        v = e[key]
        if key in ('training_seconds', 'epoch_seconds') and e['epochs'] == 1:
            if v is not None:
                raise ValueError(f'invalid {key} for one epoch')
            continue
        if type(v) not in (int, float) or not math.isfinite(v) or v < 0:
            raise ValueError(f'invalid {key}')
    for key in ('docker_cpus', 'docker_memory'):
        v = e[key]
        if e['environment'] == 'native':
            if v is not None: raise ValueError(f'invalid {key}')
        elif v != 'unknown' and (type(v) is not int or v <= 0):
            raise ValueError(f'invalid {key}')


def format_summary(entries):
    if not entries:
        return 'No results yet.'
    groups = defaultdict(list)
    for e in entries:
        validate_entry(e)
        groups[(e['data_id'], e['seed'], e['epochs'], e['batch_size'])].append(e)
    lines = []
    for key, group in sorted(groups.items()):
        lines.append(f'Data: {key[0]}; seed: {key[1]}; epochs: {key[2]}; batch size: {key[3]}')
        lines.append('Environment Device Runs Training(s) Epoch(s) Inference(s/image) Loss Train accuracy Held-out accuracy')
        for environment, device in (('docker', 'cpu'), ('native', 'cpu'), ('native', 'mps')):
            rows = [e for e in group if (e['environment'], e['device']) == (environment, device)]
            if not rows:
                lines.append(f'{environment} {device} 0 not yet measured')
                continue
            def avg(key):
                values = [e[key] for e in rows if e[key] is not None]
                return f'{mean(values):.6f}' if values else 'unavailable'
            train = mean(e['train_correct']/e['train_total'] for e in rows)
            held = mean(e['held_out_correct']/e['held_out_total'] for e in rows)
            lines.append(f'{environment} {device} {len(rows)} {avg("training_seconds")} {avg("epoch_seconds")} {avg("inference_seconds")} {avg("loss")} {train:.4f} {held:.4f}')
    lines.append('Small synthetic demo; CPU and GPU arithmetic differ, resources vary, and GPU may be slower.')
    return '\n'.join(lines)
