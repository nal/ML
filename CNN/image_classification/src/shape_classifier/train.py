"""Deterministic CPU training and paired assessment."""
import random
import platform
import sys
import time
import uuid
from datetime import datetime, timezone
import numpy as np
import torch
from torch.utils.data import DataLoader
from .checkpoint import load_checkpoint, save_checkpoint
from .data import ShapeDataset, dataset_fingerprint
from .benchmark import excluded_times
from .device import available_cpus, docker_resources
from .publication import publish, recover_checkpoint
from .model import ShapeClassifier
from .transforms import augment


def assess(model, train_data, held_out_data, device="cpu"):
    results = []
    model.eval()
    with torch.inference_mode():
        for data in (train_data, held_out_data):
            correct = total = 0
            for images, labels in DataLoader(data, batch_size=8):
                correct += int((model(images.to(device)).argmax(dim=1) == labels.to(device)).sum().item())
                total += len(labels)
            results.append((correct, total))
    return results


def train(data_dir, checkpoint, seed=42, epochs=60, batch_size=8, dataset_train_seed=None, dataset_held_out_seed=None, device="cpu", environment="docker", cpu_threads=None):
    available = available_cpus()
    if cpu_threads is not None and (type(cpu_threads) is not int or cpu_threads <= 0 or cpu_threads > available):
        raise ValueError(f'Requested {cpu_threads} CPU threads; {available} available')
    torch.set_num_threads(cpu_threads or available)
    if cpu_threads is not None and torch.get_num_threads() != cpu_threads:
        raise RuntimeError('Could not configure the requested CPU thread count')
    cpus, memory = docker_resources(environment)
    if environment == 'docker':
        if cpus == 'unknown':
            print('Warning: Docker VM CPU count could not be verified.', file=sys.stderr)
        else:
            print(f'Docker VM CPUs: {cpus}; CPU threads: {torch.get_num_threads()}', file=sys.stderr)
            if cpu_threads is not None and cpu_threads != cpus:
                print(f'Warning: Docker VM has {cpus} CPUs and {cpu_threads} threads were requested; run is not core-matched.', file=sys.stderr)
    random.seed(seed)
    np.random.seed(seed % (2**32))
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)
    train_data = ShapeDataset(data_dir, 'train')
    held_out_data = ShapeDataset(data_dir, 'held-out')
    model = ShapeClassifier().to(device)
    loader = DataLoader(train_data, batch_size=batch_size, shuffle=True)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = torch.nn.CrossEntropyLoss()
    model.train()
    times = []
    for _ in range(epochs):
        if device == "mps": torch.mps.synchronize()
        start = time.perf_counter()
        total_loss = total_examples = 0
        for images, labels in loader:
            images = torch.stack([augment(image) for image in images]).to(device)
            labels = labels.to(device)
            optimizer.zero_grad()
            loss = criterion(model(images), labels)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(labels)
            total_examples += len(labels)
        if device == 'mps': torch.mps.synchronize()
        times.append(time.perf_counter() - start)
    results = assess(model, train_data, held_out_data, device)
    model.eval()
    if device == 'mps': torch.mps.synchronize()
    start = time.perf_counter()
    with torch.inference_mode():
        for images, _ in DataLoader(held_out_data, batch_size=batch_size):
            model(images.to(device))
    if device == 'mps': torch.mps.synchronize()
    inference = (time.perf_counter() - start) / len(held_out_data)
    elapsed, per_epoch = excluded_times(times)
    entry = dict(run_id=str(uuid.uuid4()), timestamp=datetime.now(timezone.utc).isoformat(),
                 environment=environment, device=device, python_version=platform.python_version(),
                 pytorch_version=str(torch.__version__), cpu_threads=torch.get_num_threads(), requested_cpu_threads=cpu_threads,
                 docker_cpus=cpus, docker_memory=memory, seed=seed, epochs=epochs,
                 batch_size=batch_size, data_id=dataset_fingerprint(data_dir),
                 training_seconds=elapsed, epoch_seconds=per_epoch, inference_seconds=inference,
                 loss=total_loss / total_examples, train_correct=results[0][0], train_total=results[0][1],
                 held_out_correct=results[1][0], held_out_total=results[1][1])
    if environment == 'docker':
        entry['docker_cpu_provenance'] = 'unknown' if cpus == 'unknown' else 'launcher'
    recover_checkpoint(checkpoint)
    publish(data_dir, checkpoint,
            lambda path: save_checkpoint(path, model, seed, dataset_train_seed, dataset_held_out_seed, environment, device), entry)
    return results


def evaluate(data_dir, checkpoint, device="cpu"):
    torch.set_num_threads(1)
    model, _ = load_checkpoint(checkpoint)
    return assess(model.to(device), ShapeDataset(data_dir, 'train'), ShapeDataset(data_dir, 'held-out'), device)
