"""Experimental exact-CID cleanup. No input-release or production guarantees."""
import base64
import json
import math
import re
import subprocess
import time

LABEL = 'agent-interface.run-id'


def _run(args, timeout):
    return subprocess.run(args, capture_output=True, timeout=timeout, check=False)


def cleanup_owned(cid, run_id, *, timeout_s=10, runner=_run):
    result = {'status': 'UNKNOWN', 'commands': []}
    if (not isinstance(cid, str) or not re.fullmatch(r'[0-9a-f]{64}', cid)
            or not isinstance(run_id, str) or not re.fullmatch(r'[0-9a-f]{32}', run_id)
            or type(timeout_s) not in (int, float) or not math.isfinite(timeout_s) or timeout_s <= 0):
        return result
    deadline = time.monotonic() + timeout_s

    def call(args):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None
        record = {'argv': args}
        result['commands'].append(record)
        try:
            p = runner(args, timeout=remaining)
            record.update(returncode=p.returncode,
                          stdout_b64=base64.b64encode(p.stdout).decode('ascii'),
                          stderr_b64=base64.b64encode(p.stderr).decode('ascii'))
            if p.returncode != 0 or p.stderr or time.monotonic() >= deadline:
                return None
            return p.stdout
        except (OSError, subprocess.TimeoutExpired) as exc:
            record['error_type'] = type(exc).__name__
            if isinstance(exc, subprocess.TimeoutExpired):
                for field in ('stdout', 'stderr'):
                    value = getattr(exc, field, None)
                    if isinstance(value, bytes):
                        record[field + '_b64'] = base64.b64encode(value).decode('ascii')
            return None

    raw = call(['wslc', 'container', 'inspect', cid, '--format', 'json'])
    try:
        data = json.loads(raw)
        item = data[0] if isinstance(data, list) and len(data) == 1 else None
        if (not isinstance(item, dict) or item.get('Id') != cid
                or item.get('Config', {}).get('Labels', {}).get(LABEL) != run_id
                or item.get('State', {}).get('Running') is not True):
            return result
    except (ValueError, TypeError, AttributeError):
        return result
    list_args = ['wslc', 'container', 'list', '--all', '--filter', 'id=' + cid,
                 '--format', 'json', '--no-trunc']
    raw = call(list_args)
    try:
        rows = [json.loads(line) for line in raw.splitlines()]
        if len(rows) != 1 or not isinstance(rows[0], dict) or rows[0].get('ID') != cid:
            return result
    except (ValueError, TypeError, AttributeError):
        return result
    raw = call(['wslc', 'container', 'stop', '--time', '2', cid])
    if raw is None or raw.strip() != cid.encode('ascii'):
        return result
    result['stop_command_succeeded'] = True
    raw = call(list_args)
    if raw is not None and not raw.strip():
        result['status'] = 'observed_absent'
    return result
