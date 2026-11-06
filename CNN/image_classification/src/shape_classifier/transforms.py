"""Shared image preprocessing and training-only augmentation."""
import torch
from torchvision.transforms import v2

preprocess = v2.Compose([v2.Resize((144, 256)), v2.ToImage(), v2.ToDtype(torch.float32, scale=True)])
augment = v2.Compose([v2.RandomRotation(10), v2.RandomHorizontalFlip(p=0.5),
                      v2.RandomVerticalFlip(p=0.5),
                      v2.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1)])
