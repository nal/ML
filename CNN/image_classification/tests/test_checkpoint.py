"""Checkpoint provenance and portable CPU state."""
import tempfile
import unittest
from pathlib import Path
import torch
from shape_classifier.checkpoint import load_checkpoint, save_checkpoint
from shape_classifier.model import ShapeClassifier


class CheckpointTests(unittest.TestCase):
    def test_legacy_and_cross_environment(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'model.pth'
            save_checkpoint(path, ShapeClassifier(), 42, None, None)
            _, meta = load_checkpoint(path)
            self.assertEqual((meta['environment'], meta['device']), ('docker', 'cpu'))
            save_checkpoint(path, ShapeClassifier(), 42, None, None, 'native', 'mps')
            _, meta = load_checkpoint(path)
            self.assertEqual((meta['environment'], meta['device']), ('native', 'mps'))
            raw = torch.load(path, map_location='cpu', weights_only=True)
            self.assertTrue(all(v.device.type == 'cpu' for v in raw['state_dict'].values()))
            raw['metadata']['device'] = 'bogus'
            torch.save(raw, path)
            with self.assertRaises(ValueError):
                load_checkpoint(path)
