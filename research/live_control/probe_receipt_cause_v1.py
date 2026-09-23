"""Offline mutation of an internally consistent completed report; not live evidence."""
import copy
import json
from pathlib import Path
from decision_receipt_v3 import build
from report_pages_v2 import digest

HERE = Path(__file__).resolve().parent
out = HERE / 'results/receipt-cause-01'
out.mkdir(exist_ok=False)
source = HERE / 'results/cause-live-02/recover/report.json'
original = json.loads(source.read_bytes())
cases = []
for kind in ('normal', 'interruption', 'decision_reason'):
    report = copy.deepcopy(original)
    terminal = report['terminal']
    if kind == 'interruption':
        terminal['interruption'] = {'intent_token': 'synthetic', 'record': {'reason': 'focus_changed', 'verified': True}}
    if kind == 'decision_reason':
        terminal['decision_reason'] = 'synthetic reason'
    # Keep every report terminal copy consistent so binding alone cannot detect it.
    report['exchanges'][1]['reply']['records'][-1] = copy.deepcopy(terminal)
    report['last_reply']['records'][-1] = copy.deepcopy(terminal)
    report['continuation_batch']['records'][-1] = copy.deepcopy(terminal)
    receipt = build(json.dumps(report).encode())
    assert receipt['program_binding'] is not None
    assert receipt['detail_review_required'] == (kind != 'normal')
    cases.append({'kind': kind, 'attention': receipt['attention']})
result = {'success': True, 'cases': cases, 'source_sha256': digest(source.read_bytes()),
          'sources': {n: digest((HERE / n).read_bytes()) for n in ['probe_receipt_cause_v1.py', 'decision_receipt_v3.py']},
          'scope': 'offline mutated terminal copies, not actual completed-with-cause app execution'}
(out / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
