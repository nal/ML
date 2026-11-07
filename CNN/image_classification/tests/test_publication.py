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

    def test_interrupted_before_commit_restores_old_checkpoint(self):
        import json
        from shape_classifier.publication import recover_checkpoint
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            nested = root / 'nested'
            nested.mkdir()
            checkpoint = nested / 'model.pth'
            checkpoint.write_bytes(b'new')
            (nested / 'backup').write_bytes(b'old')
            journal = root / '.benchmark-transaction.json'
            journal.write_text(json.dumps({'run_id': 'run', 'checkpoint': 'nested/model.pth', 'backup': 'backup'}))
            Path(str(checkpoint) + '.transaction').write_text(json.dumps({'journal': '../.benchmark-transaction.json'}))
            recover_checkpoint(checkpoint)
            self.assertEqual(checkpoint.read_bytes(), b'old')
            self.assertFalse(journal.exists())

    def test_missing_recovery_journal_does_not_discard_sidecar(self):
        import json
        from shape_classifier.publication import recover_checkpoint
        with tempfile.TemporaryDirectory() as name:
            checkpoint = Path(name) / 'model.pth'
            sidecar = Path(str(checkpoint) + '.transaction')
            sidecar.write_text(json.dumps({'journal': 'missing/journal'}))
            with self.assertRaises((RuntimeError, OSError)):
                recover_checkpoint(checkpoint)
            self.assertTrue(sidecar.exists())

    def test_after_commit_recovery_keeps_new_checkpoint(self):
        import json
        from shape_classifier.publication import recover_checkpoint
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            checkpoint = root / 'model.pth'
            checkpoint.write_bytes(b'new')
            (root / 'backup').write_bytes(b'old')
            entry = dict(run_id='run', timestamp='2026-01-01T00:00:00Z', environment='native', device='cpu', python_version='3.14.10', pytorch_version='2.15.0', data_id='abc', epochs=1, batch_size=8, cpu_threads=1, seed=42, train_correct=1, train_total=2, held_out_correct=1, held_out_total=2, training_seconds=None, epoch_seconds=None, inference_seconds=0.1, loss=1.0, docker_cpus=None, docker_memory=None)
            (root / 'benchmark-results.json').write_text(json.dumps({'version': 1, 'entries': [entry]}))
            journal = root / '.benchmark-transaction.json'
            journal.write_text(json.dumps({'run_id': 'run', 'checkpoint': 'model.pth', 'backup': 'backup'}))
            Path(str(checkpoint) + '.transaction').write_text(json.dumps({'journal': journal.name}))
            recover_checkpoint(checkpoint)
            self.assertEqual(checkpoint.read_bytes(), b'new')
            self.assertFalse(journal.exists())

    def test_failed_write_removes_new_checkpoint(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            checkpoint = root / 'model.pth'
            entry = dict(run_id='run', timestamp='2026-01-01T00:00:00Z', environment='native', device='cpu', python_version='3.14.10', pytorch_version='2.15.0', data_id='abc', epochs=1, batch_size=8, cpu_threads=1, seed=42, train_correct=1, train_total=2, held_out_correct=1, held_out_total=2, training_seconds=None, epoch_seconds=None, inference_seconds=0.1, loss=1.0, docker_cpus=None, docker_memory=None)
            with patch('shape_classifier.publication._commit_results', side_effect=OSError('failed')):
                with self.assertRaises(OSError):
                    publish(root, checkpoint, lambda p: p.write_bytes(b'new'), entry)
            self.assertFalse(checkpoint.exists())

    def test_process_interruption_before_and_after_commit(self):
        import os
        import subprocess
        import sys
        from shape_classifier.publication import recover_checkpoint
        for committed in (False, True):
            with self.subTest(committed=committed), tempfile.TemporaryDirectory() as name:
                root = Path(name)
                checkpoint = root / 'model.pth'
                checkpoint.write_bytes(b'old')
                script = '''
import os, sys
from pathlib import Path
import shape_classifier.publication as p
root = Path(sys.argv[1]); checkpoint = root / 'model.pth'
e = dict(run_id='run', timestamp='2026-01-01T00:00:00Z', environment='native', device='cpu', python_version='3.14.10', pytorch_version='2.15.0', data_id='abc', epochs=1, batch_size=8, cpu_threads=1, seed=42, train_correct=1, train_total=2, held_out_correct=1, held_out_total=2, training_seconds=None, epoch_seconds=None, inference_seconds=0.1, loss=1.0, docker_cpus=None, docker_memory=None)
if sys.argv[2] == 'before': p._commit_results = lambda *args: os._exit(73)
else: p._recover = lambda *args: os._exit(73)
p.publish(root, checkpoint, lambda path: path.write_bytes(b'new'), e)
'''
                proc = subprocess.run([sys.executable, '-c', script, name, 'after' if committed else 'before'], env=os.environ.copy())
                self.assertEqual(proc.returncode, 73)
                recover_checkpoint(checkpoint)
                self.assertEqual(checkpoint.read_bytes(), b'new' if committed else b'old')
                self.assertEqual((root / 'benchmark-results.json').exists(), committed)

    def test_prediction_recovers_nested_checkpoint_without_data_directory(self):
        import json
        from PIL import Image
        from shape_classifier.checkpoint import save_checkpoint
        from shape_classifier.model import ShapeClassifier
        from shape_classifier.predict import predict
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            nested = root / 'nested'
            nested.mkdir()
            checkpoint = nested / 'model.pth'
            save_checkpoint(checkpoint, ShapeClassifier(), 42, None, None)
            backup = nested / 'backup'
            backup.write_bytes(checkpoint.read_bytes())
            checkpoint.write_bytes(b'interrupted')
            journal = root / '.benchmark-transaction.json'
            journal.write_text(json.dumps({'run_id': 'run', 'checkpoint': 'nested/model.pth', 'backup': 'backup'}))
            Path(str(checkpoint) + '.transaction').write_text(json.dumps({'journal': '../.benchmark-transaction.json'}))
            image = root / 'image.png'
            Image.new('RGB', (8, 8)).save(image)
            self.assertIn(predict(image, checkpoint), ('circle', 'rectangle', 'triangle'))
            self.assertFalse(journal.exists())

    @unittest.skipUnless(__import__('os').environ.get('SHAPE_CROSS_ENV') == '1', 'requires Docker and native shared mount')
    def test_cross_environment_interruption_and_nested_prediction(self):
        import os
        import subprocess
        import sys
        from PIL import Image
        from shape_classifier.checkpoint import save_checkpoint
        from shape_classifier.model import ShapeClassifier
        project = Path(__file__).resolve().parents[1]
        data = project / 'data'
        data.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='recovery-', dir=data) as name:
            root = Path(name)
            (root / 'nested').mkdir()
            checkpoint = root / 'nested/model.pth'
            image = root / 'image.png'
            Image.new('RGB', (8, 8)).save(image)
            script = '''
import os, sys
from pathlib import Path
import shape_classifier.publication as p
root = Path(sys.argv[1]); checkpoint = root / 'nested/model.pth'
e = dict(run_id='run', timestamp='2026-01-01T00:00:00Z', environment='native', device='cpu', python_version='3.14.10', pytorch_version='2.15.0', data_id='abc', epochs=1, batch_size=8, cpu_threads=1, seed=42, train_correct=1, train_total=2, held_out_correct=1, held_out_total=2, training_seconds=None, epoch_seconds=None, inference_seconds=0.1, loss=1.0, docker_cpus=None, docker_memory=None)
p._commit_results = lambda *args: os._exit(73)
p.publish(root, checkpoint, lambda path: path.write_bytes(b'new'), e)
'''
            docker = ['docker', 'run', '--rm', '-v', str(root) + ':/data', '--entrypoint', 'python', 'shape-classifier']
            native_env = dict(os.environ, PYTHONPATH=str(project / 'src'))
            for crash_in_docker in (True, False):
                save_checkpoint(checkpoint, ShapeClassifier(), 42, None, None)
                if crash_in_docker:
                    crash = subprocess.run(docker + ['-c', script, '/data'])
                    self.assertEqual(crash.returncode, 73)
                    recover = subprocess.run([sys.executable, '-m', 'shape_classifier', 'predict', str(image), '--checkpoint', str(checkpoint), '--device', 'cpu'], env=native_env, capture_output=True, text=True)
                else:
                    crash = subprocess.run([sys.executable, '-c', script, str(root)], env=native_env)
                    self.assertEqual(crash.returncode, 73)
                    recover = subprocess.run(docker + ['-m', 'shape_classifier', 'predict', '/data/image.png', '--checkpoint', '/data/nested/model.pth', '--device', 'cpu'], capture_output=True, text=True)
                self.assertEqual(recover.returncode, 0, recover.stderr)
                self.assertIn(recover.stdout.strip(), ('circle', 'rectangle', 'triangle'))
                self.assertFalse((root / '.benchmark-transaction.json').exists())

    def test_committed_journal_with_inaccessible_external_checkpoint_is_preserved(self):
        import json
        from shape_classifier.publication import recover_results
        entry = dict(run_id='run', timestamp='2026-01-01T00:00:00Z', environment='native', device='cpu', python_version='3.14.10', pytorch_version='2.15.0', data_id='abc', epochs=1, batch_size=8, cpu_threads=1, seed=42, train_correct=1, train_total=2, held_out_correct=1, held_out_total=2, training_seconds=None, epoch_seconds=None, inference_seconds=0.1, loss=1.0, docker_cpus=None, docker_memory=None)
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            journal = root / '.benchmark-transaction.json'
            journal.write_text(json.dumps({'run_id': 'run', 'checkpoint': '/nonexistent-device-benchmark/model.pth', 'backup': None}))
            (root / 'benchmark-results.json').write_text(json.dumps({'version': 1, 'entries': [entry]}))
            with self.assertRaisesRegex(RuntimeError, 'checkpoint'):
                recover_results(root)
            self.assertTrue(journal.exists())

    def test_inaccessible_external_checkpoint_preserves_journal_and_sidecar(self):
        import json
        from shape_classifier.publication import recover_results
        with tempfile.TemporaryDirectory() as name:
            root = Path(name) / 'results'
            external = Path(name) / 'external'
            root.mkdir()
            external.mkdir()
            checkpoint = external / 'model.pth'
            sidecar = Path(str(checkpoint) + '.transaction')
            sidecar.write_text(json.dumps({'journal': '../results/.benchmark-transaction.json'}))
            journal = root / '.benchmark-transaction.json'
            journal.write_text(json.dumps({'run_id': 'run', 'checkpoint': '../external/model.pth', 'backup': None}))
            original = Path.is_dir
            with patch.object(Path, 'is_dir', lambda p: False if p == external.resolve() else original(p)):
                with self.assertRaisesRegex(RuntimeError, 'checkpoint directory is unavailable'):
                    recover_results(root)
            self.assertTrue(journal.exists())
            self.assertTrue(sidecar.exists())
