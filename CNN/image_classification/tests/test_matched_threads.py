import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from shape_classifier.__main__ import main


class ThreadOptionTests(unittest.TestCase):
    def test_invalid_requests_do_not_touch_files_or_start_training(self):
        with tempfile.TemporaryDirectory() as root:
            checkpoint = Path(root) / 'model.pth'
            results = Path(root) / 'benchmark-results.json'
            journal = Path(root) / '.benchmark-transaction.json'
            checkpoint.write_bytes(b'checkpoint')
            results.write_bytes(b'results')
            journal.write_bytes(b'recovery')
            with patch('shape_classifier.__main__.available_cpus', return_value=2), \
                 patch('shape_classifier.__main__.train') as training:
                for count in ('0', '-1', 'abc', '3'):
                    with self.subTest(count=count), contextlib.redirect_stderr(io.StringIO()) as stderr:
                        try:
                            result = main(['train', '--device', 'cpu', '--data-dir', root,
                                           '--checkpoint', str(checkpoint), '--cpu-threads', count])
                        except SystemExit as exc:
                            result = exc.code
                        self.assertNotEqual(result, 0)
                        if count == '3':
                            self.assertIn('3', stderr.getvalue())
                            self.assertIn('2', stderr.getvalue())
                    training.assert_not_called()
                    self.assertEqual(checkpoint.read_bytes(), b'checkpoint')
                    self.assertEqual(results.read_bytes(), b'results')
                    self.assertEqual(journal.read_bytes(), b'recovery')

    def test_request_reaches_training(self):
        with patch('shape_classifier.__main__.available_cpus', return_value=8), \
             patch('shape_classifier.__main__.resolve_device', return_value=('native', 'cpu')), \
             patch('shape_classifier.__main__.train', return_value=[(1, 1), (1, 1)]) as training, \
             contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(['train', '--cpu-threads', '4']), 0)
            self.assertEqual(training.call_args.kwargs['cpu_threads'], 4)

    def test_other_commands_do_not_accept_thread_option(self):
        for command, extra in (('evaluate', []), ('predict', ['image.png'])):
            with self.subTest(command=command), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    main([command, *extra, '--cpu-threads', '1'])
                self.assertNotEqual(error.exception.code, 0)

    def test_observation_validation(self):
        import json
        from shape_classifier.device import docker_resources
        good = dict(version=1, cpus=8, profile='default', docker_endpoint='unix:///tmp/docker.sock')
        for value, expected in ((good, 8), (dict(good, cpus=True), 'unknown'),
                                (dict(good, version=2), 'unknown'),
                                (dict(good, docker_endpoint='tcp://host'), 'unknown'),
                                (dict(good, docker_endpoint='unix:///tmp/../bad.sock'), 'unknown')):
            with self.subTest(value=value), patch.dict('os.environ', {'SHAPE_COLIMA_OBSERVATION': json.dumps(value)}):
                self.assertEqual(docker_resources('docker')[0], expected)

    def test_summary_separates_resources_and_provenance(self):
        import json
        from shape_classifier.benchmark import format_summary, read_results, validate_entry
        base = dict(run_id='a', timestamp='2026-01-01T00:00:00Z', environment='docker', device='cpu',
                    python_version='3.14.10', pytorch_version='2', data_id='data', epochs=2,
                    batch_size=8, cpu_threads=2, seed=42, train_correct=1, train_total=2,
                    held_out_correct=1, held_out_total=2, training_seconds=2, epoch_seconds=2,
                    inference_seconds=0.1, loss=1.0, docker_cpus=8, docker_memory='unknown')
        output = format_summary([base, dict(base, run_id='b', docker_cpu_provenance='launcher'),
                                 dict(base, run_id='c', cpu_threads=4)])
        self.assertEqual(sum(line.startswith('docker') for line in output.splitlines()), 3)
        self.assertIn('legacy-unverified', output)
        self.assertIn('launcher', output)
        mixed_output = format_summary([
            dict(base, docker_cpu_provenance='launcher', requested_cpu_threads=2),
            dict(base, run_id='default', docker_cpu_provenance='launcher', requested_cpu_threads=None),
            dict(base, run_id='unknown', docker_cpus='unknown', docker_cpu_provenance='unknown'),
        ])
        self.assertIn('mixed', mixed_output)
        self.assertIn('unknown', mixed_output)
        self.assertIn('not yet measured', mixed_output)
        gpu = dict(base, environment='native', device='mps', docker_cpus=None, docker_memory=None,
                   inference_seconds=0.321)
        gpu_output = format_summary([gpu])
        self.assertIn('whole GPU', gpu_output)
        self.assertIn('0.321000', gpu_output)
        with self.assertRaises(ValueError):
            validate_entry(dict(base, docker_cpu_provenance='unknown'))

        for entry in (dict(base, docker_cpu_provenance='other'),
                      dict(base, docker_cpus='unknown', docker_cpu_provenance='launcher'),
                      dict(base, requested_cpu_threads=0),
                      dict(base, requested_cpu_threads=4)):
            with self.subTest(entry=entry), self.assertRaises(ValueError):
                validate_entry(entry)
        validate_entry(base)
        validate_entry(dict(base, docker_cpu_provenance='launcher', requested_cpu_threads=2))
        validate_entry(dict(base, docker_cpus='unknown', docker_cpu_provenance='unknown'))
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'results.json'
            raw = json.dumps({'version': 1, 'entries': [base, dict(base, run_id='new',
                              docker_cpu_provenance='launcher', requested_cpu_threads=2)]})
            path.write_text(raw)
            output = format_summary(read_results(path))
            self.assertIn('legacy-unverified', output)
            self.assertIn('launcher', output)
            self.assertEqual(path.read_text(), raw)

    def test_docker_warning_for_unknown_and_mismatch(self):
        import torch
        from shape_classifier.train import train

        class StopTraining(Exception): pass
        for allocation, warning in (('unknown', 'could not be verified'), (8, 'not core-matched'), (4, None)):
            with self.subTest(allocation=allocation), \
                 patch('shape_classifier.train.available_cpus', return_value=8), \
                 patch('shape_classifier.train.docker_resources', return_value=(allocation, 'unknown')), \
                 patch('shape_classifier.train.ShapeDataset', side_effect=StopTraining), \
                 contextlib.redirect_stderr(io.StringIO()) as stderr:
                with self.assertRaises(StopTraining):
                    train('/unused', '/unused/checkpoint', cpu_threads=4)
                if warning:
                    self.assertIn(warning, stderr.getvalue())
                else:
                    self.assertNotIn('Warning', stderr.getvalue())

    def test_training_records_configured_count_and_default(self):
        import torch
        from shape_classifier.train import train

        class TinyDataset(torch.utils.data.Dataset):
            def __init__(self, *args): pass
            def __len__(self): return 2
            def __getitem__(self, index): return torch.tensor([float(index)]), index

        entries = []
        with tempfile.TemporaryDirectory() as root, \
             patch('shape_classifier.train.ShapeDataset', TinyDataset), \
             patch('shape_classifier.train.ShapeClassifier', lambda: torch.nn.Linear(1, 2)), \
             patch('shape_classifier.train.augment', lambda image: image), \
             patch('shape_classifier.train.dataset_fingerprint', return_value='hash'), \
             patch('shape_classifier.train.available_cpus', return_value=2), \
             patch('shape_classifier.train.recover_checkpoint'), \
             patch('shape_classifier.train.publish', side_effect=lambda *args: entries.append(args[-1])), \
             contextlib.redirect_stderr(io.StringIO()):
            for count in (1, None):
                train(root, Path(root) / 'model.pth', epochs=1, batch_size=2,
                      environment='native', cpu_threads=count)
        self.assertEqual([(e['requested_cpu_threads'], e['cpu_threads']) for e in entries],
                         [(1, 1), (None, 2)])


if __name__ == '__main__':
    unittest.main()
