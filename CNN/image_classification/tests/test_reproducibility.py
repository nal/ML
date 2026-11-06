import unittest
from shape_dataset.generate import generate

class ReproducibilityTests(unittest.TestCase):
    def test_seed_independence(self):
        a=generate(42,43); b=generate(42,43); c=generate(44,43); d=generate(42,45)
        self.assertEqual(a,b)
        self.assertTrue(all(a[k]==c[k] for k in a if k.startswith('held-out/')))
        self.assertTrue(all(a[k]==d[k] for k in a if k.startswith('train/')))
        self.assertTrue(any(a[k]!=c[k] for k in a if k.startswith('train/')))
        self.assertTrue(any(a[k]!=d[k] for k in a if k.startswith('held-out/')))
    def test_invalid_cli_seeds(self):
        import subprocess, sys
        for args in (['--train-seed','1','--held-out-seed','1'], ['--train-seed','bad']):
            result=subprocess.run([sys.executable,'-m','shape_dataset',*args],capture_output=True)
            self.assertNotEqual(result.returncode,0)
