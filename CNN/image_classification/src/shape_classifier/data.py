"""Validate and cache the two required datasets."""
from pathlib import Path

from PIL import Image
from torch.utils.data import Dataset
from .transforms import preprocess

CLASS_ORDER = ["circle", "rectangle", "triangle"]


class ShapeDataset(Dataset):
    def __init__(self, root, split):
        if split not in ("train", "held-out"):
            raise ValueError(f"Invalid split: {split}")
        directory = Path(root) / split
        if not directory.is_dir():
            raise ValueError(f"Missing dataset directory: {directory}")
        unexpected = [p.name for p in directory.iterdir() if p.is_dir() and p.name not in CLASS_ORDER]
        unexpected += [p.name for p in directory.iterdir() if p.is_file() and p.suffix.lower() == '.png']
        if unexpected:
            raise ValueError(f"Unexpected dataset labels or images in {directory}: {unexpected}")
        self.samples = []
        expected = 10 if split == 'train' else 5
        for label, name in enumerate(CLASS_ORDER):
            folder = directory / name
            if not folder.is_dir():
                raise ValueError(f"Missing class directory: {folder}")
            images = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == '.png')
            if len(images) != expected:
                raise ValueError(f"Expected {expected} PNG images in {folder}, found {len(images)}")
            for path in images:
                try:
                    with Image.open(path) as image:
                        if image.format != 'PNG':
                            raise ValueError('not a PNG image')
                        tensor = preprocess(image.convert('RGB'))
                except (OSError, ValueError) as exc:
                    raise ValueError(f"Unreadable PNG image {path}: {exc}") from exc
                self.samples.append((tensor, label))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        return self.samples[index]


def dataset_fingerprint(root):
    """Fingerprint sorted relative names and bytes across both dataset splits."""
    import hashlib
    root = Path(root)
    digest = hashlib.sha256()
    for split in ('train', 'held-out'):
        for path in sorted((root / split).rglob('*.png')):
            name = path.relative_to(root).as_posix().encode()
            contents = path.read_bytes()
            for part in (name, contents):
                digest.update(len(part).to_bytes(8, 'big'))
                digest.update(part)
    return digest.hexdigest()
