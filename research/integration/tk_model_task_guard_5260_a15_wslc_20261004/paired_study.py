"""Finite actual live paired entry. Scientific/file disposition is external."""
import json
import math
import os
from pathlib import Path
import re
import sys
import time

from file_exchange import ExchangeClient
from host_bridge import sha


LOCAL_SOURCES = ('paired_study.py', 'live_pair.py', 'live_app.py', 'task_session.py',
                 'task_guard.py', 'file_exchange.py', 'host_bridge.py',
                 'model_contract.py', 'construction_x11.py')


def local_sources():
    root = Path(__file__).resolve().parent
    return [dict(path=str(root/name), sha256=sha((root/name).read_bytes()))
            for name in LOCAL_SOURCES]


def task_prompt(plan, row):
    prompt=plan['prompt']
    if plan.get('formal_allocation') is True:
        prompt += ('\nRequested target value (exact text): '
            + json.dumps(row['wanted'], ensure_ascii=False)
            + '\nRead the target and decoy literally from the attached image. Choose NO_REPAIR '
            'only when the target already equals the requested value and the decoy is empty. '
            'Choose INSERT_PREFIX only when the nonempty target is the exact suffix of the '
            'requested value and the missing leading prefix is exactly one character. Never '
            'edit the decoy or invent replacement text. Choose REFUSE when the target is empty, '
            'the decoy is nonempty, or the image is ambiguous. Report the observed target and '
            'decoy exactly as seen; return only the required JSON object.')
    return prompt.encode('utf-8')


def publish(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, sort_keys=True)
        stream.write('\n')


def run(plan_path, output, exchange):
    blob = Path(plan_path).read_bytes()
    plan = json.loads(blob)
    if (plan.get('schema') != 'a15-live-paired-study-v1'
        or type(plan.get('allocation')) is not str or not plan['allocation']
        or type(plan.get('source_sha256')) is not dict or not plan['source_sha256']
        or type(plan.get('rows')) is not list or not 1 <= len(plan['rows']) <= 4
        or type(plan.get('prompt')) is not str or not plan['prompt']
        or type(plan.get('response_timeout_seconds')) not in (int,float)
        or not math.isfinite(plan['response_timeout_seconds'])
        or not 0 < plan['response_timeout_seconds'] <= 70):
        raise ValueError('Finite explicit paired plan required')
    rows = plan['rows']
    if (any(type(row) is not dict or set(row) != {'id','wanted','target','decoy','focus_drift'}
            or type(row['id']) is not str or re.fullmatch('pair-[0-9]{3}',row['id']) is None
            or any(type(row[key]) is not str for key in ('wanted','target','decoy'))
            or not row['wanted'] or type(row['focus_drift']) is not bool for row in rows)
        or len({row['id'] for row in rows}) != len(rows)):
        raise ValueError('Invalid paired schedule')
    local = local_sources()
    if any(plan['source_sha256'].get(row['path']) != row['sha256'] for row in local):
        raise ValueError('METHOD_STOP_LOCAL_SOURCE_UNCOVERED')
    for name, expected in plan['source_sha256'].items():
        if type(expected) is not str or sha(Path(name).read_bytes()) != expected:
            raise ValueError('METHOD_STOP_SOURCE_CHANGED:'+name)
    out = Path(output)
    out.mkdir(parents=True, exist_ok=False)
    freeze_sha256 = sha(blob)
    publish(out/'study-attempt.json', dict(allocation=plan['allocation'],
        freeze_sha256=freeze_sha256, plan=plan, started_ns=time.monotonic_ns()))
    slots = [row['id']+'-'+kind for row in rows for kind in ('first','recovery')]
    client = ExchangeClient(exchange, allocation=plan['allocation'], freeze_sha256=freeze_sha256,
                            slots=slots)
    results, error = [], None
    try:
        from live_pair import LivePair, run_pair
        for row in rows:
            pair = None
            try:
                pair = LivePair(out/row['id'], wanted=row['wanted'], initial_target=row['target'],
                    initial_decoy=row['decoy'], freeze_sha256=freeze_sha256,
                    display_name=os.environ['DISPLAY'])
                result = run_pair(pair, client, row['id'], prompt=task_prompt(plan,row),
                    focus_drift=row['focus_drift'], response_timeout_seconds=plan['response_timeout_seconds'])
                results.append(dict(id=row['id'], cli_calls=result['cli_calls']))
            finally:
                if pair is not None:
                    pair.close()
                    if json.loads((pair.out/'close.json').read_bytes())['errors']:
                        raise ValueError('METHOD_STOP_OWNED_CLEANUP_FAULT')
    except BaseException as exception:
        error = type(exception).__name__+':'+str(exception)
    imports = []
    for name, module in sorted(sys.modules.items()):
        path = getattr(module,'__file__',None)
        if name.startswith('runtime.') and path and Path(path).suffix == '.py':
            imports.append(dict(module=name, path=path, sha256=sha(Path(path).read_bytes())))
    # Later imported bytes must be in the prospectively frozen source set.
    uncovered = [row['path'] for row in imports
                 if plan['source_sha256'].get(row['path']) != row['sha256']]
    final_local = local_sources()
    uncovered += [row['path'] for row in final_local
                  if plan['source_sha256'].get(row['path']) != row['sha256']]
    if uncovered and error is None:
        error = 'METHOD_STOP_LATE_SOURCE_UNCOVERED'
    result = dict(schema='a15-live-paired-result-v1', allocation=plan['allocation'],
        freeze_sha256=freeze_sha256, rows=results, error=error, runtime_imports=imports,
        local_sources=final_local,
        uncovered_imports=uncovered, task_complete=False, ended_ns=time.monotonic_ns())
    publish(out/'study-result.json', result)
    print(json.dumps(dict(rows=len(results), error=error, task_complete=False)))
    return 1 if error else 0


if __name__ == '__main__':
    raise SystemExit(run(*sys.argv[1:]))
