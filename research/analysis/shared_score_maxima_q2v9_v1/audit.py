"""Raw-only exact crossing-point auditor; imports no candidate/runner/corpus."""
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import sys


def crossing_oracle(case):
    a, b, e = [[Q(x) for x in case[k]] for k in ('a', 'b', 'e')]
    lo, hi = map(Q, case['domain'])
    n = len(a)
    intervals = []
    for winner in range(n):
        intercept = [a[j] + (e[j] if j == winner else -e[j]) for j in range(n)]
        events = {lo, hi}
        for j in range(n):
            for k in range(j):
                if b[j] != b[k]:
                    t = (intercept[k]-intercept[j])/(b[j]-b[k])
                    if lo <= t <= hi:
                        events.add(t)
        good = []
        for t in sorted(events):
            values = [intercept[j]+b[j]*t for j in range(n)]
            if values[winner] == max(values):
                good.append(t)
        intervals.append([str(min(good)), str(max(good))] if good else None)
    joint = [i for i, interval in enumerate(intervals) if interval is not None]
    endpoints = [[a[j]+b[j]*t for t in (lo, hi)] for j in range(n)]
    lower = [min(endpoints[j])-e[j] for j in range(n)]
    upper = [max(endpoints[j])+e[j] for j in range(n)]
    box = [i for i in range(n) if all(upper[i] >= lower[j] for j in range(n))]
    pairwise = [i for i in range(n) if all(any(
        a[i]+b[i]*t+e[i] >= a[j]+b[j]*t-e[j] for t in (lo, hi)) for j in range(n))]
    return {'box': box, 'pairwise': pairwise, 'joint': joint, 'intervals': intervals,
            'action_authority': False, 'task_success': None}


def audit(data, process, expected_input_hash, expected_freeze_hash):
    errors, checks = [], 0
    def require(condition, description):
        nonlocal checks
        checks += 1
        if not condition:
            errors.append(description)
    require(data.get('allocation') == 'shared-score-q2v9-01', 'allocation')
    require(data.get('freeze_sha256') == expected_freeze_hash, 'freeze')
    require(process.get('returncode') == 0 and process.get('timeout') is False, 'process_exit')
    require(process.get('stderr_bytes') == 0, 'stderr')
    require(data.get('pid') == process.get('pid'), 'process_identity')
    require(process.get('end_utc_ns', 0) >= process.get('start_utc_ns', 1), 'process_clock')
    rows = data.get('rows', [])
    require(len(rows) == 1470, 'coverage')
    inputs = [row['input'] for row in rows]
    input_bytes = (json.dumps(inputs, sort_keys=True, separators=(',', ':'))+'\n').encode()
    require(hashlib.sha256(input_bytes).hexdigest() == expected_input_hash, 'input_identity')
    require(len({c['id'] for c in inputs}) == len(inputs), 'unique_case_ids')
    narrowed_box = narrowed_pairwise = box_sum = pairwise_sum = joint_sum = 0
    named = {}
    for row in rows:
        case, output = row['input'], row['output']
        key = case['id']
        reference = crossing_oracle(case)
        require(output == reference, key+':exact_oracle')
        require(output.get('action_authority') is False and output.get('task_success') is None, key+':role')
        require(bool(output['joint']), key+':nonempty')
        require(set(output['joint']) <= set(output['pairwise']) <= set(output['box']), key+':containment')
        for i, span in enumerate(output['intervals']):
            if span is not None:
                t = (Q(span[0])+Q(span[1]))/2
                a, b, e = [[Q(v) for v in case[k]] for k in ('a','b','e')]
                values = [a[j]+b[j]*t+(e[j] if i == j else -e[j]) for j in range(len(a))]
                require(values[i] == max(values), key+':witness:'+str(i))
        narrowed_box += len(output['joint']) < len(output['box'])
        narrowed_pairwise += len(output['joint']) < len(output['pairwise'])
        box_sum += len(output['box']); pairwise_sum += len(output['pairwise']); joint_sum += len(output['joint'])
        if not key.startswith('g'):
            named[key] = output
    require(named.get('common_offset', {}).get('joint') == [0], 'common_mode_positive')
    require(named.get('common_offset', {}).get('box') == [0,1,2], 'common_mode_discriminator')
    require(named.get('incompatible_pairs', {}).get('joint') == [1,2], 'joint_witness_discriminator')
    require(named.get('incompatible_pairs', {}).get('pairwise') == [0,1,2], 'pairwise_discriminator')
    require(named.get('interior_singleton', {}).get('intervals', [None])[0] == ['0','0'], 'singleton_preserved')
    return {'decision': 'PASS_SHARED_SCORE_MAXIMA_CONTRACT' if not errors else 'FAIL_OR_HOLD',
            'checks': checks, 'errors': errors, 'records': len(rows),
            'narrowed_vs_box': narrowed_box, 'narrowed_vs_pairwise': narrowed_pairwise,
            'memberships': {'box': box_sum, 'pairwise': pairwise_sum, 'joint': joint_sum},
            'directed': named}


def load(root):
    raw = (root/'records.json').read_bytes()
    data = json.loads(raw)
    process = json.loads((root/'PROCESS.json').read_text())
    if hashlib.sha256(raw).hexdigest() != process['stdout_sha256']:
        raise ValueError('raw output identity')
    return data, process


if __name__ == '__main__':
    base = Path(__file__).resolve().parent
    freeze_bytes = (base/'FREEZE.json').read_bytes()
    freeze = json.loads(freeze_bytes)
    data, process = load(base/sys.argv[1])
    result = audit(data, process, freeze['corpus_sha256'], hashlib.sha256(freeze_bytes).hexdigest())
    print(json.dumps(result, sort_keys=True, indent=2))
    raise SystemExit(1 if result['errors'] else 0)
