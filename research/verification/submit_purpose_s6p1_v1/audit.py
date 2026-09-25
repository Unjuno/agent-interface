"""Raw-only audit: no actor, runner, candidate or legacy module imports."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
HERE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'))


def reference(packet):
    """Independent in-memory transition fold over submitted request bytes."""
    doc = [1, 0, '']; commits = []; submissions = []; seen = {}; steps = []
    event_mode = packet['policy'] == 'SUBMIT_EVENT'
    def snapshot():
        rows = {'document': [doc[:]], 'commits': [r[:] for r in commits],
                'seen': [[key, *seen[key]] for key in sorted(seen)]}
        if event_mode:
            rows['submissions'] = sorted([r[:] for r in submissions])
        return rows
    initial = snapshot()
    for req in packet['requests']:
        before = {'revision': doc[1], 'value': doc[2]}
        valid = (type(req) is dict and set(req) == {'session', 'document', 'epoch', 'job_id', 'revision', 'value', 'kind'})
        if valid:
            valid = (req['session'] == packet['session'] and req['document'] == 'doc' and req['epoch'] == 'epoch-1'
                     and type(req['revision']) is int and 0 < req['revision'] < 2**63
                     and type(req['value']) is str and len(req['value']) <= 64
                     and type(req['job_id']) is str and 0 < len(req['job_id']) <= 80
                     and req['kind'] in ('AUTO', 'SUBMIT'))
        if not valid:
            result = {'status': 'INVALID', 'state': before, 'authority': False}
        else:
            identity = req['job_id']; fp = sha(canonical(req).encode())
            delta = req['revision'] - doc[1]
            if identity in seen:
                disposition = ('CONFLICT_ID', 'REPLAY')[seen[identity][0] == fp]
            else:
                if delta < 0:
                    disposition = 'STALE'
                elif delta == 0:
                    if req['value'] != doc[2]:
                        disposition = 'CONFLICT_REVISION'
                    else:
                        disposition = 'SUBMITTED_CURRENT' if event_mode and req['kind'] == 'SUBMIT' else 'DUPLICATE_REVISION'
                else:
                    disposition = 'APPLIED'
                seen[identity] = [fp, disposition]
            if disposition == 'APPLIED':
                doc = [1, req['revision'], req['value']]
                commits.append([len(commits) + 1, identity, req['revision'], req['value'], req['kind']])
            if event_mode and disposition in {'APPLIED', 'SUBMITTED_CURRENT'} and req['kind'] == 'SUBMIT':
                submissions.append([identity, req['revision'], req['value']])
            result = {'status': disposition, 'before': before, 'state': {'revision': doc[1], 'value': doc[2]}, 'authority': False}
        steps.append({'request': req, 'result': result, 'tables': snapshot()})
    return initial, steps, snapshot()


def audit(root, overrides=None):
    root = Path(root); overrides = {} if overrides is None else overrides
    errors = []; checks = 0; summary = {}; pids = []
    def check(condition, label):
        nonlocal checks
        checks += 1
        if not condition:
            errors.append(label)
    def data(path):
        key = str(Path(path).relative_to(root))
        return overrides.get(key, Path(path).read_bytes())
    def read(path):
        return json.loads(data(path))
    try:
        freeze = json.loads((HERE / 'FREEZE.json').read_text())
        for name, value in freeze['files'].items():
            check(sha((HERE / name).read_bytes()) == value, 'SOURCE:' + name)
        definition = json.loads((HERE / 'SCHEDULE.json').read_text())
        schedule = [{'id': f'r{rep}-{index:02}-{policy}', 'scenario': definition['conditions'][index]['name'],
                     'packet': {'session': definition['session'], 'policy': policy, 'requests': definition['conditions'][index]['requests']}}
                    for rep, index, policy in definition['order']]
        start, end = read(root / 'START.json'), read(root / 'END.json')
        outer = read(root / 'OUTER.json')
        check(type(outer['exit']) is int and outer['exit'] == 0 and outer['stderr'] == '' and outer['timed_out'] is False, 'RUNNER_EXIT')
        check(outer['pid'] == start['pid'] and outer['started_ns'] <= start['started_ns'] <= end['ended_ns'] <= outer['ended_ns'], 'RUNNER_OUTER_BINDING')
        check(Path(outer['argv'][3]).name == 'run.py' and outer['argv'][1:3] == ['-S', '-B'], 'RUNNER_COMMAND')
        check(start['source_hashes'] == freeze['files'], 'START_SOURCE')
        check(start['freeze_sha256'] == sha((HERE / 'FREEZE.json').read_bytes()), 'FREEZE_ID')
        check(len(schedule) == 40 and start['planned'] == 40 and end['planned'] == 40 and end['complete'] == 40, 'DENOMINATOR')
        check(end['disposition'] == 'COMPLETE' and end['error'] is None, 'END_DISPOSITION')
        check(type(start['pid']) is int and start['pid'] == end['pid'], 'RUNNER_PID')
        check(type(start['started_ns']) is int and type(end['ended_ns']) is int and start['started_ns'] < end['ended_ns'], 'RUN_ORDER')
        check({p.name for p in root.iterdir() if p.is_dir()} == {c['id'] for c in schedule}, 'DIRECTORIES')
        for case in schedule:
            label = case['id']; directory = root / label; packet = case['packet']; policy = packet['policy']
            a, o = read(directory / 'ACTOR.json'), read(directory / 'OBSERVER.json')
            for role, process in [('ACTOR', a), ('OBSERVER', o)]:
                check(type(process['exit']) is int and process['exit'] == 0 and process['timed_out'] is False and process['stderr'] == '', label + ':' + role + ':EXIT')
                check(type(process['pid']) is int and process['pid'] > 0, label + ':' + role + ':PID')
                pids.append(process['pid'])
                check(sha(process['stdout'].encode()) == process['stdout_sha256'], label + ':' + role + ':HASH')
                check(start['started_ns'] <= process['started_ns'] <= process['ended_ns'] <= end['ended_ns'], label + ':' + role + ':OUTER_CLOCK')
                check(process['argv'][1:3] == ['-S', '-B'], label + ':' + role + ':FLAGS')
                # Validate historical absolute command components without assuming relocation paths equal them.
                check(Path(process['argv'][3]).name == ('actor.py' if role == 'ACTOR' else 'observer.py'), label + ':' + role + ':COMMAND')
            check(a['stdin'] == canonical(packet) and o['stdin'] == '', label + ':REQUEST_BYTES')
            actor, observer = json.loads(a['stdout']), json.loads(o['stdout'])
            check(actor['pid'] == a['pid'] and observer['pid'] == o['pid'], label + ':INNER_PID')
            check(actor['packet_sha256'] == sha(a['stdin'].encode()), label + ':PACKET_HASH')
            for role, inner, outer in [('ACTOR', actor, a), ('OBSERVER', observer, o)]:
                check(outer['started_ns'] <= inner['started_ns'] <= inner['ended_ns'] <= outer['ended_ns'], label + ':' + role + ':INNER_CLOCK')
            check(a['ended_ns'] <= o['started_ns'], label + ':ACTOR_BEFORE_OBSERVER')
            initial, steps, final = reference(packet)
            check(actor['initial'] == initial, label + ':INITIAL')
            check(len(actor['steps']) == len(steps), label + ':STEP_COUNT')
            for index, expected in enumerate(steps):
                if index >= len(actor['steps']):
                    continue
                actual = actor['steps'][index]
                check(canonical(actual) == canonical(expected), label + ':STEP:' + str(index))
                check(actual['result']['authority'] is False, label + ':AUTHORITY:' + str(index))
            check(actor['final'] == final, label + ':FINAL')
            check(actor['pragmas'] == {'journal_mode': 'delete', 'synchronous': 2}, label + ':PRAGMA')
            stored = data(directory / 'store.sqlite')
            check(observer['sha256'] == sha(stored) and observer['bytes'] == len(stored) and observer['unchanged'] is True, label + ':DB_HASH')
            check(observer['tables'] == final, label + ':OBSERVER_TABLES')
            db = sqlite3.connect(':memory:')
            try:
                db.deserialize(stored); db.execute('PRAGMA query_only=ON')
                physical = {name: [list(r) for r in db.execute('SELECT * FROM ' + name + ' ORDER BY 1')] for name in final}
            finally:
                db.close()
            check(physical == final, label + ':RAW_DB')
            sql = [json.loads(line) for line in data(directory / 'sql.jsonl').decode().splitlines()]
            valid_requests = sum(row['result']['status'] != 'INVALID' for row in steps)
            check(sql.count('BEGIN IMMEDIATE') == valid_requests and sql.count('COMMIT') == valid_requests and 'ROLLBACK' not in sql, label + ':TRANSACTIONS')
            count = len(final.get('submissions', [])) if policy == 'SUBMIT_EVENT' else sum(r[4] == 'SUBMIT' for r in final['commits'])
            row = summary.setdefault(policy, {'cases': 0, 'requests': 0, 'submission_records': 0, 'document_writes': 0, 'by_scenario': {}})
            row['cases'] += 1; row['requests'] += len(steps); row['submission_records'] += count; row['document_writes'] += len(final['commits'])
            row['by_scenario'].setdefault(case['scenario'], []).append({'submissions': count, 'document_writes': len(final['commits']), 'statuses': [s['result']['status'] for s in steps]})
        check(len(pids) == 80 and len(set(pids)) == 80, 'CHILD_PID_COVERAGE')
        check(summary['REVISION_ONLY']['submission_records'] == 4 and summary['SUBMIT_EVENT']['submission_records'] == 10, 'SUBMISSION_GATE')
        check(summary['REVISION_ONLY']['document_writes'] == summary['SUBMIT_EVENT']['document_writes'], 'WRITE_PARITY')
    except Exception as error:
        errors.append('AUDIT_EXCEPTION:' + type(error).__name__ + ':' + str(error))
    return {'result': 'PASS_SUBMIT_PURPOSE_BOUNDARY_SCOPED' if not errors else 'HOLD_OR_FAIL',
            'checks': checks, 'errors': errors, 'summary': summary, 'cases': sum(s['cases'] for s in summary.values()),
            'new_gui_calls': 0, 'external_human_review': False}


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('root', type=Path); a = p.parse_args()
    result = audit(a.root); print(json.dumps(result, sort_keys=True, indent=2)); raise SystemExit(bool(result['errors']))
