#!/usr/bin/env python3
"""Read-only, postmeasurement numerical replay; NOT a full input/PNG audit."""
import argparse
import base64
import hashlib
import json
import lzma
import math
from pathlib import Path

EXPECTED = 'ecdbf124acb8b1e0a47825859f5c81645d99e3cc4db9ac9b750265024efdf6cc'


def replay(path):
    raw = lzma.decompress(base64.b64decode(path.read_bytes().strip(), validate=True))
    if hashlib.sha256(raw).hexdigest() != EXPECTED:
        raise ValueError('retained evidence digest mismatch')
    data = json.loads(raw)
    rows = data['numeric_cases']
    if len(rows) != 16 or {r['case']['id'] for r in rows} != {f'case-{i:02d}' for i in range(16)}:
        raise ValueError('case allocation mismatch')
    rebuilt = []
    for r in rows:
        source = float.fromhex(r['source_yaw_hex'])
        end = float.fromhex(r['terminal_yaw_hex'])
        if not (math.isfinite(source) and math.isfinite(end)):
            raise ValueError('nonfinite yaw')
        error = abs((end - source + 180.0) % 360.0 - 180.0)
        events = r['correction_events']
        if len(events) > 6 or any(e['keys'] != ['Left'] or e['requested_seconds'] != .09 for e in events):
            raise ValueError('correction subset/budget mismatch')
        rebuilt.append(dict(r['case'], outcome=r['outcome'], pulses=len(events),
                            goal=error <= 6.0, yaw_error_deg=error))
    main = [r for r in rebuilt if r['kind'] == 'main']
    cand = [r for r in main if r['arm'] == 'pixel_stop']
    base = [r for r in main if r['arm'] == 'fixed']
    controls = [r for r in rebuilt if r['kind'] != 'main']
    if len(cand) != 6 or len(base) != 6 or len(controls) != 4:
        raise ValueError('stratum allocation mismatch')
    gates = dict(candidate_goal=sum(r['goal'] for r in cand),
                 nominal_baseline_goal=sum(r['goal'] for r in base if r['perturb'] == 6),
                 lower_baseline_misses=sum(not r['goal'] for r in base if r['perturb'] < 6),
                 lower_candidate_early=sum(r['pulses'] < 6 for r in cand if r['perturb'] < 6),
                 false_matched=[r['id'] for r in cand if r['outcome'] == 'MATCHED' and not r['goal']],
                 controls=all(r['pulses'] == 0 and r['goal'] and r['outcome'] ==
                              ('MATCHED' if r['kind'] == 'aligned' else 'UNKNOWN') for r in controls))
    if gates != data['frozen_result']['gates']:
        raise ValueError('recomputed gates contradict frozen result')
    by_id = {r['id']: r for r in data['frozen_result']['cases']}
    for r in rebuilt:
        old = by_id[r['id']]
        for key in ('outcome', 'pulses', 'goal', 'yaw_error_deg'):
            if r[key] != old[key]:
                raise ValueError(f'case result mismatch: {r["id"]} {key}')
    decision = 'HOLD_TARGET_NOT_REACHED' if gates['candidate_goal'] < 6 else 'CHECK_OTHER_GATES'
    if decision != data['frozen_result']['decision']:
        raise ValueError('decision mismatch')
    return data, dict(numerical_replay='PASS', decision=decision, gates=gates,
                      main_candidate_matched=sum(r['outcome'] == 'MATCHED' for r in cand),
                      full_input_image_audit='NOT_PERFORMED_BY_THIS_HELPER')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--extract', type=Path, help='new directory for exact report and lossless parsed result values')
    args = parser.parse_args()
    data, result = replay(Path(__file__).with_name('evidence.json.xz.b64'))
    if args.extract is not None:
        args.extract.mkdir(parents=True, exist_ok=False)
        (args.extract / 'REPORT.md').write_text(data['full_report'], encoding='utf-8')
        (args.extract / 'RESULT.values.json').write_text(json.dumps(data['frozen_result'], indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
