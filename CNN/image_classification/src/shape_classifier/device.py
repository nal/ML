"""Detect the runtime and select a usable PyTorch device."""
import os
from pathlib import Path
import torch


def in_docker():
    if Path('/.dockerenv').exists() or Path('/run/.containerenv').exists():
        return True
    try:
        return any(token in Path('/proc/1/cgroup').read_text() for token in ('docker', 'containerd', 'kubepods'))
    except OSError:
        return False


def mps_usable():
    if not torch.backends.mps.is_available():
        return False
    try:
        torch.ones(1, device='mps').cpu()
        torch.mps.synchronize()
        return True
    except (RuntimeError, NotImplementedError):
        return False


def resolve_device(choice='auto'):
    if choice not in ('auto', 'cpu', 'mps'):
        raise ValueError(f'Invalid device: {choice}')
    environment = 'docker' if in_docker() else 'native'
    usable = environment == 'native' and choice != 'cpu' and mps_usable()
    if choice == 'mps' and not usable:
        raise ValueError(f'MPS GPU is unavailable in the {environment} environment; use --device cpu or auto')
    return environment, 'mps' if usable else 'cpu'


def available_cpus():
    """Return CPUs available to this process, honoring affinity and cgroup quotas."""
    import math
    count = len(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else (os.cpu_count() or 1)
    try:
        quota, period = Path('/sys/fs/cgroup/cpu.max').read_text().split()
        if quota != 'max':
            count = min(count, max(1, math.ceil(int(quota) / int(period))))
    except (OSError, ValueError, ZeroDivisionError):
        pass
    return max(1, count)


def docker_resources(environment):
    """Report VM resources only where container constraints don't obscure them."""
    if environment != 'docker':
        return None, None
    cpus = 'unknown'
    memory = 'unknown'
    try:
        visible = os.cpu_count()
        available = available_cpus()
        if visible and available == visible:
            cpus = visible
    except (OSError, ValueError):
        pass
    try:
        lines = Path('/proc/meminfo').read_text().splitlines()
        total = next(int(line.split()[1]) * 1024 for line in lines if line.startswith('MemTotal:'))
        try:
            limit = Path('/sys/fs/cgroup/memory.max').read_text().strip()
        except OSError:
            limit = Path('/sys/fs/cgroup/memory/memory.limit_in_bytes').read_text().strip()
        if limit == 'max' or int(limit) >= total:
            memory = total
    except (OSError, ValueError, IndexError, StopIteration):
        pass
    return cpus, memory
