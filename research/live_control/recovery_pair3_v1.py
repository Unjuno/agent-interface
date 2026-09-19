"""Explicit per-model-call stages for registered OpenTTD pair 3; no automatic task loop."""
import argparse
import hashlib
import json
import time
import uuid
from pathlib import Path
from pointer_exchange_v1 import run as program
from pointer_report_view_v1 import pack
from read_pending_clock_v1 import run as drain
from received_history_v1 import assemble
from receipt_image import select_image
from unix_json_deadline import exchange

HERE = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('stage', choices=['initial', 'prepare', 'recover', 'open', 'build', 'finish'])
    ap.add_argument('socket')
    ap.add_argument('root', type=Path)
    ap.add_argument('arm', choices=['A', 'B'])
    args = ap.parse_args()
    root = args.root
    runtime = root / 'runtime'
    out = root / args.stage
    out.mkdir(exist_ok=False)
    started = time.perf_counter_ns()
    def save(name, value):
        (out / (name + '.json')).write_text(json.dumps(value, indent=2) + '\n')
    def read(stage, name):
        return json.loads((root / stage / (name + '.json')).read_text())
    def query(q):
        i = len(list(out.glob('query-*-request.json')))
        save(f'query-{i}-request', q)
        r = exchange(args.socket, q, timeout=30 if args.stage == 'finish' else 16)
        save(f'query-{i}-reply', r)
        return r
    def act(name, batch, steps):
        save(name + '-source', batch)
        save(name + '-steps', steps)
        r = program(query, batch, runtime, name, steps, 30000, lambda k, v: save(name + '-' + k, v))
        save(name + '-report', r)
        return r
    result = None
    try:
        if args.stage == 'initial':
            plan = json.loads((HERE / 'recovery_comparison_plan_v1.json').read_text())
            for name, digest in plan['sources'].items():
                assert hashlib.sha256((HERE.parent / name).read_bytes()).hexdigest() == digest, name
            save('execution', {'pair': 3, 'domain': 'openttd', 'seed': 203, 'seed_semantics': 'pair label; canonical save fixes world, no RNG seed override', 'depth': 1, 'arm': args.arm,
                 'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                 'plan_sha256': hashlib.sha256((HERE / 'recovery_comparison_plan_v1.json').read_bytes()).hexdigest(),
                 'model_label_from_system': 'Codex based on GPT-6', 'verified_model_id': None,
                 'verified_model_configuration': None, 'image_detail': 'original',
                 'presentation': 'same assembled history at recovery; reversible caller view for move',
                 'model_input_tokens': None, 'model_receipt_timestamps': None,
                 'qualification': 'unqualified for model performance while exact identity/configuration is missing'})
            b = query({'after': 0, 'events': ['observation'], 'timeout': 5})
            save('batch', b)
            result = {'batch': b, 'image': select_image(b, runtime)}
        elif args.stage == 'prepare':
            b = read('initial', 'batch')
            advance = act('advance', b, [{'op': 'observe'}])
            assert advance['state'] == 'terminal'
            stale = act('stale-right', b, [{'op': 'hold', 'keys': ['Right'], 'duration_ms': 80}])
            assert stale['program_sent'] is False and stale['reason'] == 'own command echo required'
            result = {'advance': pack(advance), 'stale': pack(stale)}
        elif args.stage == 'recover':
            stale = read('prepare', 'stale-right-report')
            if args.arm == 'A':
                after = stale['exchanges'][0]['reply']['cursor']
                q = {'after': after, 'events': ['clock'], 'timeout': .25}
                reply = query(q)
                history = assemble(stale['exchanges'] + [{'request': q, 'reply': reply}])
                records = history['review_batch']['records']
                own = stale['exchanges'][0]['request']['request_id']
                assert records[-2]['command']['transport_request_id'] == own
                assert records[-1]['event'] == 'clock'
            else:
                r = drain(stale, lambda q, remaining: exchange(args.socket, q, timeout=remaining), save)
                save('drain-report', r)
                assert r['state'] == 'own_clock_received_review_required'
                history = r['history']
            save('history', history)
            save('batch', history['review_batch'])
            result = {'history': history, 'image': select_image(history['review_batch'], runtime)}
        elif args.stage == 'open':
            r = act('open-toolbar', read('recover', 'batch'), [
                {'op': 'pointer_click', 'x': 820, 'y': 51}, {'op': 'observe'}])
            result = {'view': pack(r), 'image': r.get('image')}
        elif args.stage == 'build':
            r = act('build-road', read('open', 'open-toolbar-report')['last_reply'], [
                {'op': 'pointer_click', 'x': 709, 'y': 90},
                {'op': 'pointer_drag', 'points': [{'x': 685, 'y': 383}, {'x': 641, 'y': 400}, {'x': 609, 'y': 417}], 'duration_ms': 300},
                {'op': 'observe'}])
            result = {'view': pack(r), 'image': r.get('image')}
        else:
            b = read('build', 'build-road-report')['last_reply']
            result = query({'after': b['cursor'], 'events': ['independent_evaluation'], 'timeout': 25,
                            'request_id': uuid.uuid4().hex, 'command': {'op': 'finish'}})
        save('result', result)
        print(json.dumps(result))
    finally:
        save('stage-timing', {'started_ns': started, 'returned_ns': time.perf_counter_ns(),
                             'scope': 'local CLI stage, excludes model receipt/review and image rendering'})


if __name__ == '__main__':
    main()
