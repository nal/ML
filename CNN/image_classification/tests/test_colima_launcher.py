import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class LauncherTests(unittest.TestCase):
    def test_matching_and_mismatched_endpoint(self):
        script = Path(__file__).resolve().parents[1] / 'scripts/matched-core-docker.sh'
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            colima = root / 'colima'
            colima.write_text('#!/bin/sh\nprintf "%s\\n" "{\\"cpu\\":8,\\"docker_socket\\":\\"unix:///tmp/colima.sock\\"}"\n')
            docker = root / 'docker'
            docker.write_text('#!/bin/sh\nif [ "$1" = run ]; then env | grep "^SHAPE_COLIMA_OBSERVATION=" || true; fi\n')
            colima.chmod(0o755)
            docker.chmod(0o755)
            env = dict(os.environ, PATH=f'{root}:{os.environ["PATH"]}', DOCKER_HOST='unix:///tmp/colima.sock',
                       SHAPE_COLIMA_OBSERVATION='inherited')
            env.pop('DOCKER_CONTEXT', None)
            result = subprocess.run([str(script), '--cpu-threads', '8'], env=env, text=True, capture_output=True, check=True)
            observation = json.loads(result.stdout.strip().split('=', 1)[1])
            self.assertEqual(observation['cpus'], 8)
            self.assertEqual(observation['version'], 1)
            env['DOCKER_HOST'] = 'unix:///tmp/other.sock'
            result = subprocess.run([str(script)], env=env, text=True, capture_output=True, check=True)
            self.assertNotIn('SHAPE_COLIMA_OBSERVATION=', result.stdout)
            self.assertIn('could not be verified', result.stderr)
            env['DOCKER_HOST'] = 'unix:///tmp/colima.sock'
            for body in ('not-json', '{"cpu":0,"docker_socket":"unix:///tmp/colima.sock"}'):
                colima.write_text('#!/bin/sh\nprintf "%s\\n" ' + "'" + body + "'" + '\n')
                result = subprocess.run([str(script)], env=env, text=True, capture_output=True, check=True)
                self.assertNotIn('SHAPE_COLIMA_OBSERVATION=', result.stdout)
                self.assertIn('could not be verified', result.stderr)
            colima.write_text('#!/bin/sh\nexit 1\n')
            result = subprocess.run([str(script)], env=env, text=True, capture_output=True, check=True)
            self.assertNotIn('SHAPE_COLIMA_OBSERVATION=', result.stdout)
            colima.write_text('#!/bin/sh\nprintf "%s\\n" \'{"cpu":8,"docker_socket":"unix:///tmp/colima.sock"}\'\n')
            docker.write_text('#!/bin/sh\nif [ "$1" = context ]; then printf "%s\\n" "unix:///tmp/other.sock"; else env | grep "^SHAPE_COLIMA_OBSERVATION=" || true; fi\n')
            env['DOCKER_CONTEXT'] = 'other'
            env.pop('DOCKER_HOST', None)
            result = subprocess.run([str(script)], env=env, text=True, capture_output=True, check=True)
            self.assertNotIn('SHAPE_COLIMA_OBSERVATION=', result.stdout)
            self.assertIn('could not be verified', result.stderr)

            docker.write_text('#!/bin/sh\nif [ "$1" = context ]; then printf "%s\\n" "unix:///tmp/colima.sock"; else env | grep "^SHAPE_COLIMA_OBSERVATION=" || true; fi\n')
            env['DOCKER_CONTEXT'] = 'colima'
            env['DOCKER_HOST'] = 'unix:///tmp/other.sock'
            result = subprocess.run([str(script)], env=env, text=True, capture_output=True, check=True)
            self.assertNotIn('SHAPE_COLIMA_OBSERVATION=', result.stdout)
            self.assertIn('could not be verified', result.stderr)
