"""Scripted live sequence-mismatch isolation and received-history integration.

The deliberately inconsistent batch is a fault injection, never a real receipt.
Recovery submits only observe; this is not gameplay/task success or model self-use.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import uuid
from pointer_exchange_v1 import run
from pointer_report_view_v1 import pack, unpack
from received_history_v1 import assemble
from receipt_image import select_image
from unix_json_deadline import exchange

HERE = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('socket')
    ap.add_argument('runtime', type=Path)
    ap.add_argument('out', type=Path)
    args = ap.parse_args()
    args.out.mkdir(exist_ok=False)
    def save(name, value):
        (args.out / (name + '.json')).write_text(json.dumps(value, indent=2) + '\n')
    save('plan', {'controller': 'scripted live fault injection',
        'purpose': 'current cursor with deliberately old observation; no physical input expected',
        'recovery': 'assemble real received history; validate image sequence; explicit observe-only program',
        'sources': {str(p.relative_to(HERE.parent)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in [Path(__file__), *[HERE / n for n in ('pointer_exchange_v1.py', 'pointer_report_view_v1.py', 'received_history_v1.py', 'receipt_image.py', 'unix_json_deadline.py', 'pointer_socket_entry_v1.py')]]}})
    segments = []
    cursor = 0
    def query(request):
        nonlocal cursor
        index = len(segments)
        save(f'request-{index}', request)
        reply = exchange(args.socket, request, timeout=16)
        save(f'reply-{index}', reply)
        segments.append({'request': request, 'reply': reply})
        cursor = reply['cursor']
        save('segments', segments)
        return reply
    def call(name, batch, steps):
        save(name + '-source', batch)
        save(name + '-steps', steps)
        report = run(query, batch, args.runtime, name, steps, 30000,
                     lambda key, value: save(name + '-' + key, value))
        save(name + '-report', report)
        view = pack(report)
        assert unpack(view) == report
        save(name + '-view', view)
        return report
    outcome = {'success': False}
    try:
        initial = query({'after': 0, 'events': ['observation'], 'timeout': 5})
        advance = call('advance', initial, [{'op': 'observe'}])
        assert advance['state'] == 'terminal'
        # Fault injection: keep original event data but replace its consumer cursor.
        # Do not represent this synthetic combination as an actual transport reply.
        faulty = copy.deepcopy(initial)
        faulty['cursor'] = cursor
        faulty['fault_injection'] = 'current received cursor with old observation records'
        stale = call('stale-right', faulty, [{'op': 'hold', 'keys': ['Right'], 'duration_ms': 80}])
        assert stale['state'] == 'needs_reconciliation' and stale['program_sent'] is False
        assert stale['reason'] == 'clock sequence or timestamp mismatch; no new image authority'
        assert len(stale['exchanges']) == 1 and 'continuation_batch' not in stale
        assembled = assemble(segments)
        save('assembled-before-recovery', assembled)
        selected = select_image(assembled['review_batch'], args.runtime)
        save('selected-recovery-image', selected)
        assert selected['sequence'] == 2 and assembled['review_batch']['cursor'] == cursor
        recovered = call('recover-observe', assembled['review_batch'], [{'op': 'observe'}])
        assert recovered['state'] == 'terminal' and recovered['terminal']['status'] == 'completed'
        outcome.update(success=True, stale_reason=stale['reason'], recovery_sequence=recovered['image']['sequence'],
                       scope='scripted transport/history readiness; observe-only recovery, not task success')
    except Exception as exc:
        outcome['error'] = repr(exc)
        raise
    finally:
        try:
            finish = query({'after': cursor, 'events': ['independent_evaluation'], 'timeout': 5,
                            'request_id': uuid.uuid4().hex, 'command': {'op': 'finish'}})
            save('finish', finish)
        except Exception as exc:
            outcome['finish_error'] = repr(exc)
        save('outcome', outcome)
        print(json.dumps(outcome))


if __name__ == '__main__':
    main()
