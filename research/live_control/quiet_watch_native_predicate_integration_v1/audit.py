#!/usr/bin/env python3
"""Independent audit for quiet_watch_native_predicate_integration_v1."""
import argparse, base64, hashlib, json, statistics
from pathlib import Path

TARGET = bytes((50, 50, 220))
THRESHOLD = 512
EXPECTED_CASES = 38


def sha256(b): return hashlib.sha256(b).hexdigest()
def count(raw):
    if len(raw) != 4096: raise ValueError(len(raw))
    n = 0
    for i in range(0, 4096, 4):
        if raw[i] == 50 and raw[i+1] == 50 and raw[i+2] == 220:
            n += 1
    return n

def case_metrics(r):
    ms = r['observation_metrics']
    wall_ms = sum(m['count_end_ns'] - m['start_ns'] for m in ms) / 1e6
    cpu_ms = sum(m['total_thread_cpu_ns'] for m in ms) / 1e6
    count_wall_ms = sum(m['count_end_ns'] - m['count_start_ns'] for m in ms) / 1e6
    count_cpu_ms = sum(m['count_thread_cpu_ns'] for m in ms) / 1e6
    gaps = [(b['start_ns'] - a['count_end_ns']) / 1e6 for a,b in zip(ms, ms[1:])]
    return {
        'observation_wall_ms': wall_ms,
        'observation_thread_cpu_ms': cpu_ms,
        'count_wall_ms': count_wall_ms,
        'count_thread_cpu_ms': count_cpu_ms,
        'max_count_end_to_next_start_gap_ms': max(gaps) if gaps else 0.0,
        'sample_count': len(ms),
    }

def audit(raw_path, prereg_path):
    raw = json.loads(Path(raw_path).read_text())
    prereg = json.loads(Path(prereg_path).read_text())
    checks = {}
    checks['schema'] = raw.get('schema') == 'quiet_watch_native_predicate_integration_v1' and raw.get('mode') == 'formal'
    checks['no_runner_errors'] = raw.get('errors') == []
    checks['source_hashes'] = raw.get('sources') == prereg.get('sources')
    checks['binary_hashes'] = (
        raw['environment']['native_acquire_binary_sha256'] == prereg['binaries']['native_acquire.so'] and
        raw['environment']['native_predicate_binary_sha256'] == prereg['binaries']['native_predicate.so'])
    checks['prereg_hash'] = raw.get('prereg_sha256') == sha256(Path(prereg_path).read_bytes())
    records = raw.get('records', [])
    checks['case_count'] = len(records) == EXPECTED_CASES
    checks['schedule_identity'] = [r['case'] for r in records] == prereg['schedule']
    semantics = True; integrity = True
    for r in records:
        payloads = r['pixel_payloads']
        for dig, b64 in payloads.items():
            rb = base64.b64decode(b64)
            if sha256(rb) != dig or len(rb) != 4096:
                semantics = False
        if len(r['acquisitions']) != len(r['observation_metrics']): semantics = False
        for a,m in zip(r['acquisitions'], r['observation_metrics']):
            try: rb = base64.b64decode(payloads[a['digest']])
            except Exception: semantics = False; continue
            if count(rb) != a['match_count']: semantics = False
            if a['start_ns'] != m['start_ns'] or a['end_ns'] != m['acquire_end_ns']: semantics = False
            if not (m['start_ns'] <= m['acquire_end_ns'] <= m['count_start_ns'] <= m['count_end_ns']): semantics = False
            if m['total_thread_cpu_ns'] < 0 or m['count_thread_cpu_ns'] < 0 or m['acquire_thread_cpu_ns'] < 0: semantics = False
        f = r['final']; fm = r['final_observation_metrics']
        try: fr = base64.b64decode(payloads[f['digest']])
        except Exception: semantics = False; fr = b''
        if fr and count(fr) != f['match_count']: semantics = False
        if f['start_ns'] != fm['start_ns'] or f['end_ns'] != fm['acquire_end_ns']: semantics = False
        kinds = [e['kind'] for e in r['events']]
        if not (r['owner'].get('verified_empty') and not r['right_down_final'] and kinds == ['app_key_press','app_key_release'] and f['match_count'] == 0 and not r['thread_errors']):
            integrity = False
    checks['pixel_semantics_and_timing_brackets'] = semantics
    checks['input_integrity'] = integrity

    arms = {}
    for arm in ('python_count','native_count'):
        rs = [r for r in records if r['case']['count_backend'] == arm]
        tar = [r for r in rs if r['case']['kind'] == 'target']
        nui = [r for r in rs if r['case']['kind'] == 'nuisance']
        arms[arm] = {
            'target_detected': sum(bool(r['derived']['detected']) for r in tar),
            'target_total': len(tar),
            'nuisance_false_cancel': sum(bool(r['derived']['detected']) for r in nui),
            'nuisance_total': len(nui),
            'nuisance_metrics': {r['case']['pair_id']: case_metrics(r) for r in nui},
        }
    pairs = sorted(set(arms['python_count']['nuisance_metrics']) & set(arms['native_count']['nuisance_metrics']))
    ratios = {'thread_cpu': [], 'wall': [], 'max_gap': []}
    for p in pairs:
        b = arms['python_count']['nuisance_metrics'][p]
        c = arms['native_count']['nuisance_metrics'][p]
        ratios['thread_cpu'].append(c['observation_thread_cpu_ms'] / b['observation_thread_cpu_ms'])
        ratios['wall'].append(c['observation_wall_ms'] / b['observation_wall_ms'])
        ratios['max_gap'].append(c['max_count_end_to_next_start_gap_ms'] / b['max_count_end_to_next_start_gap_ms'])
    summary = {
        'arms': arms,
        'paired_ratios': ratios,
        'median_paired_thread_cpu_ratio': statistics.median(ratios['thread_cpu']),
        'median_paired_wall_ratio': statistics.median(ratios['wall']),
        'median_paired_max_gap_ratio': statistics.median(ratios['max_gap']),
    }
    correctness = (
        arms['python_count']['target_detected'] == 15 and arms['native_count']['target_detected'] == 15 and
        arms['python_count']['nuisance_false_cancel'] == 0 and arms['native_count']['nuisance_false_cancel'] == 0)
    checks['detection_and_false_cancel'] = correctness
    safety = all(checks.values())
    if not safety:
        decision = 'FAIL_SEMANTICS_OR_SAFETY'
    elif (summary['median_paired_thread_cpu_ratio'] <= prereg['gates']['thread_cpu_ratio_max'] and
          summary['median_paired_wall_ratio'] <= prereg['gates']['wall_ratio_max'] and
          summary['median_paired_max_gap_ratio'] <= prereg['gates']['max_gap_ratio_max']):
        decision = 'PASS_INTEGRATION_SCOPED'
    else:
        decision = 'HOLD_INTEGRATION_COST'
    expected = prereg['decision_labels']
    checks['decision_label_known'] = decision in expected
    return {'schema':'quiet_watch_native_predicate_integration_v1_audit','checks':checks,'pass':all(checks.values()),'summary':summary,'decision':decision}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--raw',required=True); ap.add_argument('--prereg',required=True); ap.add_argument('--out',required=True); args=ap.parse_args()
    result=audit(args.raw,args.prereg)
    Path(args.out).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))
    if not result['pass']: raise SystemExit(2)
if __name__=='__main__': main()
