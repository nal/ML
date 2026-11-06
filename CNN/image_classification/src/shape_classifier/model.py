"""Stable architecture used for both training and checkpoint loading."""
from torch import nn


class ShapeClassifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(nn.Conv2d(3, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
                                      nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
                                      nn.AdaptiveAvgPool2d((1, 1)), nn.Flatten())
        self.classifier = nn.Linear(32, 3)

    def forward(self, x):
        return self.classifier(self.features(x))
