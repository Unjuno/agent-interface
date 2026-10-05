"""Independent six-history oracle: stdlib JSON only, no kernel/runner imports."""
import copy
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

CASES = {
    'unbegun': (False, None, None, ['authorized', 'stop_with_verified_release']),
    'begun_failure_before_effect': (True, None, 0, ['authorized', 'begin_accepted', 'execute_receipt_unavailable', 'stop_with_verified_release']),
    'begun_failure_after_effect': (True, None, 1, ['authorized', 'begin_accepted', 'execute_receipt_unavailable', 'stop_with_verified_release']),
    'completed_none': (False, 'none', None, ['authorized', 'begin_accepted', 'receipt_accepted', 'stop_with_verified_release']),
    'completed_possible': (True, 'possible', None, ['authorized', 'begin_accepted', 'receipt_accepted', 'stop_with_verified_release']),
    'completed_observed': (True, 'observed', None, ['authorized', 'begin_accepted', 'receipt_accepted', 'stop_with_verified_release']),
}


def classify(rows):
    if len(rows) != len(CASES) or {r['case'] for r in rows} != set(CASES):
        raise ValueError('six-case roster mismatch')
    gaps = []
    for r in rows:
        possible, occurrence, inert_count, events = CASES[r['case']]
        if r['events'] != events or r['receipt_occurrence'] != occurrence:
            raise ValueError('history mismatch')
        if r['inert_application_effect_count'] != inert_count:
            raise ValueError('inert world mismatch')
        outcome = r['outcome']
        if (outcome['stage'] != 'stopped' or outcome['reason'] != 'cancelled'
                or outcome['effect_verified'] is not False
                or outcome['release_verified'] is not True
                or outcome['command_id'] != (None if r['case'] == 'unbegun' else 'cmd-1')
                or type(outcome['effect_occurred']) is not bool):
            raise ValueError('non-effect control mismatch')
        if outcome['effect_occurred'] is not possible:
            gaps.append(r['case'])
    return gaps


def main():
    root = Path(__file__).resolve().parent
    start = datetime.now(timezone.utc).isoformat()
    results = []
    for name in ['raw-before.jsonl','raw-after.jsonl']:
        raw = (root / name).read_bytes()
        rows = [json.loads(line) for line in raw.splitlines()]
        gaps = classify(rows)
        wanted = ['begun_failure_before_effect','begun_failure_after_effect'] if name == 'raw-before.jsonl' else []
        if gaps != wanted:raise ValueError(f'unexpected gaps in {name}: {gaps}')
        results.append({'file':name,'sha256':hashlib.sha256(raw).hexdigest(),
                        'rows':len(rows),'missing_possible_effect':gaps})
    rows = [json.loads(line) for line in (root / 'raw-after.jsonl').read_bytes().splitlines()]
    mutations = []
    for name in ['missing_row','duplicate_case','false_pending_effect','invent_verified_effect','invent_no_release','wrong_command']:
        changed = copy.deepcopy(rows)
        if name == 'missing_row':changed.pop()
        elif name == 'duplicate_case':changed[-1] = copy.deepcopy(changed[0])
        elif name == 'false_pending_effect':changed[1]['outcome']['effect_occurred'] = False
        elif name == 'invent_verified_effect':changed[1]['outcome']['effect_verified'] = True
        elif name == 'invent_no_release':changed[1]['outcome']['release_verified'] = False
        else:changed[1]['outcome']['command_id'] = 'different'
        try: rejected = bool(classify(changed))
        except ValueError:rejected = True
        if not rejected:raise ValueError(f'corruption accepted: {name}')
        mutations.append({'name':name,'rejected':True})
    report = {'disposition':'SCOPED_CANCELLATION_EFFECT_GAP_AND_REPAIR',
              'started_utc':start,'ended_utc':datetime.now(timezone.utc).isoformat(),
              'inputs':results,'corruption_controls':mutations,
              'scope':'sequential contract only; inert application worlds, no native backend/input'}
    print(json.dumps(report))


if __name__ == '__main__':main()
