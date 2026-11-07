#!/bin/sh
# Host-side launcher: observe Colima without changing its configuration.
exec python3 - "$@" <<'PY'
import json
import os
from pathlib import Path
import subprocess
import sys

env = os.environ.copy()
env.pop('SHAPE_COLIMA_OBSERVATION', None)
profile = env.get('COLIMA_PROFILE', 'default')
try:
    status = json.loads(subprocess.check_output(
        ['colima', 'status', profile, '--json'], text=True, stderr=subprocess.DEVNULL,
        timeout=20))
    socket = status['docker_socket']
    if not isinstance(socket, str) or not socket:
        raise ValueError('no Colima Docker socket')
    colima_endpoint = 'unix://' + str(Path(socket.removeprefix('unix://')).resolve())
    if env.get('DOCKER_HOST'):
        context = None
    elif env.get('DOCKER_CONTEXT'):
        context = env['DOCKER_CONTEXT']
    else:
        context = subprocess.check_output(['docker', 'context', 'show'], text=True, timeout=10).strip()
    endpoint = (subprocess.check_output(['docker', 'context', 'inspect', context, '--format',
                '{{.Endpoints.docker.Host}}'], text=True, timeout=10).strip()
                if context else env['DOCKER_HOST'])
    if not endpoint.startswith('unix:///'):
        raise ValueError('Docker endpoint is not a Unix socket')
    endpoint = 'unix://' + str(Path(endpoint.removeprefix('unix://')).resolve())
    cpus = status['cpu']
    if endpoint != colima_endpoint or type(cpus) is not int or cpus <= 0:
        raise ValueError('Docker endpoint or CPU allocation could not be verified')
    env['SHAPE_COLIMA_OBSERVATION'] = json.dumps(dict(version=1, cpus=cpus, profile=profile,
                                                       docker_endpoint=endpoint))
except (OSError, KeyError, TypeError, ValueError, subprocess.SubprocessError):
    print('Warning: Colima VM allocation could not be verified.', file=sys.stderr)

args = ['docker', 'run', '--rm', '-v', f'{Path.cwd() / "data"}:/data']
if 'SHAPE_COLIMA_OBSERVATION' in env:
    args += ['-e', 'SHAPE_COLIMA_OBSERVATION']
args += ['--entrypoint', 'python', env.get('SHAPE_CLASSIFIER_IMAGE', 'shape-classifier'),
         '-m', 'shape_classifier', 'train', *sys.argv[1:]]
os.execvpe('docker', args, env)
PY
