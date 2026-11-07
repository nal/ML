import tempfile
import unittest
from pathlib import Path
from shape_classifier.benchmark import read_results, format_summary


class ResultTests(unittest.TestCase):
    def test_missing_and_malformed(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'benchmark-results.json'
            self.assertEqual(read_results(path), [])
            self.assertIn('no results yet', format_summary([]).lower())
            path.write_text('{broken')
            with self.assertRaises(ValueError):
                read_results(path)
            self.assertEqual(path.read_text(), '{broken')

    def test_invalid_entry_rejected_without_modifying_results_or_checkpoint(self):
        import contextlib
        import io
        import json
        from shape_classifier.__main__ import main
        from shape_classifier.publication import publish
        from shape_classifier.train import train
        from unittest.mock import patch
        import torch

        class TinyDataset(torch.utils.data.Dataset):
            def __init__(self, *args): pass
            def __len__(self): return 2
            def __getitem__(self, index): return torch.tensor([float(index)]), index

        valid = dict(run_id='run', timestamp='2026-01-01T00:00:00+00:00',
                     environment='native', device='cpu', python_version='3.14.10',
                     pytorch_version='2.15.0', data_id='abc', epochs=1, batch_size=8,
                     cpu_threads=1, seed=42, train_correct=1, train_total=2,
                     held_out_correct=1, held_out_total=2, training_seconds=None,
                     epoch_seconds=None, inference_seconds=0.1, loss=1.0,
                     docker_cpus=None, docker_memory=None)
        invalid = [dict(valid, training_seconds=0), dict(valid, epoch_seconds=0),
                   dict(valid, timestamp='not-a-date'), dict(valid, timestamp='2026-01-01'),
                   dict(valid, timestamp='2026-01-01T00:00:00+03:00')]
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            results = root / 'benchmark-results.json'
            checkpoint = root / 'model.pth'
            checkpoint.write_bytes(b'original')
            for entry in invalid:
                with self.subTest(entry=entry):
                    raw = json.dumps({'version': 1, 'entries': [entry]})
                    results.write_text(raw)
                    with contextlib.redirect_stderr(io.StringIO()):
                        self.assertEqual(main(['summary', '--data-dir', str(root)]), 1)
                    with self.assertRaisesRegex(ValueError, 'Invalid benchmark results'):
                        publish(root, checkpoint, lambda p: p.write_bytes(b'new'), valid)
                    with patch('shape_classifier.train.ShapeDataset', TinyDataset), \
                         patch('shape_classifier.train.ShapeClassifier', lambda: torch.nn.Linear(1, 2)), \
                         patch('shape_classifier.train.augment', lambda image: image), \
                         patch('shape_classifier.train.dataset_fingerprint', return_value='abc'), \
                         patch('shape_classifier.train.available_cpus', return_value=1):
                        with self.assertRaisesRegex(ValueError, 'Invalid benchmark results'):
                            train(root, checkpoint, epochs=1, batch_size=2, environment='native')
                    self.assertEqual(results.read_text(), raw)
                    self.assertEqual(checkpoint.read_bytes(), b'original')
