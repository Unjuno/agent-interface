"""Prospective, byte-retaining host/container launch for finite formal runs."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def write_new(path, blob):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(blob)


def write_json_new(path, value):
    write_new(path, (json.dumps(value, sort_keys=True) + '\n').encode('utf-8'))


def host_plan_ready(root, expected_blob):
    """Accept readiness only after the host's sealed plan matches exact bytes."""
    directory = Path(root) / 'host' / 'host-plan'
    try:
        marker_blob = (directory / 'ready.json').read_bytes()
        marker = json.loads(marker_blob)
        payload = (directory / 'payload.bin').read_bytes()
    except (OSError, ValueError, TypeError):
        return False
    return (type(marker) is dict and set(marker) == {'bytes', 'sha256'}
        and type(marker.get('bytes')) is int and marker['bytes'] == len(payload)
        and marker.get('sha256') == digest(payload) and payload == expected_blob)


def start_capture(argv, cwd, directory):
    """Publish an immutable argv/time receipt before starting exactly once."""
    directory, cwd = Path(directory), Path(cwd)
    if directory.exists():
        raise ValueError('LAUNCH_EVIDENCE_EXISTS')
    directory.mkdir(parents=True, exist_ok=False)
    if type(argv) is not list or not argv or any(type(value) is not str for value in argv):
        raise ValueError('LAUNCH_ARGV_INVALID')
    attempt = dict(argv=argv, started_utc=utc_now())
    write_json_new(directory / 'attempt.json', attempt)
    stdout_path, stderr_path = directory / 'stdout.bin', directory / 'stderr.bin'
    started = time.monotonic()
    launch_error = None
    try:
        with stdout_path.open('xb') as stdout, stderr_path.open('xb') as stderr:
            process = subprocess.Popen(argv, cwd=str(cwd), stdin=subprocess.DEVNULL,
                stdout=stdout, stderr=stderr, shell=False)
    except OSError as exception:
        launch_error = type(exception).__name__ + ':' + str(exception)
        process = None
        for path in (stdout_path, stderr_path):
            if not path.exists():
                write_new(path, b'')
    return dict(argv=argv, cwd=cwd, directory=directory, attempt=attempt,
        process=process, started=started, launch_error=launch_error,
        stdout_path=stdout_path, stderr_path=stderr_path)


def finish_capture(capture, *, timeout_seconds):
    process = capture['process']
    timed_out = False
    exit_code = None
    if process is not None:
        try:
            exit_code = process.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.terminate()
            try:
                exit_code = process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                exit_code = process.wait()
    stdout = capture['stdout_path'].read_bytes()
    stderr = capture['stderr_path'].read_bytes()
    finished = utc_now()
    receipt = dict(capture['attempt'], exit_code=exit_code,
        finished_utc=finished, launch_error=capture['launch_error'],
        output_sha256={'attempt.json': digest((capture['directory'] / 'attempt.json').read_bytes()),
                       'stdout.bin': digest(stdout), 'stderr.bin': digest(stderr)},
        timed_out=timed_out,
        wall_seconds=max(0.0, time.monotonic() - capture['started']))
    write_json_new(capture['directory'] / 'receipt.json', receipt)
    return receipt


def validate_outer_plan(path):
    path = Path(path)
    config = json.loads(path.read_bytes())
    required = {'schema', 'root', 'source_root', 'plan_sha256', 'host_plan_sha256',
        'launcher_sha256', 'python_executable', 'host_script', 'host_argv',
        'host_timeout_seconds', 'candidate_output', 'candidate_argv',
        'candidate_timeout_seconds', 'host_ready_timeout_seconds',
        'codex_executable', 'codex_sha256', 'container_image_digest',
        'response_schema_sha256'}
    if type(config) is not dict or set(config) != required or config['schema'] != 'a15-formal-outer-launch-v1':
        raise ValueError('OUTER_PLAN_SCHEMA')
    root, source_root = Path(config['root']), Path(config['source_root'])
    if digest((root / 'plan.json').read_bytes()) != config['plan_sha256']:
        raise ValueError('OUTER_PLAN_FROZEN_PLAN_MISMATCH')
    if digest((root / 'host-plan.json').read_bytes()) != config['host_plan_sha256']:
        raise ValueError('OUTER_PLAN_HOST_PLAN_MISMATCH')
    if digest(Path(__file__).read_bytes()) != config['launcher_sha256']:
        raise ValueError('OUTER_PLAN_LAUNCHER_CHANGED')
    plan = json.loads((root / 'plan.json').read_bytes())
    host_plan = json.loads((root / 'host-plan.json').read_bytes())
    if (host_plan.get('allocation') != plan.get('allocation')
        or host_plan.get('freeze_sha256') != config['plan_sha256']):
        raise ValueError('OUTER_PLAN_ALLOCATION_JOIN')
    if plan.get('formal_allocation') is True:
        if not (root / 'response.schema.json').is_file():
            raise ValueError('FORMAL_ROOT_SCHEMA_MISSING')
        if digest((root / 'response.schema.json').read_bytes()) != config.get('response_schema_sha256'):
            raise ValueError('FORMAL_ROOT_SCHEMA_CHANGED')
        model = plan.get('model')
        if type(model) is not dict or not model.get('name') or not model.get('effort'):
            raise ValueError('FORMAL_REQUESTED_MODEL_MISSING')
        sources = plan.get('source_sha256')
        if type(sources) is not dict or not sources:
            raise ValueError('FORMAL_SOURCE_CLOSURE_MISSING')
        for logical, expected in sources.items():
            if type(logical) is not str or not logical.startswith('/src/'):
                raise ValueError('FORMAL_SOURCE_PATH_INVALID')
            relative = Path(*logical.removeprefix('/src/').split('/'))
            source, capsule = source_root / relative, root / 'source-capsule' / relative
            if not source.is_file() or digest(source.read_bytes()) != expected:
                raise ValueError('FORMAL_SOURCE_CHANGED:' + logical)
            if not capsule.is_file() or digest(capsule.read_bytes()) != expected:
                raise ValueError('FORMAL_SOURCE_CAPSULE_CHANGED:' + logical)
        launcher_key = next((key for key in sources if key.endswith('/formal_launch.py')), None)
        host_key = next((key for key in sources if key.endswith('/file_exchange.py')), None)
        if launcher_key is None or sources[launcher_key] != config['launcher_sha256']:
            raise ValueError('FORMAL_LAUNCHER_NOT_FROZEN')
        if host_key is None or digest(Path(config['host_script']).read_bytes()) != sources[host_key]:
            raise ValueError('FORMAL_HOST_SCRIPT_NOT_FROZEN')
        schema_path = root / 'response.schema.json'
        codex = Path(config.get('codex_executable', ''))
        if not codex.is_file() or digest(codex.read_bytes()) != config.get('codex_sha256'):
            raise ValueError('FORMAL_CODEX_EXECUTABLE_CHANGED')
        if (host_plan.get('executable_sha256') != config['codex_sha256']
            or len(host_plan.get('plans', {})) != 2 * len(plan.get('rows', []))
            or Path(config['candidate_output']) != root / 'candidate'):
            raise ValueError('FORMAL_HOST_PLAN_EXECUTABLE_OR_SLOT_JOIN')
        expected_slots = {row['id'] + '-' + kind for row in plan['rows']
                          for kind in ('first', 'recovery')}
        if set(host_plan['plans']) != expected_slots:
            raise ValueError('FORMAL_HOST_SLOT_SET')
        for slot, frozen in host_plan['plans'].items():
            argv = frozen.get('argv', [])
            if (not argv or Path(argv[0]) != codex
                or argv.count('--model') != 1
                or argv[argv.index('--model')+1] != model['name']
                or argv.count('--config') != 1
                or argv[argv.index('--config')+1] != 'model_reasoning_effort="' + model['effort'] + '"'
                or argv.count('--output-schema') != 1
                or Path(argv[argv.index('--output-schema')+1]) != schema_path
                or frozen.get('schema_sha256') != config['response_schema_sha256']
                or argv.count('--image') != 1
                or Path(argv[argv.index('--image')+1]) != root / 'exchange' / slot / 'image' / 'payload.png'
                or argv.count('--cd') != 1
                or not Path(argv[argv.index('--cd')+1]).is_dir()):
                raise ValueError('FORMAL_HOST_SLOT_BINDING:' + slot)
        candidate = config['candidate_argv']
        image_digest = config.get('container_image_digest', '')
        if (Path(candidate[0]).name.casefold() != 'wslc.exe'
            or candidate.count('--network') != 1 or candidate[candidate.index('--network')+1] != 'none'
            or candidate.count('--pull') != 1 or candidate[candidate.index('--pull')+1] != 'never'
            or len(image_digest) != 64 or any(char not in '0123456789abcdef' for char in image_digest)
            or candidate.count('sha256:' + image_digest) != 1
            or '--study' not in candidate or candidate.count('--study') != 1
            or '--rm' not in candidate
            or candidate.count('--cpus') != 1 or candidate[candidate.index('--cpus')+1] != '0.5'
            or candidate.count('--memory') != 1 or candidate[candidate.index('--memory')+1] != '512M'
            or candidate.count('--user') != 1 or candidate[candidate.index('--user')+1] != '65534:65534'
            or candidate[candidate.index('--study')+1:] !=
                ['/out/plan.json', '/out/candidate', '/out/exchange']):
            raise ValueError('FORMAL_CONTAINER_COMMAND_NOT_PINNED')
        image_index = candidate.index('sha256:' + image_digest)
        if candidate[image_index+1] != (
                '/src/research/integration/tk_model_task_guard_5260_a15_wslc_20261004/construction_x11.py'):
            raise ValueError('FORMAL_CONTAINER_ENTRYPOINT_CHANGED')
        mounts = [candidate[index+1] for index, value in enumerate(candidate[:-1])
                  if value == '--mount']
        expected_source = 'type=bind,source=' + str(source_root).replace('\\', '/') + ',target=/src,readonly'
        expected_output = 'type=bind,source=' + str(root).replace('\\', '/') + ',target=/out'
        if (len(mounts) != 2 or mounts.count(expected_source) != 1
            or mounts.count(expected_output) != 1):
            raise ValueError('FORMAL_CONTAINER_MOUNT_BINDING')
    if Path(config['candidate_output']).exists():
        raise ValueError('CANDIDATE_OUTPUT_MUST_NOT_EXIST')
    for directory in ('host-launch', 'candidate-launch', 'host'):
        if (root / directory).exists():
            raise ValueError('LAUNCH_OR_CUSTODY_DIRECTORY_EXISTS:' + directory)
    for raw in (config['python_executable'], config['host_script']):
        if not Path(raw).is_file():
            raise ValueError('OUTER_PLAN_EXECUTABLE_MISSING:' + raw)
    if Path(config['host_argv'][0]) != Path(config['python_executable']):
        raise ValueError('OUTER_PLAN_HOST_EXECUTABLE_JOIN')
    if not config['candidate_argv'] or not Path(config['candidate_argv'][0]).is_file():
        raise ValueError('OUTER_PLAN_CANDIDATE_EXECUTABLE_MISSING')
    return config


def launch(path):
    config = validate_outer_plan(path)
    root = Path(config['root'])
    host = start_capture(config['host_argv'], config['source_root'], root / 'host-launch')
    expected_host_plan = (root / 'host-plan.json').read_bytes()
    deadline = time.monotonic() + config['host_ready_timeout_seconds']
    while not host_plan_ready(root, expected_host_plan) \
            and host['process'] is not None and host['process'].poll() is None:
        if time.monotonic() >= deadline:
            break
        time.sleep(0.02)
    if not host_plan_ready(root, expected_host_plan):
        receipt = finish_capture(host, timeout_seconds=2)
        return dict(status='STOP_HOST_NOT_READY', host_exit_code=receipt['exit_code'])

    candidate = start_capture(config['candidate_argv'], config['source_root'],
                              root / 'candidate-launch')
    candidate_receipt = finish_capture(candidate,
        timeout_seconds=config['candidate_timeout_seconds'])
    if candidate_receipt['exit_code'] != 0 and host['process'] is not None \
            and host['process'].poll() is None:
        host['process'].terminate()
    host_receipt = finish_capture(host, timeout_seconds=config['host_timeout_seconds'])
    status = ('COMPLETE' if candidate_receipt['exit_code'] == 0
              and not candidate_receipt['timed_out']
              and host_receipt['exit_code'] == 0 and not host_receipt['timed_out']
              else 'STOP_LAUNCH_OR_EXCHANGE')
    return dict(status=status, host_exit_code=host_receipt['exit_code'],
                candidate_exit_code=candidate_receipt['exit_code'],
                candidate_timed_out=candidate_receipt['timed_out'])


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('formal_launch.py OUTER_PLAN.json')
    print(json.dumps(launch(sys.argv[1]), sort_keys=True))
