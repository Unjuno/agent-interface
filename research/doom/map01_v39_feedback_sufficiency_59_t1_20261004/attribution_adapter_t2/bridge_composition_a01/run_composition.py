"""One-shot composition of merged v39 bridge rows with the T2 scorer adapter."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT.parent
sys.path.insert(0, str(PACKAGE))
from adapter import adapt_session_records
from independent_progress_clock_v2 import ProgressClock, ProgressSample
OUT = ROOT / 'results' / 'a03'
INPUT = PACKAGE / 'v39_bridge_events.jsonl'


def scorer(rows):
    down = rows[0]['physical_key_measurement']['adapter_edge']
    up = rows[1]['physical_key_measurement']['adapter_edge'] if len(rows) > 1 else None
    lower = down['interval'][1]
    upper = up['interval'][0] if up else lower + 1000
    midpoint = lower + (upper - lower) // 2
    samples = []
    events = []
    clock = ProgressClock()
    for timestamp, kills in ((lower, 0), (midpoint, 1)):
        payload = ProgressSample(timestamp, kills, 0, False, False, False)
        events.extend(clock.ingest(payload))
        samples.append({
            'scheduled_ns': timestamp, 'sample_started_ns': timestamp,
            'sample_finished_ns': timestamp, 'start_lateness_ns': 0,
            'missed_periods_before': 0, 'payload': payload.as_dict(),
            'controller_visible': False,
        })
    return samples, events


def evaluate(rows):
    samples, events = scorer(rows)
    return adapt_session_records(samples, events, rows), samples, events


def main():
    if OUT.exists():
        raise FileExistsError(f'refusing to overwrite {OUT}')
    rows = [json.loads(line) for line in INPUT.read_text(encoding='utf-8').splitlines() if line]
    result, samples, events = evaluate(rows)
    controls = {}
    altered = json.loads(json.dumps(rows))
    altered[1]['physical_key_measurement']['adapter_edge']['actuation_id'] += ':foreign'
    controls['mismatched_actuation'] = evaluate(altered)[0]
    altered = json.loads(json.dumps(rows))
    altered[1]['physical_key_measurement']['adapter_edge']['status'] = 'UNRESOLVED'
    controls['unconfirmed_up'] = evaluate(altered)[0]
    controls['missing_up'] = evaluate(rows[:1])[0]
    OUT.mkdir(parents=True)
    (OUT / 'input-events.jsonl').write_bytes(INPUT.read_bytes())
    (OUT / 'scorer-samples.json').write_text(json.dumps(samples, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    (OUT / 'scorer-events.json').write_text(json.dumps(events, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    (OUT / 'result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    (OUT / 'controls.json').write_text(json.dumps(controls, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({'disposition': result['trace_integrity'], 'counts': result['counts'],
                      'attribution': result['attributions'][0],
                      'controls': {k: v['attributions'][0]['status'] for k, v in controls.items()}},
                     sort_keys=True, indent=2))

if __name__ == '__main__':
    main()
