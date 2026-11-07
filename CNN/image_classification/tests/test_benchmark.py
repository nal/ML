import tempfile
import unittest
from pathlib import Path
from shape_classifier.data import dataset_fingerprint
from shape_classifier.benchmark import excluded_times


class MeasurementTests(unittest.TestCase):
    def test_excludes_first_epoch(self):
        self.assertEqual(excluded_times([4.0]), (None, None))
        self.assertEqual(excluded_times([4.0, 2.0, 4.0]), (6.0, 3.0))

    def test_fingerprint_uses_path_and_content(self):
        with tempfile.TemporaryDirectory() as root:
            p = Path(root) / 'train/circle/a.png'
            p.parent.mkdir(parents=True)
            p.write_bytes(b'a')
            before = dataset_fingerprint(root)
            p.write_bytes(b'b')
            self.assertNotEqual(before, dataset_fingerprint(root))
            upper = p.with_name('B.PNG')
            upper.write_bytes(b'c')
            with_upper = dataset_fingerprint(root)
            upper.write_bytes(b'd')
            self.assertNotEqual(with_upper, dataset_fingerprint(root))

    def test_cpu_thread_detection_returns_positive_count(self):
        from shape_classifier.device import available_cpus
        self.assertGreater(available_cpus(), 0)

    def test_training_synchronizes_mps_and_excludes_warmup(self):
        from unittest.mock import patch
        import torch
        from shape_classifier.train import train
        class TinyDataset(torch.utils.data.Dataset):
            def __init__(self, root, split): self.split = split
            def __len__(self): return 2
            def __getitem__(self, index): return torch.tensor([float(index)]), index
        captured = []
        with tempfile.TemporaryDirectory() as root, \
             patch('shape_classifier.train.ShapeDataset', TinyDataset), \
             patch('shape_classifier.train.ShapeClassifier', lambda: torch.nn.Linear(1, 2)), \
             patch('shape_classifier.train.augment', lambda image: image), \
             patch('shape_classifier.train.dataset_fingerprint', return_value='hash'), \
             patch('shape_classifier.train.available_cpus', return_value=1), \
             patch('shape_classifier.train.publish', side_effect=lambda root, checkpoint, write, entry: captured.append(entry)), \
             patch('shape_classifier.train.recover_checkpoint'), \
             patch('shape_classifier.train.torch.mps.synchronize') as sync, \
             patch.object(torch.nn.Module, 'to', lambda self, *a, **k: self), \
             patch.object(torch.Tensor, 'to', lambda self, *a, **k: self):
            results = train(root, Path(root) / 'model.pth', epochs=2, batch_size=2, device='mps', environment='native')
        self.assertEqual(sync.call_count, 6)
        self.assertEqual([total for _, total in results], [2, 2])
        self.assertIsNotNone(captured[0]['epoch_seconds'])
        self.assertEqual(captured[0]['cpu_threads'], 1)
        self.assertGreaterEqual(captured[0]['inference_seconds'], 0)

    def test_docker_resources_reports_known_vm_values_and_respects_limits(self):
        from unittest.mock import patch
        from shape_classifier.device import docker_resources
        def files(path, *args, **kwargs):
            values = {'/proc/meminfo': 'MemTotal:       2097152 kB\n', '/sys/fs/cgroup/memory.max': 'max\n'}
            if str(path) not in values: raise FileNotFoundError(str(path))
            return values[str(path)]
        with patch('pathlib.Path.read_text', files), patch('shape_classifier.device.available_cpus', return_value=4), patch('shape_classifier.device.os.cpu_count', return_value=4):
            self.assertEqual(docker_resources('docker'), (4, 2097152 * 1024))
            self.assertEqual(docker_resources('native'), (None, None))
        def limited(path, *args, **kwargs):
            if str(path) == '/sys/fs/cgroup/memory.max': return '1048576\n'
            return files(path, *args, **kwargs)
        with patch('pathlib.Path.read_text', limited), patch('shape_classifier.device.available_cpus', return_value=2), patch('shape_classifier.device.os.cpu_count', return_value=4):
            self.assertEqual(docker_resources('docker'), ('unknown', 'unknown'))
