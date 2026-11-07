"""Predict one image using the checkpoint's class order."""
from PIL import Image
import torch
from .checkpoint import load_checkpoint
from .transforms import preprocess


def predict(image_path, checkpoint, device="cpu"):
    model, metadata = load_checkpoint(checkpoint)
    model.to(device)
    try:
        with Image.open(image_path) as image:
            tensor = preprocess(image.convert('RGB'))
    except (OSError, ValueError) as exc:
        raise ValueError(f'Cannot read image {image_path}: {exc}') from exc
    with torch.inference_mode():
        index = int(model(tensor.unsqueeze(0).to(device)).argmax(dim=1).item())
    return metadata['class_order'][index]
