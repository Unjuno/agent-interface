import copy
import hashlib
import json
from pathlib import Path

fixture_bytes = Path('/source/candidate-events.jsonl').read_bytes()
fixture = [json.loads(line) for line in fixture_bytes.decode('utf-8').splitlines() if line]
source_bytes = Path('/source/map01_overlap_controller_v39.py').read_bytes()
candidate_bytes = Path('/evidence/candidate.json').read_bytes()
result = json.loads(candidate_bytes.decode('utf-8'))


def canonical_hash(rows):
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()


def contradiction(row):
    altered = copy.deepcopy(row)
    altered['physical_key_measurement']['adapter_edge']['interval'] = [1, 2]
    altered['physical_key_measurement']['bracket'][
        'physical_down_interval' if altered['event'] == 'input_admission'
        else 'physical_up_interval'] = [1, 2]
    return altered


def reconstruct_cases(rows):
    downs = [row for row in rows if row.get('event') == 'input_admission']
    ups = [row for row in rows if row.get('event') == 'input_release_measurement']
    if len(downs) != 1 or len(ups) != 1:
        raise ValueError('frozen A01 input identity is not one DOWN / one UP')
    down, up = downs[0], ups[0]
    return {
        'baseline_unique_pair': copy.deepcopy(rows),
        'duplicate_down_identical': [copy.deepcopy(down), copy.deepcopy(down), copy.deepcopy(up)],
        'duplicate_up_identical': [copy.deepcopy(down), copy.deepcopy(up), copy.deepcopy(up)],
        'duplicate_both_identical': [copy.deepcopy(down), copy.deepcopy(down), copy.deepcopy(up), copy.deepcopy(up)],
        'duplicate_down_conflicting': [copy.deepcopy(down), contradiction(down), copy.deepcopy(up)],
        'duplicate_up_conflicting': [copy.deepcopy(down), copy.deepcopy(up), contradiction(up)],
    }


def verify(candidate, do_tamper_challenge=True):
    errors = []
    cases = reconstruct_cases(fixture)
    if candidate.get('experiment') != 'V39_ADAPTER_EDGE_CARDINALITY_A01': errors.append('wrong experiment id')
    if candidate.get('source_commit') != '64c48e95425972bc04e61a41d219686c789cb6b6': errors.append('wrong exact source commit')
    if candidate.get('source_sha256') != hashlib.sha256(source_bytes).hexdigest(): errors.append('source digest mismatch')
    if candidate.get('fixture_sha256') != hashlib.sha256(fixture_bytes).hexdigest(): errors.append('fixture digest mismatch')
    expected_fixture_sha = 'ad0b1c29da4b626e9be27e8716cdabfbb25ac49dcf0abd4bda4bd2f7a9f84e4e'
    if hashlib.sha256(fixture_bytes).hexdigest() != expected_fixture_sha: errors.append('unexpected retained A01 raw')
    for name, events in cases.items():
        down_count = sum(row.get('event') == 'input_admission' for row in events)
        up_count = sum(row.get('event') == 'input_release_measurement' for row in events)
        expected_status = 'adapter_edge_brackets_paired' if (down_count, up_count) == (1, 1) else 'adapter_edge_receipt_incomplete'
        case = candidate.get('cases', {}).get(name)
        if type(case) is not dict:
            errors.append(f'{name}: missing result'); continue
        observed_counts = case.get('event_counts', {})
        if (observed_counts.get('input_admission'), observed_counts.get('input_release_measurement')) != (down_count, up_count):
            errors.append(f'{name}: reported counts disagree with independently reconstructed inputs')
        if case.get('receipt_count') != 1 or type(case.get('receipts')) is not list or len(case['receipts']) != 1:
            errors.append(f'{name}: not exactly one grouped receipt'); continue
        receipt = case['receipts'][0]
        if receipt.get('status') != expected_status: errors.append(f'{name}: expected {expected_status}, got {receipt.get("status")}')
        intervals = (receipt.get('down_edge_interval_ns'), receipt.get('up_edge_interval_ns'))
        if expected_status == 'adapter_edge_brackets_paired':
            raw_down = events[0]['physical_key_measurement']['adapter_edge']['interval']
            raw_up = events[1]['physical_key_measurement']['adapter_edge']['interval']
            if intervals != (raw_down, raw_up): errors.append(f'{name}: paired endpoints differ from retained raw')
        elif intervals != (None, None):
            errors.append(f'{name}: duplicate evidence exposed an interval')
        if receipt.get('grants_input_authority') is True or receipt.get('application_consumption_observed') is True:
            errors.append(f'{name}: receipt made unsupported authority/consumption claim')
        if 'intent-v39-a01' in json.dumps(case): errors.append(f'{name}: raw intent token leaked')
        if name not in candidate.get('weakened_cardinality_mutation_control', {}):
            errors.append(f'{name}: weakened guard control missing')
    weak = candidate.get('weakened_cardinality_mutation_control', {})
    for name, events in cases.items():
        case = weak.get(name)
        expected_count = (sum(r.get('event') == 'input_admission' for r in events), sum(r.get('event') == 'input_release_measurement' for r in events))
        if type(case) is not dict or case.get('receipt_count') != 1 or type(case.get('receipts')) is not list or len(case['receipts']) != 1:
            errors.append(f'{name}: weakened control missing one receipt'); continue
        expected_weak_status = 'adapter_edge_brackets_paired' if min(expected_count) >= 1 else 'adapter_edge_receipt_incomplete'
        if case['receipts'][0].get('status') != expected_weak_status:
            errors.append(f'{name}: weakened guard did not demonstrate expected sensitivity')

    tampered = copy.deepcopy(candidate)
    duplicate = tampered['cases']['duplicate_down_identical']['receipts'][0]
    duplicate['status'] = 'adapter_edge_brackets_paired'
    duplicate['down_edge_interval_ns'] = candidate['cases']['baseline_unique_pair']['receipts'][0]['down_edge_interval_ns']
    duplicate['up_edge_interval_ns'] = candidate['cases']['baseline_unique_pair']['receipts'][0]['up_edge_interval_ns']
    if do_tamper_challenge:
        tamper_detected = any('duplicate_down_identical:' in error for error in verify(tampered, do_tamper_challenge=False))
        if not tamper_detected: errors.append('auditor sensitivity: coherent paired-duplicate corruption escaped')
    return errors

errors = verify(result)
resource = json.loads(Path('/evidence/candidate.json').read_text(encoding='utf-8')).get('resource_snapshot', {})
report = {
    'audit': 'PASS' if not errors else 'FAIL',
    'checks': 66,
    'errors': errors,
    'independence': 'Reconstructs each six-row treatment directly from the frozen A01 raw fixture; derives expected cardinality/status, checks baseline timing against the raw edge intervals, and tests detection of coherent duplicate-pair corruption.',
    'tamper_control': 'PASS' if not any('sensitivity' in error for error in errors) else 'FAIL',
    'candidate_sha256': hashlib.sha256(candidate_bytes).hexdigest(),
    'source_sha256': hashlib.sha256(source_bytes).hexdigest(),
    'fixture_sha256': hashlib.sha256(fixture_bytes).hexdigest(),
    'resource_snapshot': resource,
    'limitations': ['one synthetic A01 fixture; no live X-server key state, application consumption, game/task effect, model, GUI, or input']
}
Path('/audit-v2/audit.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))
raise SystemExit(0 if not errors else 1)
