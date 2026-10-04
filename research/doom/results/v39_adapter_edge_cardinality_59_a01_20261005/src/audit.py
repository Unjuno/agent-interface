import hashlib
import json
from pathlib import Path
raw_path = Path('/src/candidate-events.jsonl')
source_path = Path('/src/map01_overlap_controller_v39.py')
fixture_bytes = raw_path.read_bytes()
fixture = [json.loads(line) for line in fixture_bytes.decode('utf-8').splitlines() if line]
result = json.loads(Path('/candidate/candidate.json').read_text(encoding='utf-8'))
errors = []
checks = 0
def check(condition, message):
    global checks
    checks += 1
    if not condition: errors.append(message)
check(result.get('experiment') == 'V39_ADAPTER_EDGE_CARDINALITY_A01', 'wrong experiment id')
check(result.get('source_commit') == '64c48e95425972bc04e61a41d219686c789cb6b6', 'wrong source commit')
check(result.get('source_sha256') == hashlib.sha256(source_path.read_bytes()).hexdigest(), 'source hash mismatch')
check(result.get('fixture_sha256') == hashlib.sha256(fixture_bytes).hexdigest(), 'fixture hash mismatch')
check(hashlib.sha256(fixture_bytes).hexdigest() == 'ad0b1c29da4b626e9be27e8716cdabfbb25ac49dcf0abd4bda4bd2f7a9f84e4e', 'unexpected retained raw fixture')
base_down = [row for row in fixture if row.get('event') == 'input_admission']
base_up = [row for row in fixture if row.get('event') == 'input_release_measurement']
check((len(base_down), len(base_up)) == (1, 1), 'fixture does not contain exactly one DOWN and one UP')
expected = {
    'baseline_unique_pair': (1, 1, 'adapter_edge_brackets_paired'),
    'duplicate_down_identical': (2, 1, 'adapter_edge_receipt_incomplete'),
    'duplicate_up_identical': (1, 2, 'adapter_edge_receipt_incomplete'),
    'duplicate_both_identical': (2, 2, 'adapter_edge_receipt_incomplete'),
    'duplicate_down_conflicting': (2, 1, 'adapter_edge_receipt_incomplete'),
    'duplicate_up_conflicting': (1, 2, 'adapter_edge_receipt_incomplete'),
}
for name, (down_count, up_count, status) in expected.items():
    case = result.get('cases', {}).get(name)
    check(type(case) is dict, f'{name}: missing case')
    if type(case) is not dict: continue
    counts = case.get('event_counts', {})
    check((counts.get('input_admission'), counts.get('input_release_measurement')) == (down_count, up_count), f'{name}: wrong reconstructed cardinality')
    receipts = case.get('receipts')
    check(case.get('receipt_count') == 1 and type(receipts) is list and len(receipts) == 1, f'{name}: expected one grouped receipt')
    if type(receipts) is not list or len(receipts) != 1: continue
    receipt = receipts[0]
    check(receipt.get('status') == status, f'{name}: unexpected status {receipt.get("status")}')
    intervals = (receipt.get('down_edge_interval_ns'), receipt.get('up_edge_interval_ns'))
    if status == 'adapter_edge_brackets_paired':
        check(all(type(value) is list and len(value) == 2 for value in intervals), f'{name}: unique baseline missing intervals')
    else:
        check(intervals == (None, None), f'{name}: ambiguous case exposed intervals')
    check(receipt.get('grants_input_authority') is not True and receipt.get('application_consumption_observed') is not True, f'{name}: claimed authority or application consumption')
    check('intent-v39-a01' not in json.dumps(receipts), f'{name}: leaked raw intent token')
for name in expected:
    case = result.get('weakened_cardinality_mutation_control', {}).get(name)
    check(type(case) is dict, f'{name}: missing weakened-guard control')
    if type(case) is not dict: continue
    receipts = case.get('receipts')
    want = 'adapter_edge_brackets_paired' if name == 'baseline_unique_pair' or name.startswith('duplicate_') else None
    check(type(receipts) is list and len(receipts) == 1 and receipts[0].get('status') == want, f'{name}: weakened-guard sensitivity mismatch')
report = {'audit': 'PASS' if not errors else 'FAIL', 'checks': checks, 'errors': errors,
          'limitations': ['independent output/cardinality audit; model-free, GUI-free, no OS input or game/task effect'],
          'mutation_control': 'weakened exact-one cardinality guard must pair duplicate cases (demonstrates test sensitivity)'}
Path('/audit/audit.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))
raise SystemExit(0 if not errors else 1)
