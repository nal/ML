"""Classifier contract tests using small temporary image sets."""
import tempfile
import unittest
import subprocess
import sys
import inspect
from pathlib import Path
from unittest.mock import patch

import torch
from PIL import Image
from shape_classifier.checkpoint import load_checkpoint, save_checkpoint
from shape_classifier.data import CLASS_ORDER, ShapeDataset
from shape_classifier.model import ShapeClassifier
from shape_classifier.predict import predict
from shape_classifier.train import assess
from shape_classifier.train import train as train_classifier
from shape_classifier.__main__ import main
from shape_classifier.transforms import preprocess


class TrainingDefaultsTests(unittest.TestCase):
    def test_default_and_overrides_reach_training(self):
        with patch('shape_classifier.__main__.train', return_value=[(1, 30), (1, 15)]) as run:
            self.assertEqual(main(['train']), 0)
            self.assertEqual(run.call_args.args[3], 60)
            self.assertEqual(inspect.signature(train_classifier).parameters['epochs'].default, 60)
            for epochs in (1, 30):
                self.assertEqual(main(['train', '--epochs', str(epochs)]), 0)
                self.assertEqual(run.call_args.args[3], epochs)
            for value in ('0', '-1', '1.5'):
                with self.assertRaises(SystemExit) as error:
                    main(['train', '--epochs', value])
                self.assertNotEqual(error.exception.code, 0)


class ClassifierTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for split, count in [('train', 10), ('held-out', 5)]:
            for label in CLASS_ORDER:
                folder = self.root / split / label
                folder.mkdir(parents=True)
                for i in range(count):
                    Image.new('RGB', (8, 8), (i, 100, 200)).save(folder / f'{i}.png')

    def legacy_checkpoint(self):
        """Create a feature 002/003-format CPU checkpoint in this fixture."""
        path = self.root / "legacy.pth"
        save_checkpoint(path, ShapeClassifier(), 42, None, None)
        return path

    def test_cache_and_paired_assessment(self):
        with patch('shape_classifier.data.preprocess', wraps=preprocess) as resize:
            train = ShapeDataset(self.root, 'train')
            held = ShapeDataset(self.root, 'held-out')
            self.assertEqual(resize.call_count, 45)
        self.assertEqual(train[0][0].shape, (3, 144, 256))
        self.assertEqual(train[0][0].dtype, torch.float32)
        self.assertTrue(0 <= train[0][0].min() <= train[0][0].max() <= 1)
        with patch('PIL.Image.open', side_effect=AssertionError('cache reread')), patch('shape_classifier.train.augment', side_effect=AssertionError('evaluation augmented')):
            self.assertEqual([total for _, total in assess(ShapeClassifier(), train, held)], [30, 15])

    def test_bad_datasets_rejected(self):
        (self.root / 'held-out' / 'circle' / '0.png').unlink()
        with self.assertRaisesRegex(ValueError, 'Expected 5'):
            ShapeDataset(self.root, 'held-out')
        path = self.root / 'model.pth'
        save_checkpoint(path, ShapeClassifier(), 42, None, None)
        result = subprocess.run([sys.executable, '-m', 'shape_classifier', 'evaluate', '--data-dir', str(self.root), '--checkpoint', str(path)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('Training:', result.stdout)
        (self.root / 'train' / 'unknown').mkdir()
        with self.assertRaisesRegex(ValueError, 'Unexpected'):
            ShapeDataset(self.root, 'train')

    def test_checkpoint_prediction_and_metadata(self):
        path = self.root / 'model.pth'
        save_checkpoint(path, ShapeClassifier(), 42, None, 43)
        raw = torch.load(path, map_location='cpu', weights_only=True)
        self.assertEqual(raw['metadata']['dataset_train_seed'], 'unknown')
        self.assertEqual(raw['metadata']['dataset_held_out_seed'], 43)
        self.assertTrue(all(v.device.type == 'cpu' for v in raw['state_dict'].values()))
        model, metadata = load_checkpoint(path)
        self.assertEqual(metadata['class_order'], CLASS_ORDER)
        self.assertIn(predict(self.root / 'train' / 'circle' / '0.png', path), CLASS_ORDER)
        raw['metadata']['input_size'] = [1, 1]
        torch.save(raw, path)
        with self.assertRaisesRegex(ValueError, 'incompatible'):
            load_checkpoint(path)
        with self.assertRaises(ValueError):
            predict(self.root / 'missing.png', path)


if __name__ == '__main__':
    unittest.main()
