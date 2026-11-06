"""Deterministic CPU training and paired assessment."""
import random
import numpy as np
import torch
from torch.utils.data import DataLoader
from .checkpoint import load_checkpoint, save_checkpoint
from .data import ShapeDataset
from .model import ShapeClassifier
from .transforms import augment


def assess(model, train_data, held_out_data):
    results = []
    model.eval()
    with torch.inference_mode():
        for data in (train_data, held_out_data):
            correct = total = 0
            for images, labels in DataLoader(data, batch_size=8):
                correct += int((model(images).argmax(dim=1) == labels).sum().item())
                total += len(labels)
            results.append((correct, total))
    return results


def train(data_dir, checkpoint, seed=42, epochs=60, batch_size=8, dataset_train_seed=None, dataset_held_out_seed=None):
    random.seed(seed)
    np.random.seed(seed % (2**32))
    torch.manual_seed(seed)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    train_data = ShapeDataset(data_dir, 'train')
    held_out_data = ShapeDataset(data_dir, 'held-out')
    model = ShapeClassifier()
    loader = DataLoader(train_data, batch_size=batch_size, shuffle=True)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = torch.nn.CrossEntropyLoss()
    model.train()
    for _ in range(epochs):
        for images, labels in loader:
            images = torch.stack([augment(image) for image in images])
            optimizer.zero_grad()
            loss = criterion(model(images), labels)
            loss.backward()
            optimizer.step()
    results = assess(model, train_data, held_out_data)
    save_checkpoint(checkpoint, model, seed, dataset_train_seed, dataset_held_out_seed)
    return results


def evaluate(data_dir, checkpoint):
    torch.set_num_threads(1)
    model, _ = load_checkpoint(checkpoint)
    return assess(model, ShapeDataset(data_dir, 'train'), ShapeDataset(data_dir, 'held-out'))
