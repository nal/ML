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
