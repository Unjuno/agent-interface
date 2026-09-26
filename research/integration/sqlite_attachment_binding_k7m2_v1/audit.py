"""Raw-only independent reconstruction. Imports no study or actor implementation."""
import copy
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys

SCENARIOS = ('STABLE', 'CURRENT_WRITE', 'UNRELATED_WRITE', 'REBIND_PRE',
             'REBIND_PRE_CURRENT_WRITE', 'REBIND_PRE_OLD_WRITE',
             'REBIND_POST', 'OTHER_ALIAS_POST')
POLICIES = ('SCHEMA_ONLY', 'BINDING_SCOPED')


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def check_case(r, root, files=True):
    errors = []
    def ck(ok, name):
        if not ok:
            errors.append(name)
    ck(r['error'] is None, 'case_error')
    ck(r['scenario'] in SCENARIOS and r['policy'] in POLICIES, 'case_identity')
    ck(type(r['repetition']) is int and r['repetition'] in (0, 1), 'typed_repetition')
    calls = r['calls']
    tags = [c['tag'] for c in calls]
    ck(len(tags) == len(set(tags)), 'duplicate_tag')
    v = {c['tag']: c['response'] for c in calls}
    s, policy = r['scenario'], r['policy']
    order = ['initial', 'warm']
    if s.startswith('REBIND_PRE'):
        order.append('pre_bind')
    order += ['prepared', 'at_prepare']
    changed = {'CURRENT_WRITE': 'alpha', 'UNRELATED_WRITE': 'beta',
               'REBIND_PRE_CURRENT_WRITE': 'beta', 'REBIND_PRE_OLD_WRITE': 'alpha'}.get(s)
    if changed:
        order.append('mutation')
    if s in ('REBIND_POST', 'OTHER_ALIAS_POST'):
        order.append('post_bind')
    order += ['at_commit', 'decision', 'final', 'reader_stop', 'peer_stop']
    ck(tags == order, 'call_schedule')
    for i, call in enumerate(calls):
        ck(type(call['start_ns']) is int and type(call['end_ns']) is int
           and call['start_ns'] <= call['end_ns'], 'clock_type_order')
        if i:
            ck(calls[i-1]['end_ns'] <= call['start_ns'], 'rpc_order')
    slot, generation = 'A', 1
    prepared_slot = 'A'
    prepared_gen = 1
    for c in calls:
        q = c['request']
        if q['op'] == 'bind' and q['alias'] == 'slot':
            slot, generation = q['database'], generation + 1
            ck(c['response'] == {'alias': 'slot', 'database': slot, 'generation': generation}, 'bind_receipt')
        if c['tag'] == 'prepared':
            prepared_slot, prepared_gen = slot, generation
    ck(prepared_slot == ('B' if s.startswith('REBIND_PRE') else 'A'), 'prepare_source')
    ck(slot == ('B' if s.startswith('REBIND') else 'A'), 'commit_source')
    for name in ('A', 'B', 'U'):
        init = v['initial'][name]
        ck(type(init['schema']) is int and init['schema'] == 3, 'natural_schema')
        ck(init['rows'] == {'alpha': ['a0', 1], 'beta': ['b0', 1]}, 'initial_rows')
    ck(v['initial']['main']['effects'] == [], 'initial_effect_empty')
    before = v['at_prepare'][prepared_slot]
    after = v['at_commit'][slot]
    def target(snap):
        match = re.fullmatch(r'CREATE VIEW v_dep AS SELECT value,revision FROM (alpha|beta)', snap['view'])
        ck(match is not None, 'known_view_definition')
        return match.group(1) if match else 'alpha'
    dep, current_dep = target(before), target(after)
    value, version = before['rows'][dep]
    token = v['prepared']['token']
    expected_tables = [dep] if policy == 'BINDING_SCOPED' else ['alpha']
    ck(token == {'binding': prepared_gen, 'schema': before['schema'],
                 'dependencies': {t: before['rows'][t][1] for t in expected_tables},
                 'value': value, 'row_revision': version}, 'prepared_token')
    ck(v['warm']['token'] == {'binding': 1, 'schema': 3, 'dependencies': {'alpha': 1},
                              'value': 'a0', 'row_revision': 1}, 'warm_token')
    expected_observed = ['beta'] if prepared_slot == 'B' else []
    ck(v['prepared']['observed'] == expected_observed, 'actual_callback_set')
    ck(v['prepared']['metadata_reused'] is (not (policy == 'BINDING_SCOPED' and prepared_slot == 'B')), 'metadata_cache_choice')
    # Derive mutation truth from committed row images, not decision labels.
    expected_snapshot = copy.deepcopy(v['at_prepare'])
    if changed:
        old = expected_snapshot[prepared_slot]['rows'][changed]
        expected_snapshot[prepared_slot]['rows'][changed] = [old[0] + '!', old[1] + 1]
        mutation = next(c for c in calls if c['tag'] == 'mutation')
        ck(mutation['request'] == {'op': 'mutate', 'database': prepared_slot, 'table': changed}, 'mutation_request')
    ck(v['at_commit'] == expected_snapshot, 'committed_mutation')
    current_versions = {t: after['rows'][t][1] for t in token['dependencies']}
    reason = 'ACCEPT'
    if policy == 'BINDING_SCOPED' and generation != prepared_gen:
        reason = 'BINDING_CHANGED'
    elif current_versions != token['dependencies']:
        reason = 'REVISION_CHANGED'
    accepted = reason == 'ACCEPT'
    decision = v['decision']
    ck(decision == {'accepted': accepted, 'reason': reason, 'schema': after['schema'],
                    'binding': generation, 'current_revisions': current_versions}, 'decision_reconstruction')
    ck(type(decision['accepted']) is bool, 'typed_acceptance')
    expected_final = copy.deepcopy(expected_snapshot)
    expected_final['main']['effects'] = [[value, prepared_gen]] if accepted else []
    ck(v['final'] == expected_final, 'effect_reconstruction')
    for role in ('reader', 'peer'):
        proc = r['processes'][role]
        ck(type(proc['returncode']) is int and proc['returncode'] == 0, 'actual_process_exit')
        ck(type(proc['pid']) is int and proc['pid'] > 0, 'process_identity')
        ck(len(proc['argv']) == 6 and Path(proc['argv'][2]).name == 'actor.py'
           and proc['argv'][3] == role and Path(proc['argv'][4]).name == root.name
           and proc['argv'][5] == policy, 'process_command')
        if files:
            qlines = (root / (role + '.stdin')).read_bytes().splitlines(keepends=True)
            rlines = (root / (role + '.stdout')).read_bytes().splitlines(keepends=True)
            role_calls = [c for c in calls if c['role'] == role]
            ck(len(qlines) == len(rlines) == len(role_calls), 'ipc_cardinality')
            ck(all(x.endswith(b'\n') for x in qlines + rlines), 'ipc_framing')
            ck([json.loads(x) for x in qlines] == [c['request'] for c in role_calls], 'ipc_requests')
            ck([json.loads(x) for x in rlines] == [{'ok': True, 'result': c['response']} for c in role_calls], 'ipc_responses')
            ck((root / (role + '.stderr')).read_bytes() == b'', 'empty_stderr')
    if files:
        for name, d in r['file_hashes'].items():
            ck(digest(root / name) == d, 'file_hash:' + name)
        for name in ('A', 'B', 'U', 'main'):
            db = sqlite3.connect((root / (name + '.db')).resolve().as_uri() + '?mode=ro', uri=True)
            if name == 'main':
                snap = {'effects': [list(x) for x in db.execute('SELECT value,prepared_binding FROM effects ORDER BY rowid')]}
            else:
                snap = {'schema': db.execute('PRAGMA schema_version').fetchone()[0],
                        'view': db.execute("SELECT sql FROM sqlite_schema WHERE name='v_dep'").fetchone()[0],
                        'rows': {t: list(db.execute('SELECT value,revision FROM ' + t).fetchone()) for t in ('alpha', 'beta')}}
            ck(snap == v['final'][name], 'database_bytes:' + name)
            db.close()
        sql = [json.loads(x)['data'] for x in (root / 'reader.sql.jsonl').read_text().splitlines()
               if json.loads(x)['kind'] == 'sql']
        ck(sql.count('SELECT value,revision FROM slot.v_dep') == 2, 'two_real_selects')
        ck(sql.count('BEGIN IMMEDIATE') == 1, 'atomic_validation')
        ck(not any(re.search(r'schema_version\s*=', x, re.I) for x in sql), 'no_schema_assignment')
    valid = (slot == prepared_slot and after['rows'][current_dep] == [value, version])
    stats = {'missing': int(dep not in token['dependencies']),
             'extra': len(set(token['dependencies']) - {dep}),
             'stale_effect': int(accepted and not valid),
             'false_refusal': int(not accepted and valid),
             'accepted': int(accepted), 'refused': int(not accepted)}
    return errors, stats


def audit(root, source):
    errors = []
    frozen = json.loads((source / 'FREEZE.json').read_text())
    for name, d in frozen['sources'].items():
        if digest(source / name) != d:
            errors.append('source:' + name)
    totals = {p: {'cases': 0, 'missing': 0, 'extra': 0, 'stale_effect': 0,
                  'false_refusal': 0, 'accepted': 0, 'refused': 0} for p in POLICIES}
    cases = []
    for batch in range(4):
        b = root / ('batch-%d' % batch)
        done = json.loads((b / 'DONE.json').read_text())
        exit_record = json.loads((root / ('EXIT-%d.json' % batch)).read_text())
        if type(exit_record['returncode']) is not int or exit_record['returncode'] != 0 or done['count'] != 8:
            errors.append('batch_exit:' + str(batch))
        for path in sorted(b.glob('*/CASE.json')):
            if digest(path) != done['cases'].get(path.parent.name):
                errors.append('case_hash:' + str(path))
            r = json.loads(path.read_text())
            e, st = check_case(r, path.parent)
            errors += [path.parent.name + ':' + x for x in e]
            cases.append((r['scenario'], r['policy'], r['repetition']))
            t = totals[r['policy']]
            t['cases'] += 1
            for key, count in st.items():
                t[key] += count
    expected = [(s, p, r) for s in SCENARIOS for r in range(2) for p in POLICIES]
    if cases != expected:
        errors.append('complete_schedule')
    desired = {'SCHEMA_ONLY': {'cases': 16, 'missing': 6, 'extra': 6, 'stale_effect': 4,
                              'false_refusal': 2, 'accepted': 12, 'refused': 4},
               'BINDING_SCOPED': {'cases': 16, 'missing': 0, 'extra': 0, 'stale_effect': 0,
                                  'false_refusal': 0, 'accepted': 10, 'refused': 6}}
    if totals != desired:
        errors.append('registered_gate')
    return {'decision': 'PASS_ATTACHED_DATABASE_DEPENDENCY_BOUNDARY_SCOPED' if not errors else 'FAIL_OR_HOLD',
            'errors': errors, 'totals': totals, 'cases': len(cases)}


if __name__ == '__main__':
    root = Path(sys.argv[1]).resolve()
    result = audit(root, Path(__file__).resolve().parent)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if not result['errors'] else 1)
