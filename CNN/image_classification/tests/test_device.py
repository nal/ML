"""Device selection and CLI startup behavior."""
import contextlib
import io
import unittest
from unittest.mock import patch

from shape_classifier.device import resolve_device
from shape_classifier.__main__ import main


class DeviceTests(unittest.TestCase):
    def test_resolution(self):
        with patch('shape_classifier.device.in_docker', return_value=True), patch('shape_classifier.device.mps_usable', return_value=True):
            self.assertEqual(resolve_device('auto'), ('docker', 'cpu'))
            self.assertEqual(resolve_device('cpu'), ('docker', 'cpu'))
            with self.assertRaisesRegex(ValueError, 'MPS.*unavailable'):
                resolve_device('mps')
        with patch('shape_classifier.device.in_docker', return_value=False):
            with patch('shape_classifier.device.mps_usable', return_value=True):
                self.assertEqual(resolve_device('auto'), ('native', 'mps'))
            with patch('shape_classifier.device.mps_usable', return_value=False):
                self.assertEqual(resolve_device('auto'), ('native', 'cpu'))
                with self.assertRaisesRegex(ValueError, 'MPS.*unavailable'):
                    resolve_device('mps')

    def test_unavailable_device_fails_before_work(self):
        with patch('shape_classifier.device.in_docker', return_value=True), patch('shape_classifier.__main__.train') as train:
            with contextlib.redirect_stderr(io.StringIO()) as out:
                self.assertEqual(main(['train', '--device', 'mps']), 1)
            self.assertIn('unavailable', out.getvalue())
            train.assert_not_called()

    def test_default_reports_resolved_context(self):
        with patch('shape_classifier.device.in_docker', return_value=True), patch('shape_classifier.__main__.train', return_value=[(1, 30), (1, 15)]):
            with contextlib.redirect_stderr(io.StringIO()) as out:
                self.assertEqual(main(['train']), 0)
            self.assertIn('docker', out.getvalue())
            self.assertIn('cpu', out.getvalue())
            self.assertIn('Python', out.getvalue())
            self.assertIn('PyTorch', out.getvalue())
