"""Independent raw-only oracle: literal typed deck and graph reachability."""
import copy
import hashlib
import json
from pathlib import Path
import sys

VALUES = [None, '', 0, True, False, 1.0, [], {}, 'x' * 65, 'w', 'x' * 64, 'independent-witness']
LABELS = ['succeeded', 'failed', 'unavailable']

def same(a, b):
    if type(a) is not type(b):
        return False
    if type(a) is dict:
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if type(a) is list:
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b

def audit(record):
    errors, violations = [], []
    if record.get('schema') != 'compiled-success-evidence-regression-v1' or record.get('arm') not in ('baseline', 'repaired'):
        return {'errors': ['schema_or_arm'], 'contract_violations': [], 'rows': len(record.get('rows', []))}
    source = Path(__file__).with_name(record['arm'] + '_compiled_gui.txt')
    if record.get('source_sha256') != hashlib.sha256(source.read_bytes()).hexdigest():
        errors.append('source_identity')
    rows = record.get('rows', [])
    wanted = {f'{s}-{i}-{n}' for s in LABELS for i in range(12) for n in (1, 2)}
    ids = [r.get('id') for r in rows]
    if len(rows) != 72 or len(set(ids)) != 72 or set(ids) != wanted:
        errors.append('coverage')
    for row in rows:
        s, i, stage = row['status'], row['ref_index'], row['stage']
        if s not in LABELS or type(i) is not int or not 0 <= i < 12 or type(stage) is not int or stage not in (1, 2):
            errors.append('case:' + str(row.get('id'))); continue
        if row['id'] != f'{s}-{i}-{stage}' or not same(row['evidence_ref'], VALUES[i]):
            errors.append('input:' + row['id'])
        invalid_success = s == 'succeeded' and i < 9
        reject = invalid_success and record['arm'] == 'repaired'
        steps = stage if reject or s != 'succeeded' else 2
        result = row['result']
        calls, events = row['calls'], row['events']
        expected_counts = {'execute': steps, 'admit': steps, 'observe': steps + 1, 'verify_effect': steps}
        if {k: len(v) for k, v in calls.items()} != expected_counts:
            errors.append('calls:' + row['id'])
        if row['interface_unchanged'] is not True or row['verdicts_unchanged'] is not True:
            errors.append('mutation:' + row['id'])
        terminals = [e for e in events if e.get('event') == 'action_terminal']
        effects = [e for e in events if e.get('event') == 'effect_checked']
        finishes = [e for e in events if e.get('event') == 'runtime_finished']
        if len(terminals) != steps or any(e.get('release_verified') is not True for e in terminals):
            errors.append('terminal:' + row['id'])
        if len(effects) != steps - int(reject):
            errors.append('effect_count:' + row['id'])
        for j, event in enumerate(effects, 1):
            ref = VALUES[i] if j == stage else 'frame' + str(j + 1)
            status = s if j == stage else 'succeeded'
            if event.get('status') != status or not same(event.get('evidence_ref'), ref):
                errors.append('effect_identity:' + row['id'])
        if reject:
            if row['exception'] != 'ValueError' or result is not None or finishes:
                errors.append('rejection:' + row['id'])
        else:
            outcome = 'TASK_SUCCEEDED' if s == 'succeeded' else 'SAFE_YIELD'
            reason = {'succeeded': 'method_complete', 'failed': 'effect_failed', 'unavailable': 'effect_unavailable'}[s]
            if row['exception'] is not None or type(result) is not dict or len(finishes) != 1:
                errors.append('return:' + row['id']); continue
            if not same([result.get('outcome'), result.get('reason'), result.get('completed_transitions')], [outcome, reason, steps]):
                errors.append('result:' + row['id'])
            if not same(result.get('critical_events'), [e for e in events if e['event'] in {
                    'branch_selected', 'admission_refused', 'action_terminal', 'effect_checked', 'runtime_finished'}]):
                errors.append('journal:' + row['id'])
            if s != 'succeeded' and result.get('pending_effect', {}).get('action') != ('enter' if stage == 1 else 'save'):
                errors.append('pending:' + row['id'])
        if invalid_success and not reject:
            violations.append(row['id'])
    return {'errors': errors, 'contract_violations': violations, 'rows': len(rows)}

def controls(record):
    altered = []
    x = copy.deepcopy(record); x['rows'].pop(); altered.append(('missing_row', x))
    x = copy.deepcopy(record); x['rows'][0] = copy.deepcopy(x['rows'][1]); altered.append(('duplicate', x))
    x = copy.deepcopy(record); x['rows'][4]['evidence_ref'] = 0.0; altered.append(('json_type', x))
    x = copy.deepcopy(record); x['rows'][0]['calls']['execute'].append({}); altered.append(('extra_dispatch', x))
    x = copy.deepcopy(record); x['rows'][0]['events'].append({'event': 'runtime_finished'}); altered.append(('false_completion', x))
    x = copy.deepcopy(record); x['rows'][0]['events'][2]['release_verified'] = False; altered.append(('release', x))
    return {name: bool(audit(value)['errors']) for name, value in altered}

if __name__ == '__main__':
    before, after, output = map(Path, sys.argv[1:4])
    baseline, repaired = json.loads(before.read_bytes()), json.loads(after.read_bytes())
    result = {'baseline': audit(baseline), 'repaired': audit(repaired), 'corruptions': controls(repaired),
              'baseline_raw_sha256': hashlib.sha256(before.read_bytes()).hexdigest(),
              'repaired_raw_sha256': hashlib.sha256(after.read_bytes()).hexdigest()}
    ok = (not result['baseline']['errors'] and not result['repaired']['errors'] and
          len(result['baseline']['contract_violations']) == 18 and
          not result['repaired']['contract_violations'] and all(result['corruptions'].values()))
    result['status'] = 'PASS_SUCCESS_REFERENCE_SCOPED' if ok else 'FAIL_AUDIT'
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, indent=2, sort_keys=True); stream.write('\n')
    print(json.dumps(result))
    sys.exit(0 if ok else 1)
