import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from shape_classifier.publication import publish


class PublicationTests(unittest.TestCase):
    def test_failed_result_write_preserves_checkpoint(self):
        with tempfile.TemporaryDirectory() as root:
            checkpoint = Path(root) / 'model.pth'
            checkpoint.write_bytes(b'old')
            entry = dict(run_id='run', timestamp='2026-01-01T00:00:00+00:00', environment='native', device='cpu', python_version='3.14.10', pytorch_version='2.15.0', data_id='abc', epochs=1, batch_size=8, cpu_threads=1, seed=42, train_correct=1, train_total=2, held_out_correct=1, held_out_total=2, training_seconds=None, epoch_seconds=None, inference_seconds=0.1, loss=1.0, docker_cpus=None, docker_memory=None)
            with patch('shape_classifier.publication._commit_results', side_effect=OSError('failed')):
                with self.assertRaises(OSError):
                    publish(Path(root), checkpoint, lambda path: path.write_bytes(b'new'), entry)
            self.assertEqual(checkpoint.read_bytes(), b'old')
            self.assertFalse((Path(root) / 'benchmark-results.json').exists())
