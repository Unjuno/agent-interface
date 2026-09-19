"""Independent retained-evidence audit. Does not import the candidate gate."""
from collections import Counter
from contextlib import closing
import json
from pathlib import Path
import sqlite3


def load(path):
    return json.loads(Path(path).read_text())


def audit_case(root):
    root = Path(root); result = load(root/'result.json'); config = load(root/'config.json')
    ready = load(root/'ready.json'); trace = load(root/'trace.json'); spec = result['spec']
    policy, scenario, token = spec['policy'], spec['scenario'], config['token']
    failures = []; issued = {}; resolved = {}; input_count = 0; brackets = 0; query_count = 0
    def require(ok, message):
        if not ok:
            failures.append(message)
    def sample(row):
        nonlocal brackets
        brackets += 1
        require(all(type(row.get(k)) is int for k in ('start_ns','sample_ns','end_ns')) and
                row['start_ns'] <= row['sample_ns'] <= row['end_ns'], 'invalid acquisition bracket')
    def conflict(a, b, canonical):
        values = []
        for op in (a, b):
            ef = ready['effects'][op]
            if ef['reads'] is None or ef['writes'] is None:
                return True
            try:
                convert = (lambda n: ready['aliases'][n]) if canonical else (lambda n: n)
                values.append((set(map(convert, ef['reads'])),set(map(convert, ef['writes']))))
            except KeyError:
                return True
        (ar, aw), (br, bw) = values
        return bool((aw & (br | bw)) or (bw & (ar | aw)))
    last_selection = None
    for row in trace:
        event = row['event']
        if event == 'selection':
            op = row['operation']; pending = set(issued) - set(resolved)
            require(sorted(pending) == row['pending'], 'invented pending set')
            require(row.get('grants_input_authority') is False, 'advice grants authority')
            require(op not in issued, 'operation was retried')
            if policy == 'global_wait':
                require(not pending, 'global arm bypassed pending effect')
            elif policy != 'release_only':
                require(not any(conflict(op, p, policy != 'name_frontier') for p in pending), 'frontier violated dependency')
            last_selection = op
        elif event in ('input', 'lookup_input'):
            rec = row['receipt']; input_count += 1
            for key in ('pre','held','released'):
                sample(rec[key])
            require(not rec['pre']['keys'] and not rec['pre']['buttons'] and rec['pre']['focus'] == ready['window_id'], 'stale focus or held input before admission')
            require(rec['code'] in rec['held']['keys'], 'missing physical down')
            require(not rec['released']['keys'] and not rec['released']['buttons'], 'nonempty physical release')
            require(rec['pre']['end_ns'] <= rec['start_ns'] <= rec['ack_ns'] <= rec['held']['start_ns'] <=
                    rec['held']['end_ns'] <= rec['up_start_ns'] <= rec['up_end_ns'] <= rec['released']['start_ns'], 'input timestamp order')
            if event == 'input':
                require(last_selection == row['operation'], 'input not tied to selection')
                require(row['operation'] not in issued, 'duplicate issued operation')
                issued[row['operation']] = rec['start_ns']; last_selection = None
            else:
                require(policy == 'frontier_lookup' and rec['key'] == 'F5', 'unauthorized lookup arm')
                query_count += 1
        elif event == 'feedback':
            require(type(row['start_ns']) is int and row['start_ns'] <= row['end_ns'], 'feedback interval')
            for decision in row['decisions']:
                receipt = load(root/'public'/decision['file']); op = receipt.get('operation')
                valid = bool(op in issued and receipt.get('epoch') == config['epoch'] and
                    receipt.get('payload_sha256') == ready['effects'][op]['payload_sha256'] and
                    receipt.get('kind') in ('ack','lookup') and receipt.get('status') == 'COMMITTED' and
                    type(receipt.get('effect_rowid')) is int and receipt['effect_rowid'] > 0 and
                    type(receipt.get('durable_ns')) is int and type(receipt.get('published_ns')) is int and
                    issued[op] <= receipt['durable_ns'] <= receipt['published_ns'] <= row['end_ns'])
                require(decision['accepted'] is valid, 'incorrect receipt acceptance')
                if valid:
                    resolved.setdefault(op, row['end_ns'])
    sample(result['final_input'])
    require(not result['final_input']['keys'] and not result['final_input']['buttons'], 'final input nonempty')
    require(result['issued'] == issued and result['resolved'] == resolved, 'state summary differs from trace')
    require(result['visible_complete'] is (len(resolved)==4), 'false visible completion')
    require(result['lookups'] == query_count, 'lookup count mismatch')
    with closing(sqlite3.connect('file:' + str((root/'private.sqlite').resolve()) + '?mode=ro',uri=True)) as db:
        effects = [list(x) for x in db.execute('SELECT rowid,operation,value,read_version,applied_ns FROM effects ORDER BY rowid')]
        documents = [list(x) for x in db.execute('SELECT * FROM documents ORDER BY name')]
        require(db.execute('PRAGMA integrity_check').fetchone()[0]=='ok', 'database integrity')
    require(effects == result['score']['effects'], 'reported effects differ from retained database')
    require(documents == result['score']['documents'], 'reported documents differ from retained database')
    for name, value, version in documents:
        matches = [x for x in effects if x[1] == name]
        require(version == len(matches) and value == (matches[-1][2] if matches else 'old:' + name), 'document/effect disagreement')
    counts = Counter(x[1] for x in effects)
    require(all(n==1 for n in counts.values()), 'duplicate effect')
    bad = [x[1] for x in effects if x[2] != token + ':' + ('A' if x[1]=='D' else x[1])]
    premature = sum(x[1]=='D' and x[3] != 1 for x in effects)
    if scenario in ('delayed','alias','opaque'):
        expected_issued, expected_effects, expected_resolved = set('ADBC'), set('ADBC'), set('ADBC')
    elif scenario == 'ack_lost':
        if policy == 'global_wait':
            expected_issued, expected_effects, expected_resolved = set('A'), set('A'), set()
        elif policy == 'release_only':
            expected_issued, expected_effects, expected_resolved = set('ADBC'), set('ADBC'), set('DBC')
        elif policy == 'frontier_lookup':
            expected_issued, expected_effects, expected_resolved = set('ADBC'), set('ADBC'), set('ADBC')
        else:
            expected_issued, expected_effects, expected_resolved = set('ABC'), set('ABC'), set('BC')
    elif scenario == 'dropped':
        if policy == 'global_wait':
            expected_issued, expected_effects, expected_resolved = set('A'), set(), set()
        elif policy == 'release_only':
            expected_issued, expected_effects, expected_resolved = set('ADBC'), set('DBC'), set('DBC')
        else:
            expected_issued, expected_effects, expected_resolved = set('ABC'), set('BC'), set('BC')
    else:
        raise ValueError('unknown scenario')
    wrong_expected = policy=='release_only' or (policy=='name_frontier' and scenario=='alias')
    require(set(issued)==expected_issued, 'unexpected issued operations')
    require(set(counts)==expected_effects, 'unexpected committed operations')
    require(set(resolved)==expected_resolved, 'unexpected resolved operations')
    require(bad == (['D'] if wrong_expected else []), 'unexpected semantic output')
    require(premature == int(wrong_expected), 'unexpected dependent-read version')
    application = [json.loads(s) for s in (root/'application.jsonl').read_text().splitlines()]
    requests = [s for s in application if s['event']=='request']
    require(Counter(s['operation'] for s in requests)==Counter(issued.keys()), 'application/input count divergence')
    commits = [s for s in application if s['event']=='committed']
    boundary = resolved.get('A', result['end_ns'])
    early = sum(s['operation'] in ('B','C') and s['durable_ns'] < boundary for s in commits)
    return dict(**{'pass':not failures}, failures=failures, index=spec['index'], policy=policy,
                scenario=scenario, repetition=spec['repetition'], independent_before_A_resolution=early,
                correct_effects=len(effects)-len(bad), effects=len(effects), wrong_effects=len(bad),
                premature_dependent_reads=premature, input_releases=input_count, acquisition_brackets=brackets,
                visible_complete=result['visible_complete'], acknowledged=len(resolved), lookups=query_count,
                duration_ms=(result['end_ns']-result['start_ns'])/1_000_000,
                A_resolution_ms=((resolved['A']-result['start_ns'])/1_000_000 if 'A' in resolved else None))
