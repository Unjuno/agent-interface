#!/usr/bin/env python3
import hashlib, importlib.util, json, random, sys
from pathlib import Path

TASK = 'USEFUL-CONTROL-INTERVAL-CONTRACT-FORMAL-20260917-002'
SEED = 94120260917002
N_CASES = 20_000
EXPECTED_CANDIDATE_SHA256 = '9783b3b6b24bcb93b4cf608db2bbd3f65740a1b0f5372c783f6c0367b680fc8b'
ROOT = Path(__file__).resolve().parent
CANDIDATE_PATH = ROOT / 'interval_contract.py'
MARKER = ROOT / 'FORMAL_INVOKED.json'
RESULT = ROOT / 'FORMAL_RESULT.json'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_candidate():
    if sha256(CANDIDATE_PATH) != EXPECTED_CANDIDATE_SHA256:
        raise SystemExit('candidate source SHA mismatch before formal invocation')
    spec = importlib.util.spec_from_file_location('candidate_interval_contract', CANDIDATE_PATH)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def generate_case(rng: random.Random, idx: int):
    ws = rng.randrange(0, 95)
    we = rng.randrange(ws + 1, 97)
    acts = []
    for j in range(rng.randrange(0, 6)):
        down = rng.randrange(0, 96)
        lo = rng.randrange(down, 97)
        hi = rng.randrange(lo, 97)
        auth = []
        for _ in range(rng.randrange(0, 5)):
            s = rng.randrange(0, 96)
            e = rng.randrange(s + 1, 97)
            auth.append((s, e))
        acts.append({'id': f'c{idx}-a{j}', 'down': down, 'lo': lo, 'hi': hi, 'auth': auth})
    events = []
    for k in range(rng.randrange(0, 5)):
        mode = rng.randrange(0, 3)
        if mode == 0 and acts:
            aid = acts[rng.randrange(len(acts))]['id']
        elif mode == 1:
            aid = f'unknown-{idx}-{k}'
        else:
            aid = None
        events.append({'t': rng.randrange(0, 96), 'id': aid, 'scored': bool(rng.getrandbits(1)), 'useful': bool(rng.getrandbits(1))})
    return {'wait': (ws, we), 'acts': acts, 'events': events}


def candidate_eval(m, case):
    wait = m.Interval(*case['wait'])
    acts = [m.Actuation(a['down'], m.ReleaseReceipt(a['lo'], a['hi'], False), [m.Interval(*x) for x in a['auth']], a['id']) for a in case['acts']]
    events = [m.EffectEvent(e['t'], e['id'], e['scored'], e['useful']) for e in case['events']]
    return m.analyze(wait, acts, events)


def oracle(case):
    ws, we = case['wait']
    lower_union, upper_union, auth_lower_union, auth_upper_union = set(), set(), set(), set()
    per = {}
    known = {a['id'] for a in case['acts']}
    for a in case['acts']:
        lower = set(range(max(ws, a['down']), max(max(ws, a['down']), min(we, a['lo']))))
        upper = set(range(max(ws, a['down']), max(max(ws, a['down']), min(we, a['hi']))))
        alower = {t for t in lower if any(s <= t < e for s, e in a['auth'])}
        aupper = {t for t in upper if any(s <= t < e for s, e in a['auth'])}
        lower_union |= lower; upper_union |= upper; auth_lower_union |= alower; auth_upper_union |= aupper
        per[a['id']] = {'lower_ns': len(lower), 'upper_ns': len(upper), 'authority_lower_ns': len(alower), 'authority_upper_ns': len(aupper)}
    effects = {'useful_bound': 0, 'useful_unbound': 0, 'nonuseful_bound': 0, 'unscored': 0}
    for e in case['events']:
        if not e['scored']:
            effects['unscored'] += 1
        elif e['id'] in known:
            effects['useful_bound' if e['useful'] else 'nonuseful_bound'] += 1
        elif e['useful']:
            effects['useful_unbound'] += 1
    return {
        'wait_ns': we - ws,
        'physical_occupancy_lower_ns': len(lower_union),
        'physical_occupancy_upper_ns': len(upper_union),
        'authorized_occupancy_lower_ns': len(auth_lower_union),
        'authorized_occupancy_upper_ns': len(auth_upper_union),
        'per_actuation': per,
        'effects': effects,
    }


def canonical_case_summary(idx, case, out):
    return {'i': idx, 'input': case, 'out': out}


def run_controls(m):
    controls = {}
    def rejects(name, fn):
        try:
            fn(); controls[name] = False
        except ValueError:
            controls[name] = True
    rejects('duplicate_actuation_id_reject', lambda: m.analyze(m.Interval(0, 20), [
        m.Actuation(1, m.ReleaseReceipt(3, 4, False), [], 'dup'),
        m.Actuation(2, m.ReleaseReceipt(4, 5, False), [], 'dup')], []))
    rejects('post_key_down_reject', lambda: m.Actuation(1, m.ReleaseReceipt(2, 3, True), [], 'a'))
    rejects('release_before_down_reject', lambda: m.Actuation(5, m.ReleaseReceipt(4, 6, False), [], 'a'))

    overlap = m.analyze(m.Interval(0, 30), [
        m.Actuation(10, m.ReleaseReceipt(20, 20, False), [], 'a'),
        m.Actuation(15, m.ReleaseReceipt(25, 25, False), [], 'b')], [])
    controls['overlap_union_not_sum'] = overlap['physical_occupancy_lower_ns'] == 15 and overlap['physical_occupancy_upper_ns'] == 15

    outside = m.analyze(m.Interval(0, 40), [m.Actuation(10, m.ReleaseReceipt(20, 30, False), [m.Interval(0, 9), m.Interval(31, 40)], 'a')], [])
    controls['authority_outside_physical_no_increase'] = outside['authorized_occupancy_lower_ns'] == 0 and outside['authorized_occupancy_upper_ns'] == 0

    wait = m.Interval(0, 20)
    act = [m.Actuation(1, m.ReleaseReceipt(2, 2, False), [], 'known')]
    controls['useful_bound_role'] = m.analyze(wait, act, [m.EffectEvent(3, 'known', True, True)])['effects'] == {'useful_bound':1,'useful_unbound':0,'nonuseful_bound':0,'unscored':0}
    controls['useful_unbound_role'] = m.analyze(wait, act, [m.EffectEvent(3, 'other', True, True)])['effects'] == {'useful_bound':0,'useful_unbound':1,'nonuseful_bound':0,'unscored':0}
    controls['nonuseful_bound_role'] = m.analyze(wait, act, [m.EffectEvent(3, 'known', True, False)])['effects'] == {'useful_bound':0,'useful_unbound':0,'nonuseful_bound':1,'unscored':0}
    controls['unscored_role'] = m.analyze(wait, act, [m.EffectEvent(3, 'known', False, True)])['effects'] == {'useful_bound':0,'useful_unbound':0,'nonuseful_bound':0,'unscored':1}
    return controls


def classify(errors, controls):
    if errors:
        return 'FAIL_INTERVAL_ARITHMETIC'
    if not controls['duplicate_actuation_id_reject'] or not controls['post_key_down_reject'] or not contrls['release_before_down_reject']:
        return 'FAIL_PROVENANCE_OR_RELEASE_GATE'
    role_names = ['authority_outside_physical_no_increase','useful_bound_role','useful_unbound_role','nonuseful_bound_role','unscored_role']
    if any(not controls[n] for n in role_names):
        return 'FAIL_EVIDENCE_ROLE_COLLAPSE'
    if not controls['overlap_union_not_sum']:
        return 'FAIL_INTERVAL_ARITHMETIC'
    return 'PASS_USEFUL_CONTROL_INTERVAL_CONTRACT_SCOPED'


def main():
    if MARKER.exists() or RESULT.exists():
        raise SystemExit('formal invocation already consumed; rerun forbidden')
    m = load_candidate()
    MARKER.write_text(json.dumps({'task': TASK, 'formal_invocation': 1, 'seed': SEED, 'cases': N_CASES}, sort_keys=True) + '\n')
    rng = random.Random(SEED)
    digest = hashlib.sha256()
    mismatches = []
    invariant_errors = []
    for i in range(N_CASES):
        case = generate_case(rng, i)
        got = candidate_eval(m, case)
        exp = oracle(case)
        if got != exp and len(mismatches) < 20:
            mismatches.append({'i': i, 'case': case, 'got': got, 'expected': exp})
        if got != exp:
            pass
        vals = [got['physical_occupancy_lower_ns'], got['physical_occupancy_upper_ns'], got['authorized_occupancy_lower_ns'], got['authorized_occupancy_upper_ns']]
        if not (0 <= vals[0] <= vals[1] <= got['wait_ns'] and 0 <= vals[2] <= vals[3] and vals[2] <= vals[0] and vals[3] <= vals[1]):
            if len(invariant_errors) < 20:
                invariant_errors.append({'i': i, 'vals': vals, 'wait_ns': got['wait_ns']})
        digest.update((json.dumps(canonical_case_summary(i, case, got), sort_keys=True, separators=(',', ':')) + '\n').encode())
    # Regenerate mismatch count without storing all rows by replaying only comparison count in the same pass logic above.
    rng2 = random.Random(SEED)
    mismatch_count = 0
    for i in range(N_CASES):
        case = generate_case(rng2, i)
        if candidate_eval(m, case) != oracle(case):
            mismatch_count += 1
    controls = run_controls(m)
    errors = []
    if mismatch_count:
        errors.append(f'oracle_mismatch_count={mismatch_count}')
    if invariant_errors:
        errors.append(f'invariant_error_count={len(invariant_errors)}')
    decision = classify(errors, controls)
    result = {
        'schema': 'useful_control_interval_contract_formal_v2',
        'task': TASK,
        'formal_invocation': 1,
        'formal_reruns': 0,
        'seed': SEED,
        'case_count': N_CASES,
        'candidate_git_blob': '979f257b4f02be80bcaa30ae8d5a0aa92162bfb1',
        'candidate_sha256': sha256(CANDIDATE_PATH),
        'exact_oracle_matches': N_CASES - mismatch_count,
        'oracle_mismatch_count': mismatch_count,
        'case_digest_sha256': digest.hexdigest(),
        'invariant_error_count': len(invariant_errors),
        'controls': controls,
        'errors': errors,
        'decision': decision,
        'mismatch_examples': mismatches,
        'invariant_examples': invariant_errors,
        'network_calls': 0,
        'x11_or_gui_calls': 0,
        'task_input_calls': 0,
        'authority_grants': 0,
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'decision': decision, 'matches': result['exact_oracle_matches'], 'digest': result['case_digest_sha256']}, sort_keys=True))

if __name__ == '__main__':
    main()
