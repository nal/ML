"""Atomic CPU checkpoint storage and strict metadata validation."""
import os
import tempfile
from pathlib import Path

import torch
from .data import CLASS_ORDER
from .model import ShapeClassifier


def save_checkpoint(path, model, seed, train_seed, held_out_seed, environment="docker", device="cpu"):
    metadata = {'class_order': CLASS_ORDER.copy(), 'input_size': [144, 256],
                'pixel_scaling': 'float32_0_1', 'training_seed': seed,
                'dataset_train_seed': train_seed if train_seed is not None else 'unknown',
                'dataset_held_out_seed': held_out_seed if held_out_seed is not None else 'unknown',
                'pytorch_version': str(torch.__version__), 'environment': environment, 'device': device}
    destination = Path(path)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, prefix='.shapes-', suffix='.tmp', delete=False) as file:
            temp = file.name
            torch.save({'state_dict': {k: v.detach().cpu() for k, v in model.state_dict().items()},
                        'metadata': metadata}, file)
        os.replace(temp, destination)
    finally:
        if temp and os.path.exists(temp):
            os.unlink(temp)


def load_checkpoint(path):
    try:
        from .publication import recover_checkpoint, locked, _checkpoint_lock, _sidecar
        while True:
            recover_checkpoint(path)
            with locked(_checkpoint_lock(path)):
                if _sidecar(path).exists():
                    continue
                checkpoint = torch.load(path, map_location='cpu', weights_only=True)
                break
        if not isinstance(checkpoint, dict) or set(checkpoint) != {'state_dict', 'metadata'}:
            raise ValueError('invalid checkpoint structure')
        meta = checkpoint['metadata']
        expected = {'class_order': CLASS_ORDER, 'input_size': [144, 256],
                    'pixel_scaling': 'float32_0_1'}
        if not isinstance(meta, dict) or any(meta.get(k) != v for k, v in expected.items()):
            raise ValueError('incompatible checkpoint metadata')
        if meta.get('environment') not in ('docker', 'native') or meta.get('device') not in ('cpu', 'mps'):
            raise ValueError('invalid checkpoint provenance')
        if meta['environment'] == 'docker' and meta['device'] != 'cpu':
            raise ValueError('invalid checkpoint provenance')
        if type(meta.get('training_seed')) is not int or not isinstance(meta.get('pytorch_version'), str):
            raise ValueError('invalid checkpoint provenance')
        for key in ('dataset_train_seed', 'dataset_held_out_seed'):
            value = meta.get(key)
            if type(value) is not int and value != 'unknown':
                raise ValueError(f'invalid checkpoint {key}')
        model = ShapeClassifier()
        model.load_state_dict(checkpoint['state_dict'], strict=True)
        model.eval()
        return model, meta
    except Exception as exc:
        raise ValueError(f'Cannot load checkpoint {path}: {exc}') from exc
