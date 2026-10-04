"""Independent raw-artifact audit; does not import the candidate adapter."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT.parent
RUN = ROOT / 'results' / 'a03'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    freeze = json.loads((ROOT / 'FREEZE.json').read_text(encoding='utf-8'))
    result = json.loads((RUN / 'result.json').read_text(encoding='utf-8'))
    controls = json.loads((RUN / 'controls.json').read_text(encoding='utf-8'))
    summary = json.loads((ROOT / 'RESULT.json').read_text(encoding='utf-8'))
    source = PACKAGE / 'adapter.py'
    assert sha(source) == freeze['candidate_adapter_sha256']
    assert sha(PACKAGE / 'v39_bridge_events.jsonl') == freeze['base']['bridge_events_sha256']
    for name, record in freeze['candidate_sources'].items():
        path = ROOT / name if name != 'adapter.py' and name != 'test_bridge_composition.py' else PACKAGE / name
        assert sha(path) == record['sha256']
    for line in (PACKAGE / 'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        expected, relative = line.split('  ', 1)
        assert sha(PACKAGE / relative) == expected
    rows = [json.loads(line) for line in (RUN / 'input-events.jsonl').read_text(encoding='utf-8').splitlines() if line]
    assert len(rows) == 2
    down, up = rows
    down_edge = down['physical_key_measurement']['adapter_edge']
    up_edge = up['physical_key_measurement']['adapter_edge']
    assert down_edge['status'] == 'CONFIRMED_PHYSICAL_DOWN'
    assert up_edge['status'] == 'CONFIRMED_PHYSICAL_UP'
    assert down_edge['actuation_id'] == up_edge['actuation_id']
    guaranteed = [down_edge['interval'][1], up_edge['interval'][0]]
    attribution = result['attributions'][0]
    assert result['counts']['key_release_receipts'] == 1
    assert result['counts']['unverified_or_censored_key_intervals'] == 0
    assert attribution['status'] == 'TEMPORALLY_UNIQUE'
    assert attribution['detection_interval_ns'][0] >= guaranteed[0]
    assert attribution['detection_interval_ns'][1] <= guaranteed[1]
    assert attribution['intent_token'] == down['intent_token']
    assert attribution['causal_attribution'] == 'NOT_ESTABLISHED'
    assert all(value['attributions'][0]['status'] != 'TEMPORALLY_UNIQUE' for value in controls.values())
    assert summary['detection_interval_ns'] == attribution['detection_interval_ns']
    assert summary['guaranteed_held_interval_ns'] == guaranteed
    assert summary['controls'] == {key: value['attributions'][0]['status'] for key, value in controls.items()}
    print(json.dumps({'audit':'PASS_SCOPED_BRIDGE_COMPOSITION', 'errors':[],
                      'guaranteed_held_ns':guaranteed,
                      'attribution':attribution,
                      'controls':{k:v['attributions'][0]['status'] for k,v in controls.items()}},
                     indent=2, sort_keys=True))

if __name__ == '__main__': main()
