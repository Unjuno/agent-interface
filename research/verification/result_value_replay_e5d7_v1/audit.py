"""Raw-file auditor. Does not import the receiver, runner, or its classifications."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3

SCHEDULES = {
    'STABLE': [('A', 1), ('A', 1), ('A', 1)],
    'OTHER_EFFECT': [('A', 1), ('B', 3), ('A', 1), ('A', 1)],
    'ABA': [('A', 1), ('B', 3), ('C', -3), ('A', 1), ('A', 1)],
    'LOST_REPLY': [('A', 1), ('B', 3), ('A', 1), ('A', 1)],
    'PAYLOAD_CONFLICT': [('A', 1), ('A', 2), ('A', 2)],
    'NEW_OPERATION': [('A', 1), ('B', 3), ('D', 2), ('D', 2), ('D', 2)],
}
MODES = ('CURRENT_PROJECTION', 'RECORDED_RESULT')


def strict(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def load(path):
    return json.loads(path.read_text())


def state(path):
    db = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)
    try:
        return {'state': list(db.execute('SELECT counter,version FROM state').fetchone()),
                'effects': [list(r) for r in db.execute('SELECT operation_id,delta,counter_after,commit_version FROM effects ORDER BY commit_version')]}
    finally:
        db.close()


def inspect(root, construction=False):
    errors, checks, processes, cases = [], 0, 0, 0
    counts = {m: {'cases': 0, 'effects': 0, 'replies': 0, 'replayed': 0, 'conflicts': 0,
                   'historical_mismatches': 0, 'wrong_value': 0, 'version_only': 0} for m in MODES}
    def check(ok, label):
        nonlocal checks
        checks += 1
        if not ok:
            errors.append(label)
    if not construction:
        try:
            freeze = load(root / 'FREEZE.json')
            for name, expected in freeze['files'].items():
                check(hashlib.sha256((root / name).read_bytes()).hexdigest() == expected, 'source:' + name)
        except Exception as exc:
            errors.append('freeze:' + repr(exc))
    batches = [root] if construction else sorted(root.glob('formal-*'))
    expected_scenarios = [load(root / 'CONSUMED.json')['scenario']] if construction else list(SCHEDULES)
    check(len(batches) == len(expected_scenarios), 'batch_count')
    seen = []
    for batch in batches:
        try:
            consumed, meta = load(batch / 'CONSUMED.json'), load(batch / 'batch.json')
            scenario = consumed['scenario']
            check(scenario in expected_scenarios, f'{batch.name}:scenario')
            seen.append(scenario)
            check(meta['status'] == 'COMPLETE', f'{scenario}:complete')
            check(type(consumed['pid']) is int and consumed['pid'] > 0, f'{scenario}:batch_pid')
            for rep in range(1 if construction else 2):
                for mode in MODES:
                    name = f'{scenario}-{mode}-{rep}'
                    d = batch / name
                    case = load(d / 'case.json')
                    check(case['scenario'] == scenario and case['policy'] == mode and case['rep'] == rep, name + ':identity')
                    sequence = SCHEDULES[scenario]
                    check(len(list(d.glob('*.process.json'))) == len(sequence), name + ':process_files')
                    check(len(case['calls']) == len(sequence), name + ':call_count')
                    check(state((d / 'initial.sqlite').resolve()) == {'state': [0, 0], 'effects': []}, name + ':initial')
                    history, value, version = {}, 0, 0
                    for i, (op, delta) in enumerate(sequence):
                        tag = f'{name}/{i}'
                        p = d / f'{i:02d}'
                        req = load(p.with_suffix('.request.json'))
                        check(strict(req) == strict({'scope': 'e5d7-private', 'operation_id': op, 'delta': delta}), tag + ':request')
                        rec = load(p.with_suffix('.process.json'))
                        raw = p.with_suffix('.stdout').read_text()
                        sql = p.with_suffix('.stderr').read_text()
                        crash = scenario == 'LOST_REPLY' and i == 0
                        check(type(rec['returncode']) is int and rec['returncode'] == (73 if crash else 0), tag + ':exit')
                        check(type(rec['pid']) is int and rec['pid'] > 0, tag + ':pid')
                        check(type(rec['started_ns']) is int and type(rec['ended_ns']) is int and rec['ended_ns'] >= rec['started_ns'], tag + ':clock')
                        check(len(rec['argv']) == (9 if crash else 8) and rec['argv'][1:3] == ['-S', '-B'] and Path(rec['argv'][3]).name == 'receiver.py' and rec['argv'][4] == '--db' and Path(rec['argv'][5]).parent.name == name and Path(rec['argv'][5]).name == 'state.sqlite' and rec['argv'][6:8] == ['--policy', mode], tag + ':argv')
                        check('BEGIN IMMEDIATE\n' in sql and 'COMMIT\n' in sql and sql.index('BEGIN IMMEDIATE') < sql.index('COMMIT'), tag + ':transaction')
                        check(('OWNED_EXIT_AFTER_COMMIT_73' in sql) == crash, tag + ':crash_marker')
                        fresh = op not in history
                        conflict = not fresh and history[op][0] != delta
                        if fresh:
                            value += delta
                            version += 1
                            history[op] = [delta, value, version]
                        db_expect = {'state': [value, version], 'effects': [[k] + v for k, v in history.items()]}
                        snapshot = p.with_suffix('.sqlite')
                        check(hashlib.sha256(snapshot.read_bytes()).hexdigest() == rec['snapshot_sha256'], tag + ':db_hash')
                        check(state(snapshot.resolve()) == db_expect, tag + ':db_reconstruction')
                        if crash:
                            check(raw == '', tag + ':missing_reply_stays_absent')
                        else:
                            actual = json.loads(raw)
                            expected_result = None
                            if not conflict:
                                out_value, out_version = (value, version) if (fresh or mode == 'CURRENT_PROJECTION') else tuple(history[op][1:])
                                expected_result = {'operation_id': op, 'counter_after': out_value, 'commit_version': out_version}
                            expect = {'status': 'CONFLICT' if conflict else ('APPLIED' if fresh else 'REPLAYED'),
                                      'result': expected_result, 'current': {'counter': value, 'version': version},
                                      'new_effect': fresh, 'authority': False, 'task_success': None}
                            check(strict(actual) == strict(expect), tag + ':response')
                            c = counts[mode]
                            c['replies'] += 1
                            c['conflicts'] += int(conflict)
                            if not fresh and not conflict:
                                c['replayed'] += 1
                                result = actual['result']
                                mismatch = (result['counter_after'], result['commit_version']) != tuple(history[op][1:])
                                wrong_value = result['counter_after'] != history[op][1]
                                c['historical_mismatches'] += int(mismatch)
                                c['wrong_value'] += int(wrong_value)
                                c['version_only'] += int(mismatch and not wrong_value)
                        processes += 1
                    check(state((d / 'state.sqlite').resolve()) == db_expect, name + ':final_db')
                    counts[mode]['cases'] += 1
                    counts[mode]['effects'] += version
                    cases += 1
        except Exception as exc:
            errors.append(f'{batch.name}:unreadable:{type(exc).__name__}:{exc}')
    check(sorted(seen) == sorted(expected_scenarios), 'scenario_coverage')
    if not construction:
        check(cases == 24 and processes == 96, 'denominator')
        check(counts['CURRENT_PROJECTION']['historical_mismatches'] == 12, 'control_discriminator')
        check(counts['CURRENT_PROJECTION']['wrong_value'] == 8 and counts['CURRENT_PROJECTION']['version_only'] == 4, 'aba_discriminator')
        check(counts['RECORDED_RESULT']['historical_mismatches'] == 0, 'candidate_correctness')
        check(all(c['effects'] == 24 and c['conflicts'] == 4 for c in counts.values()), 'effects_and_conflicts')
    return {'decision': ('PASS_CONSTRUCTION_AUDIT' if construction else 'PASS_HISTORICAL_RESULT_PROJECTION_SCOPED') if not errors else 'HOLD_OR_FAIL',
            'checks': checks, 'cases': cases, 'processes': processes, 'counts': counts, 'errors': errors}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('root', type=Path)
    ap.add_argument('--construction', action='store_true')
    a = ap.parse_args()
    result = inspect(a.root.resolve(), a.construction)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(bool(result['errors']))
