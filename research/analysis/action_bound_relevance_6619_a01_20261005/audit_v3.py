"""Independent raw reconstruction and mutation checks; does not import candidate.py."""
import copy
import hashlib
import json
import sys
from pathlib import Path


def frame_delta(case):
    a, b = case.get('before'), case.get('current')
    if not isinstance(a, str) or not isinstance(b, str) or len(a) != len(b):
        return None
    return [offset for offset in range(len(a)) if a[offset] != b[offset]]


def receipt_matches(case):
    r = case['receipt']; p = case['prediction']
    fields = ('action_id', 'source_epoch', 'viewport_generation')
    return r.get('acknowledged') is True and all(r.get(k) == p.get(k) for k in fields)


def mismatch_errors(public_doc, oracle_doc, raw_doc):
    errors = []
    cases = public_doc['cases']; results = raw_doc.get('results')
    labels = {x['id']: x for x in oracle_doc['labels']}
    if not isinstance(results, list) or len(results) != len(cases):
        return ['result cardinality mismatch']
    for case, result in zip(cases, results):
        cid = case['id']; label = labels[cid]; delta = frame_delta(case)
        if result.get('id') != cid: errors.append(f'{cid}: id mismatch')
        # The scorer-only axis must never be copied into the candidate raw.
        forbidden = {'scorer_origin', 'task_relevance', 'hard_critical', 'oracle_label'}
        if forbidden.intersection(result): errors.append(f'{cid}: scorer-label leakage')
        if result.get('origin_claim') != 'UNATTRIBUTED': errors.append(f'{cid}: unjustified origin attribution')
        valid = receipt_matches(case)
        pred = case['prediction']
        matched = (delta is not None and pred.get('uncertainty_pixels') == 0
                   and delta == pred.get('expected_changed_pixels'))
        required = set(label['required_pixels']) | set(label['critical_pixels'])
        public_required = set(case['contract'].get('required_pixels', []))
        public_critical = set(case['contract'].get('critical_pixels', []))
        if required != public_required | public_critical:
            errors.append(f'{cid}: public obligation/oracle mismatch')
        obligated = bool(required.intersection(delta or []))
        expected_gate = ('FORWARD_FULL_CURRENT' if not valid
                         or case['contract'].get('coverage') != 'PROVEN_COMPLETE'
                         else 'FORWARD' if (set(case['contract'].get('required_pixels', []))
                                            | set(case['contract'].get('critical_pixels', []))) & set(delta or [])
                         else 'SUPPRESS')
        expected = {
            'changed_pixels': delta,
            'receipt_valid': valid,
            'prediction_matches': matched,
            'full_frame': delta or [],
            'prediction_only': [] if valid and matched else (delta or []),
            'complete_relevance': ((delta or []) if expected_gate != 'SUPPRESS' else []),
            'complete_decision': expected_gate,
        }
        for key in ('changed_pixels', 'receipt_valid', 'prediction_matches'):
            if result.get(key) != expected[key]: errors.append(f'{cid}: {key} reconstruction mismatch')
        for arm in ('full_frame', 'prediction_only', 'complete_relevance'):
            arm_result = result.get(arm, {})
            if arm_result.get('forwarded_pixels') != expected[arm]: errors.append(f'{cid}: {arm} decision mismatch')
            if arm_result.get('delivery_tick') != case['decision_tick']:
                errors.append(f'{cid}: {arm} delivery tick mismatch')
        if result.get('complete_relevance', {}).get('decision') != expected['complete_decision']:
            errors.append(f'{cid}: #1726 COMPLETE_ONLY decision mismatch')
        expected_prediction_decision = ('SUPPRESS' if valid and matched else
                                         'FORWARD' if delta else 'NO_CHANGE')
        if result.get('prediction_only', {}).get('decision') != expected_prediction_decision:
            errors.append(f'{cid}: prediction-only disposition mismatch')
        for arm in ('full_frame', 'prediction_only', 'complete_relevance'):
            forwarded = set(result.get(arm, {}).get('forwarded_pixels') or [])
            mandatory = set(label['required_pixels']) | set(label['critical_pixels'])
            if arm != 'prediction_only' and mandatory.intersection(delta or []) and not mandatory.intersection(forwarded):
                errors.append(f'{cid}: {arm} missed required or critical cue')
            if mandatory.intersection(delta or []) and result.get(arm, {}).get('delivery_tick', 10**9) > case['deadline_tick']:
                errors.append(f'{cid}: {arm} late required delivery')
    return errors


def main():
    if len(sys.argv) != 4:
        raise SystemExit('usage: audit_v2.py PUBLIC_CASES SCORER_ORACLE CANDIDATE_RAW')
    public, oracle, raw_path = map(Path, sys.argv[1:])
    root = Path(__file__).resolve().parent
    freeze = json.loads((root / 'FREEZE.json').read_text())
    pin_errors = []
    for rel, expected_hash in freeze['source_sha256'].items():
        actual_hash = hashlib.sha256((root / rel).read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            pin_errors.append(f'{rel}: source hash mismatch')
    for rel, expected_hash in freeze['repository_context_sha256'].items():
        actual_hash = hashlib.sha256((root.parents[2] / rel).read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            pin_errors.append(f'{rel}: repository context hash mismatch')
    baseline_hash = hashlib.sha256((root / 'sources/observation_relevance_completeness_1726_candidate.py').read_bytes()).hexdigest()
    if baseline_hash != freeze['reference_baseline']['sha256']:
        pin_errors.append('pinned #1726 baseline hash mismatch')
    public_doc = json.loads(public.read_text()); oracle_doc = json.loads(oracle.read_text()); raw = json.loads(raw_path.read_text())
    errors = pin_errors + mismatch_errors(public_doc, oracle_doc, raw)
    mutations = []
    def reject(name, mutate):
        changed = copy.deepcopy(raw); mutate(changed)
        detected = bool(mismatch_errors(public_doc, oracle_doc, changed))
        mutations.append({'name': name, 'rejected': detected})
    indexes = {r['id']: i for i, r in enumerate(raw['results'])}
    reject('drop-required-cue', lambda doc: doc['results'][indexes['self_match1_required']]['complete_relevance'].update(forwarded_pixels=[]))
    reject('forge-self-causation', lambda doc: doc['results'][indexes['external_match1_required']].update(origin_claim='SELF'))
    reject('late-required-delivery', lambda doc: doc['results'][indexes['self_match1_required']]['complete_relevance'].update(delivery_tick=13))
    reject('stale-receipt-still-suppresses', lambda doc: (doc['results'][indexes['unknown_receipt_and_coverage']].update(receipt_valid=False), doc['results'][indexes['unknown_receipt_and_coverage']]['complete_relevance'].update(forwarded_pixels=[])))
    errors += [m['name'] for m in mutations if not m['rejected']]
    labels = {x['id']: x for x in oracle_doc['labels']}
    res = {x['id']: x for x in raw['results']}
    metric = {arm: {'required_or_critical_misses': 0, 'late_required': 0, 'optional_changed_forwarded': 0, 'optional_matched_suppressed': 0}
              for arm in ('full_frame', 'prediction_only', 'complete_relevance')}
    for case in public_doc['cases']:
        label = labels[case['id']]; delta = set(frame_delta(case) or [])
        mandatory = (set(label['required_pixels']) | set(label['critical_pixels'])) & delta
        required = set(label['required_pixels']) & delta
        for arm, item in metric.items():
            forwarded = set(res[case['id']][arm]['forwarded_pixels'])
            if mandatory and not mandatory.issubset(forwarded): item['required_or_critical_misses'] += 1
            if required and res[case['id']][arm]['delivery_tick'] > case['deadline_tick']: item['late_required'] += 1
            if label.get('task_relevance') == 'IRRELEVANT' and delta and forwarded: item['optional_changed_forwarded'] += 1
            if label.get('task_relevance') == 'IRRELEVANT' and delta and not forwarded and res[case['id']]['prediction_matches']: item['optional_matched_suppressed'] += 1
    # Same candidate-visible input under distinct scorer-only origin labels.
    by_id = {c['id']: c for c in public_doc['cases']}
    yoked = []
    for suffix in ('required', 'irrelevant'):
        a=by_id[f'self_match1_{suffix}']; b=by_id[f'external_match1_{suffix}']
        public_equal={k:v for k,v in a.items() if k!='id'} == {k:v for k,v in b.items() if k!='id'}
        outputs_equal=all(res[a['id']][arm]==res[b['id']][arm] for arm in ('full_frame','prediction_only','complete_relevance')) and res[a['id']]['origin_claim']==res[b['id']]['origin_claim']
        scorer_distinct=labels[a['id']]['origin'] != labels[b['id']]['origin']
        yoked.append({'pair':suffix,'public_equal':public_equal,'outputs_equal':outputs_equal,'scorer_origin_distinct':scorer_distinct})
    candidate_leaks_oracle=any(any(k in row for k in ('oracle','task_relevance','hard_critical','scorer_origin')) for row in raw.get('results',[]))
    # The unknown row is checked directly because it is not a mandatory event.
    unknown=res['unknown_receipt_and_coverage']
    unknown_safe=(unknown['receipt_valid'] is False and bool(unknown['complete_relevance']['forwarded_pixels']))
    pass_gate=(not errors and all(x['rejected'] for x in mutations)
        and all(x['public_equal'] and x['outputs_equal'] and x['scorer_origin_distinct'] for x in yoked)
        and not candidate_leaks_oracle and metric['complete_relevance']['required_or_critical_misses']==0
        and metric['complete_relevance']['late_required']==0 and metric['prediction_only']['required_or_critical_misses']>0
        and metric['complete_relevance']['optional_matched_suppressed']>0 and unknown_safe)
    report={'schema':'action-bound-relevance-independent-audit-v3','decision':'PASS_METHOD_SCOPED' if pass_gate else 'FAIL_OR_HOLD_AUDIT','row_count':len(public_doc['cases']),'metrics':metric,'yoked_controls':yoked,'mutation_controls':mutations,'unknown_fallback':unknown_safe,'candidate_oracle_leakage':candidate_leaks_oracle,'errors':errors,'scope':'synthetic deterministic raster method only; no live UI/game/model/input, no suppression safety or task-effect claim'}
    print(json.dumps(report,sort_keys=True,indent=2))
    if pass_gate: return 0
    return 2

if __name__ == '__main__': raise SystemExit(main())
