"""Independent state oracle. Does not import experiment or trust its verdict."""
from __future__ import annotations
import argparse, base64, collections, hashlib, json, os, subprocess
from pathlib import Path


def require(test, message):
    if not test: raise AssertionError(message)


def cmd(repo, *args):
    e = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    e.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null', LC_ALL='C')
    p = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, env=e, timeout=10)
    require(p.returncode == 0, repr((args, p.stderr)))
    return p.stdout


def tree(repo, oid):
    """Read full bytes AND mode/type for every tracked leaf, not just target ref."""
    entries = {}
    for row in cmd(repo, 'ls-tree', '-rz', oid).split(b'\0'):
        if row:
            meta, name = row.split(b'\t', 1); mode, kind, obj = meta.decode().split()
            require(kind == 'blob', 'non-blob fixture entry')
            data = cmd(repo, 'cat-file', 'blob', obj)
            require(hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == obj,
                    'blob identity')
            entries[name.decode()] = {'mode': mode, 'type': kind, 'oid': obj,
                                     'data': base64.b64encode(data).decode()}
    return entries


def audit_case(d, case):
    r = json.loads((d / 'result.json').read_text()); repo = d / 'repo.git'
    for k in ('id', 'policy', 'scenario', 'rep'): require(r[k] == case[k], 'case identity')
    require(all(type(r[k]) is int for k in ('planned_ns', 'validated_ns', 'commit_start_ns', 'commit_end_ns')), 'clock type')
    require(r['planned_ns'] <= r['validated_ns'] <= r['commit_start_ns'] <= r['commit_end_ns'], 'clock order')
    for k in ('A', 'B', 'observed', 'precommit', 'final'):
        require(cmd(repo, 'cat-file', '-t', r[k]).strip() == b'commit', 'missing commit')
    require(cmd(repo, 'rev-parse', 'refs/heads/target').decode().strip() == r['final'], 'final ref')
    a, b, x, before, final = [tree(repo, r[k]) for k in ('A', 'B', 'observed', 'precommit', 'final')]
    token = case['id'].encode(); s = case['scenario']; policy = case['policy']
    values = {'declared.txt': b'allow\n', 'hidden.txt': b'allow\n',
              'effect.txt': b'old-' + token + b'\n', 'unrelated.txt': b'u0-' + token + b'\n',
              'deletable.txt': b'keep-' + token + b'\n'}
    def bytes_only(t): return {p: base64.b64decode(v['data']) for p, v in t.items()}
    require(bytes_only(a) == values, 'initial fixture bytes')
    wanted = dict(values); wanted['effect.txt'] = b'desired-' + token + b'\n'
    require(bytes_only(b) == wanted, 'desired fixture bytes')
    now = dict(values)
    if s == 'unrelated_edit': now['unrelated.txt'] = b'u1-' + token + b'\n'
    elif s == 'unrelated_add': now['added.txt'] = b'new-' + token + b'\n'
    elif s == 'unrelated_delete': del now['deletable.txt']
    elif s == 'read_conflict': now['hidden.txt'] = b'deny\n'
    elif s == 'write_conflict': now['effect.txt'] = b'concurrent-' + token + b'\n'
    require(bytes_only(x) == now, 'pre-validation fixture')
    if s == 'after_validation_change': now['unrelated.txt'] = b'race-' + token + b'\n'
    require(bytes_only(before) == now, 'pre-commit fixture')
    require(set(r['read_receipt']) == {'declared.txt', 'hidden.txt'}, 'complete read receipt')
    for p in r['read_receipt']:
        require(r['read_receipt'][p] == [a[p]['mode'], a[p]['type'], a[p]['oid']], 'read receipt identity')
    require(r['write_before'] == [a['effect.txt']['mode'], 'blob', a['effect.txt']['oid']], 'write precondition')
    read_ok = all(a[p] == x[p] for p in ('declared.txt', 'hidden.txt'))
    write_ok = a['effect.txt'] == x['effect.txt']
    require(type(r['read_ok']) is bool and r['read_ok'] == read_ok, 'read verdict')
    require(type(r['write_ok']) is bool and r['write_ok'] == write_ok, 'write verdict')
    attempted = read_ok and (policy != 'guarded_current_patch' or write_ok)
    applied = attempted and s != 'after_validation_change'
    expected_reason = ('read_conflict' if not read_ok else 'write_conflict' if not attempted
                       else 'applied' if applied else 'cas_rejected')
    require(r['reason'] == expected_reason, 'reason')
    rc = r['git_returncode']
    require((rc is None) if not attempted else (type(rc) is int and ((rc == 0) == applied)), 'return code')
    if attempted:
        candidate = tree(repo, r['proposed'])
        cp = sorted(p for p in x.keys() | candidate.keys() if x.get(p) != candidate.get(p))
        require(r['candidate_changed_paths'] == cp, 'write footprint receipt')
        if policy == 'fixed_snapshot': require(candidate == b, 'fixed snapshot construction')
        else:
            expect = dict(x); expect['effect.txt'] = b['effect.txt']
            require(candidate == expect, 'current patch construction')
    else: require(r['proposed'] is None and r['candidate_changed_paths'] == [], 'unexpected proposal')
    observed_expected = (b if policy == 'fixed_snapshot' else {**x, 'effect.txt': b['effect.txt']}) if applied else before
    require(final == observed_expected, 'actual state disagrees with recorded policy')
    should_apply = s in ('stable', 'unrelated_edit', 'unrelated_add', 'unrelated_delete')
    goal_tree = {**before, 'effect.txt': b['effect.txt']} if should_apply else before
    parent = cmd(repo, 'rev-list', '--parents', '-n', '1', r['final']).decode().split()[1:]
    history_ok = (parent == [r['observed']]) if should_apply and applied else True
    outside = sorted(p for p in before.keys() | final.keys() if p != 'effect.txt' and before.get(p) != final.get(p))
    outcome_ok = final == goal_tree and applied == should_apply and history_ok
    reflog = cmd(repo, 'reflog', 'show', '--format=%H%x09%gs', 'refs/heads/target').decode().strip().splitlines()
    require(reflog == r['reflog'] and reflog[0].split('\t')[0] == r['final'], 'reflog identity')
    return dict(case, correct=outcome_ok, applied=applied, should_apply=should_apply,
                outside_write_changes=outside, conflicting_write_overwritten=(s == 'write_conflict' and applied),
                current_parent_preserved=history_ok, reason=r['reason'], final_tree=final,
                parent_oids=parent)


def audit(root, plan):
    expected = {c['id'] for c in plan['cases']}
    actual = {d.name for d in root.iterdir() if d.is_dir()}
    require(actual == expected and len(expected) == len(plan['cases']), 'allocation completeness')
    rows = [audit_case(root / c['id'], c) for c in plan['cases']]
    cells = {}
    for r in rows:
        key = r['policy'] + ':' + r['scenario']
        cell = cells.setdefault(key, {'count': 0, 'correct': 0, 'outside_write_loss': 0, 'write_conflict_loss': 0})
        cell['count'] += 1; cell['correct'] += int(r['correct'])
        cell['outside_write_loss'] += int(bool(r['outside_write_changes']))
        cell['write_conflict_loss'] += int(r['conflicting_write_overwritten'])
    return {'schema': 'git-write-footprint-audit-v1', 'count': len(rows), 'integrity_pass': True,
            'cells': cells, 'rows': rows}

if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('root', type=Path); p.add_argument('plan', type=Path); p.add_argument('out', type=Path)
    args = p.parse_args(); result = audit(args.root, json.loads(args.plan.read_text()))
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, indent=2))
