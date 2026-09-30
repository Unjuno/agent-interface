"""One original-runtime diagnostic; no repair, native session or scientific retry."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
import hashlib
import importlib
import json
import os
from pathlib import Path
import resource
import sys
import threading
import time
import traceback
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'formal-01'
ACTIVE = ''
PROFILE = []
TRIPWIRES = []
JOURNAL = None
SOURCE_FILE = str(ROOT / 'upstream/runtime/cli_v1/mcp_server.py')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2, sort_keys=True, allow_nan=False)
        f.write('\n')


def event(kind, **value):
    row = dict(kind=kind, monotonic_ns=time.monotonic_ns(), **value)
    JOURNAL.write(json.dumps(row, sort_keys=True, allow_nan=False) + '\n')
    JOURNAL.flush()


def profile(frame, kind, _arg):
    if kind == 'call' and frame.f_code.co_filename == SOURCE_FILE and frame.f_code.co_name == 'invoke':
        PROFILE.append({'label': ACTIVE, 'function': 'invoke',
            'operation': frame.f_locals.get('operation'), 'thread_id': threading.get_ident(),
            'monotonic_ns': time.monotonic_ns(), 'source_file': SOURCE_FILE})


def tripwire(name):
    def reject(*_args, **_kwargs):
        TRIPWIRES.append(name)
        raise RuntimeError('FORBIDDEN_NATIVE_PATH:' + name)
    return reject


def inventory(folder):
    return {str(p.relative_to(folder)): {'bytes': p.stat().st_size, 'sha256': digest(p)}
            for p in sorted(folder.rglob('*')) if p.is_file()}


def loaded_modules():
    result = {}
    for name, module in sorted(sys.modules.items()):
        file = getattr(module, '__file__', None)
        if file and Path(file).is_file():
            path = Path(file).resolve()
            result[name] = {'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest(path)}
    return result


async def capture(server, tool, arguments, label):
    event('public_call_started', label=label, tool=tool, arguments=arguments)
    try:
        reply = await server.call_tool(tool, arguments)
        value = reply.model_dump(mode='json')
        result = {'kind': 'return', 'class': type(reply).__module__ + '.' + type(reply).__name__, 'value': value}
    except Exception as error:
        result = {'kind': 'exception', 'type': type(error).__name__, 'message': str(error),
                  'traceback': traceback.format_exc()}
    event('public_call_completed', label=label, result=result)
    return result


async def run_cases(module):
    global ACTIVE
    loop = asyncio.get_running_loop()
    healthy = ThreadPoolExecutor(max_workers=1, thread_name_prefix='diagnostic-healthy')
    rejected = ThreadPoolExecutor(max_workers=1, thread_name_prefix='diagnostic-rejected')
    rejected.shutdown(wait=True)
    loop.set_default_executor(healthy)
    rows = []
    owners = {}
    def make(name):
        server = module.create_server({'fixture': 123}, str(OUT / name),
                                      display_name='no-display', session_mode='persistent-x11')
        owners[name] = server
        event('server_created', server=name)
        return server
    async def close(server, directory, label):
        global ACTIVE
        ACTIVE = label
        before = len(PROFILE)
        response = await capture(server, 'interface_close', {}, label)
        entered = len(PROFILE) - before
        ACTIVE = label + '_list'
        ledger = await capture(server, 'interface_results', {}, ACTIVE)
        row = {'label': label, 'tool': 'interface_close', 'arguments': {}, 'result': response,
            'invoke_entries': entered, 'ledger': ledger, 'server_directory': directory,
            'inventory': inventory(OUT / directory)}
        rows.append(row)
        save(OUT / (label + '.json'), row)
        event('row_retained', label=label, invoke_entries=entered)
    try:
        await close(make('healthy'), 'healthy', 'healthy_close')
        affected = make('rejection')
        loop.set_default_executor(rejected)
        event('executor_installed', state='already_shutdown')
        await close(affected, 'rejection', 'rejected_close')
        loop.set_default_executor(healthy)
        event('executor_installed', state='original_healthy_restored')
        ACTIVE = 'executor_health_probe'
        sentinel = await asyncio.to_thread(lambda: {'value': 'healthy-executor',
                                                   'thread_id': threading.get_ident()})
        probe = dict(sentinel, completed=True)
        event('executor_health_probe_completed', result=probe)
        await close(affected, 'rejection', 'recovered_close')
        await close(make('fresh'), 'fresh', 'fresh_close')
        return {'rows': rows, 'health_probe': probe}
    finally:
        # No owner cleanup is dispatched here: no owner ever opens a native session.
        loop.set_default_executor(healthy)
        rejected.shutdown(wait=True)
        healthy.shutdown(wait=True)


def main():
    global JOURNAL
    OUT.mkdir(exist_ok=False)
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024,) * 2)
    resource.setrlimit(resource.RLIMIT_CPU, (15, 15))
    JOURNAL = (OUT / 'EVENTS.jsonl').open('x', encoding='utf-8')
    result = {'disposition': 'STOP_BEFORE_OUTCOME'}
    before = {}
    freeze = json.loads((ROOT / 'FREEZE.json').read_text())
    expected = freeze['files']
    save(OUT / 'PREFLIGHT.json', {'affinity': sorted(os.sched_getaffinity(0)),
        'rlimit_as': resource.getrlimit(resource.RLIMIT_AS),
        'rlimit_cpu': resource.getrlimit(resource.RLIMIT_CPU), 'freeze_sha256': digest(ROOT / 'FREEZE.json')})
    try:
        before = {n: digest(ROOT / n) for n in expected}
        if before != expected:
            raise RuntimeError('frozen source mismatch')
        imported = json.loads((ROOT / 'preflight-01/RESULT.json').read_text())
        if imported['status'] != 'PASS_IMPORT_ONLY':
            raise RuntimeError('import preflight unavailable')
        for name, rec in imported['loaded_files'].items():
            if digest(Path(rec['path'])) != rec['sha256']:
                raise RuntimeError('dependency changed:' + name)
        event('all_frozen_and_dependency_hashes_verified')
        sys.path.insert(0, str(ROOT / 'upstream'))
        module = importlib.import_module('runtime.cli_v1.mcp_server')
        session = importlib.import_module('runtime.cli_v1.mcp_session')
        if str(Path(module.__file__).resolve()) != SOURCE_FILE:
            raise RuntimeError('wrong module origin')
        with ExitStack() as guards:
            for mod, names in ((module, ('dispatch', 'dispatch_in_session', 'observe', 'observe_in_session')),
                               (session, ('open_session', 'select_backend', 'inspect_focused_target', 'observe_in_session'))):
                for name in names:
                    guards.enter_context(patch.object(mod, name, tripwire(mod.__name__ + '.' + name)))
            threading.setprofile(profile)
            try:
                data = asyncio.run(run_cases(module))
            finally:
                threading.setprofile(None)
        after = {n: digest(ROOT / n) for n in expected}
        journal = [json.loads(line) for line in (OUT / 'EVENTS.jsonl').read_text().splitlines()]
        started = [x for x in journal if x['kind'] == 'public_call_started']
        raw = dict(schema='mcp-preworker-original-v1', synthetic=False,
            evidence_origin='observed_transcript_of_deliberately_injected_executor_lifecycle_fault', **data,
            profile_events=PROFILE, tripwire_calls=TRIPWIRES, source_unchanged=before == after,
            public_close_calls=sum(x['tool'] == 'interface_close' for x in started),
            public_list_calls=sum(x['tool'] == 'interface_results' for x in started),
            executor_probe_calls=sum(x['kind'] == 'executor_health_probe_completed' for x in journal))
        save(OUT / 'RAW.json', raw)
        from oracle import audit
        audited = audit(raw, OUT)
        save(OUT / 'AUDIT.json', audited)
        result = dict(audited, formal_invocations=1)
        if not audited['errors']:
            from controls import controls
            checked = controls(raw)
            save(OUT / 'CONTROLS.json', checked)
            result['controls_passed'] = checked['passed']
            if not checked['passed']:
                result['observed_behavior_disposition'] = result['disposition']
                result['disposition'] = 'HOLD_CONTROL_INTEGRITY'
    except BaseException as error:
        result.update(error_type=type(error).__name__, error=str(error), traceback=traceback.format_exc())
    finally:
        JOURNAL.close()
        save(OUT / 'RESULT.json', result)
        save(OUT / 'LOADED_MODULES.json', {'files': loaded_modules(),
            'scope': 'Actual terminal loaded source/library inventory, including lazy imports; no extra tool calls'})
        after = {n: digest(ROOT / n) for n in expected if (ROOT / n).is_file()}
        save(OUT / 'RECEIPT.json', {'source_before': before, 'source_after': after,
            'source_unchanged': before == after == expected,
            'outputs': inventory(OUT), 'profile_events': PROFILE, 'tripwire_calls': TRIPWIRES,
            'resource': {'affinity': sorted(os.sched_getaffinity(0)),
                'rlimit_as': resource.getrlimit(resource.RLIMIT_AS),
                'rlimit_cpu': resource.getrlimit(resource.RLIMIT_CPU),
                'ru_maxrss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}})
    return 0 if result['disposition'] == 'PASS_PREWORKER_CAPACITY_RELEASE_SCOPED' else 1


if __name__ == '__main__':
    raise SystemExit(main())
