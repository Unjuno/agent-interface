"""Copied saved-data review probes only, never native calls or original audit repair."""
import copy, datetime, hashlib, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from auditor import check
from checks import check_rows

def invented(rows):
    for row in rows:
        for stage in [row['acquisition'], *row['arms'].values()]:
            for c in stage['calls']: c['op'] = 'Invented'
def wrong_windows(rows):
    for row in rows:
        for stage in [row['acquisition'], *row['arms'].values()]:
            for c in stage['calls']: c['window'] = 999999
def reversed_acquisition(rows):
    rows[0]['acquisition']['calls'][0].update(start_ns=-1, end_ns=-2)
def before_mutation(rows):
    row = next(r for r in rows if r['mode'] == 'STALE_HINT')
    t = row['acquisition']['calls'][0]['start_ns']
    for stage in row['arms'].values():
        for c in stage['calls']: c.update(start_ns=t, end_ns=t+1); t += 2
def zero_elapsed(rows):
    for row in rows:
        for stage in [row['acquisition'], *row['arms'].values()]: stage['elapsed_ns'] = 0

def main():
    raw = ROOT/'runs/candidate/raw.jsonl'; oracle = ROOT/'runs/candidate/oracle.jsonl'
    rows = [json.loads(s) for s in raw.read_text().splitlines()]; truth = [json.loads(s) for s in oracle.read_text().splitlines()]
    result = {'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'scope': 'POSTRUN_SAVED_STRUCTURAL_CONSISTENCY_ONLY', 'native_runs': 0, 'formal_auditor_runs': 0, 'raw_sha256': hashlib.sha256(raw.read_bytes()).hexdigest(), 'first_status_unchanged': check(rows, truth)['first_status'], 'actual_saved_rows_check': check_rows(rows), 'rows': len(rows), 'td_red': {'tests': 6, 'failures': 6, 'exit': 1, 'stub': 'check_rows returnedFalse without exceptions'}, 'controls': []}
    for name, mutate in [('invented_ops', invented), ('wrong_window_ids', wrong_windows), ('negative_reversed_acquisition', reversed_acquisition), ('reacquisition_before_mutation', before_mutation), ('zero_elapsed', zero_elapsed)]:
        altered = copy.deepcopy(rows); mutate(altered)
        assert json.dumps(altered, sort_keys=True) != json.dumps(rows, sort_keys=True)
        original_accepted = False
        try: check(altered, truth); original_accepted = True
        except AssertionError: pass
        saved_rejected = False
        try: check_rows(altered)
        except AssertionError: saved_rejected = True
        result['controls'].append({'name': name, 'original_frozen_auditor_accepted': original_accepted, 'supplement_rejected': saved_rejected})
    assert all(c['original_frozen_auditor_accepted'] and c['supplement_rejected'] for c in result['controls'])
    with (ROOT/'saved_review/SAVED_CHECKS.json').open('x') as f: json.dump(result, f, indent=2); f.write('\n')
    print(json.dumps(result, indent=2))
if __name__ == '__main__': main()
