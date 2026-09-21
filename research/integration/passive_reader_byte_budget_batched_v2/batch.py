"""Issue 3999: two-case batches; unchanged Issue 3977 case function."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import run

ROOT = Path(__file__).resolve().parent


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def exclusive(path, value):
    with path.open('xb') as stream:
        stream.write(encoded(value))


def load(path):
    return json.loads(path.read_bytes())


def verify_freeze(path):
    freeze = load(path)
    for name, info in freeze['sources'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != info['sha256']:
            raise ValueError('SOURCE_FREEZE_MISMATCH:'+name)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def execute(out, index, mode, freeze_path):
    freeze_hash = verify_freeze(freeze_path)
    plan = ([(1024, 1, 0), (1025, 1, 0)] if mode == 'construction' else
            [(size, limit, rep) for rep in range(2) for size in (1023, 1024, 1025)
             for limit in (1, 32)])
    batches = len(plan)//2
    if not 0 <= index < batches:
        raise ValueError('INVALID_BATCH_INDEX')
    if (out/'STOP.json').exists():
        raise ValueError('ALLOCATION_ALREADY_STOPPED')
    rows = [] if index == 0 else load(out/'ROWS.json')
    if len(rows) != 2*index:
        raise ValueError('PREFIX_COUNT')
    for prior in range(index):
        done = load(out/f'BATCH-{prior:02d}.DONE.json')
        external = load(out/f'BATCH-{prior:02d}.EXECUTION.json')
        prefix_hash = hashlib.sha256(encoded(rows[:2*prior+2])).hexdigest()
        if (type(external['exit']) is not int or external['exit'] != 0
                or external['timed_out'] is not False or done['prefix_sha256'] != prefix_hash
                or done['range'] != [2*prior, 2*prior+2]):
            raise ValueError('PRECEDING_BATCH_NOT_VERIFIED')
    consumed = {'batch': index, 'range': [2*index, 2*index+2], 'pid': os.getpid(),
                'mode': mode, 'freeze_sha256': freeze_hash, 'argv': sys.argv,
                'prior_prefix_sha256': hashlib.sha256(encoded(rows)).hexdigest()}
    exclusive(out/f'BATCH-{index:02d}.CONSUMED.json', consumed)
    if index == 0:
        exclusive(out/'START.json', {'mode': mode, 'plan': plan, 'argv': sys.argv,
                                     'pid': os.getpid(), 'formal_retry_count': 0})
    try:
        for case_index in range(2*index, 2*index+2):
            size, limit, rep = plan[case_index]
            rows.append(run.one(out, case_index, size, limit, rep))
            run.put(out/'ROWS.json', rows)
        done = {'batch': index, 'range': [2*index, 2*index+2], 'pid': os.getpid(),
                'prefix_sha256': hashlib.sha256(encoded(rows)).hexdigest(),
                'prefix_count': len(rows), 'mode': mode, 'status': 'COMPLETE'}
        exclusive(out/f'BATCH-{index:02d}.DONE.json', done)
        if index == batches-1:
            exclusive(out/'TERMINAL.json', {'status': 'COMPLETE', 'rows': len(plan),
                                            'mode': mode, 'batch_count': batches})
        print(json.dumps(done, sort_keys=True), flush=True)
    except BaseException as error:
        exclusive(out/'STOP.json', {'batch': index, 'type': type(error).__name__,
                                    'message': str(error), 'complete_rows': len(rows)})
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--index', type=int, required=True)
    parser.add_argument('--mode', choices=('construction', 'formal'), required=True)
    parser.add_argument('--freeze', type=Path, required=True)
    args = parser.parse_args()
    execute(args.out.resolve(), args.index, args.mode, args.freeze.resolve())
