"""Bounded, local-only Git state-preservation experiment. No user repositories."""
from __future__ import annotations
import argparse, hashlib, json, os, platform, random, subprocess, sys, time
from pathlib import Path

POLICIES = ('fixed_snapshot', 'current_patch', 'guarded_current_patch')
SCENARIOS = ('stable', 'unrelated_edit', 'unrelated_add', 'unrelated_delete',
             'read_conflict', 'write_conflict', 'after_validation_change')
READS = ('declared.txt', 'hidden.txt')
WRITE = 'effect.txt'
BASE = 'c6d195473be0aa876cc991093262494209c7971f'


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def env():
    e = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    e.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null',
             GIT_AUTHOR_NAME='Fixture', GIT_AUTHOR_EMAIL='fixture@example.invalid',
             GIT_COMMITTER_NAME='Fixture', GIT_COMMITTER_EMAIL='fixture@example.invalid',
             GIT_AUTHOR_DATE='2026-09-16T00:00:00+00:00',
             GIT_COMMITTER_DATE='2026-09-16T00:00:00+00:00', LC_ALL='C')
    return e


def git(repo, *args, data=None, check=True, extra=None):
    e = env(); e.update(extra or {})
    p = subprocess.run(['git', '-C', str(repo), *args], input=data,
                       capture_output=True, env=e, timeout=10)
    if check and p.returncode:
        raise RuntimeError((args, p.returncode, p.stderr.decode(errors='replace')))
    return p


def text(repo, *args):
    return git(repo, *args).stdout.decode().strip()


def snapshot(repo, oid):
    out = {}
    for item in git(repo, 'ls-tree', '-rz', oid).stdout.split(b'\0'):
        if item:
            meta, path = item.split(b'\t', 1)
            mode, kind, value = meta.decode().split()
            out[path.decode()] = [mode, kind, value]
    return out


def build(repo, files, parent, label):
    """Fixture construction only; flat, generated names and regular file bytes."""
    entries = []
    for name, value in sorted(files.items()):
        oid = git(repo, 'hash-object', '-w', '--stdin', data=value).stdout.strip()
        entries.append(b'100644 blob ' + oid + b'\t' + name.encode() + b'\0')
    tree = git(repo, 'mktree', '-z', data=b''.join(entries)).stdout.decode().strip()
    args = ['commit-tree', tree, '-m', label]
    if parent: args += ['-p', parent]
    return text(repo, *args)


def patch(repo, current, desired_entry, index):
    """Apply only the authored WRITE to the checked snapshot using a private index."""
    if index.exists(): raise FileExistsError(index)
    e = {'GIT_INDEX_FILE': str(index.resolve())}
    git(repo, 'read-tree', current, extra=e)
    mode, kind, blob = desired_entry
    if kind != 'blob': raise ValueError('fixture supports a blob output only')
    git(repo, 'update-index', '--add', '--cacheinfo', f'{mode},{blob},{WRITE}', extra=e)
    tree = git(repo, 'write-tree', extra=e).stdout.decode().strip()
    return text(repo, 'commit-tree', tree, '-p', current, '-m', 'bounded delayed edit')


def one(root, case):
    if case['policy'] not in POLICIES or case['scenario'] not in SCENARIOS:
        raise ValueError(case)
    d = Path(root) / case['id']; d.mkdir(parents=True, exist_ok=False)
    repo = d / 'repo.git'
    subprocess.run(['git', 'init', '--bare', '--quiet', '--object-format=sha1', str(repo)],
                   check=True, env=env(), capture_output=True, timeout=10)
    git(repo, 'config', 'core.logAllRefUpdates', 'true')
    token = case['id'].encode()
    files = {'declared.txt': b'allow\n', 'hidden.txt': b'allow\n',
             WRITE: b'old-' + token + b'\n', 'unrelated.txt': b'u0-' + token + b'\n',
             'deletable.txt': b'keep-' + token + b'\n'}
    planned = time.perf_counter_ns()
    a = build(repo, files, None, 'plan A')
    desired_files = dict(files); desired_files[WRITE] = b'desired-' + token + b'\n'
    b = build(repo, desired_files, a, 'fixed desired B')
    at = snapshot(repo, a); bt = snapshot(repo, b)
    git(repo, 'update-ref', '-m', 'baseline', 'refs/heads/target', a)
    changed = dict(files); s = case['scenario']
    if s == 'unrelated_edit': changed['unrelated.txt'] = b'u1-' + token + b'\n'
    elif s == 'unrelated_add': changed['added.txt'] = b'new-' + token + b'\n'
    elif s == 'unrelated_delete': del changed['deletable.txt']
    elif s == 'read_conflict': changed['hidden.txt'] = b'deny\n'
    elif s == 'write_conflict': changed[WRITE] = b'concurrent-' + token + b'\n'
    current = a
    if changed != files:
        current = build(repo, changed, a, 'other actor before validation')
        git(repo, 'update-ref', '-m', 'other actor', 'refs/heads/target', current, a)
    observed = text(repo, 'rev-parse', 'refs/heads/target')
    snap = snapshot(repo, observed)
    read_ok = all(snap.get(p) == at[p] for p in READS)
    write_ok = snap.get(WRITE) == at[WRITE]
    validated = time.perf_counter_ns()
    reason = 'read_conflict' if not read_ok else None
    if reason is None and case['policy'] == 'guarded_current_patch' and not write_ok:
        reason = 'write_conflict'
    proposed = None; rc = None; err = ''; changed_paths = []
    if reason is None:
        proposed = b if case['policy'] == 'fixed_snapshot' else patch(
            repo, observed, bt[WRITE], d / 'private.index')
        candidate = snapshot(repo, proposed)
        changed_paths = sorted(p for p in snap.keys() | candidate.keys()
                               if snap.get(p) != candidate.get(p))
        if case['policy'] != 'fixed_snapshot' and changed_paths != [WRITE]:
            raise RuntimeError('candidate changed outside declared write scope')
    precommit = observed
    if s == 'after_validation_change':
        changed['unrelated.txt'] = b'race-' + token + b'\n'
        precommit = build(repo, changed, observed, 'actor after validation')
        git(repo, 'update-ref', '-m', 'after validation', 'refs/heads/target', precommit, observed)
    commit_start = time.perf_counter_ns()
    if reason is None:
        p = git(repo, 'update-ref', '-m', 'delayed edit', 'refs/heads/target', proposed,
                observed, check=False)
        rc = p.returncode; err = p.stderr.decode()
        reason = 'applied' if rc == 0 else 'cas_rejected'
        if rc != 0 and s != 'after_validation_change':
            raise RuntimeError(('unexpected Git rejection', err))
    commit_end = time.perf_counter_ns()
    final = text(repo, 'rev-parse', 'refs/heads/target')
    row = dict(case, A=a, B=b, observed=observed, precommit=precommit, proposed=proposed,
               final=final, read_receipt={p: at[p] for p in READS}, write_before=at[WRITE],
               read_ok=read_ok, write_ok=write_ok, reason=reason, git_returncode=rc,
               stderr=err, candidate_changed_paths=changed_paths,
               planned_ns=planned, validated_ns=validated,
               commit_start_ns=commit_start, commit_end_ns=commit_end)
    row['reflog'] = text(repo, 'reflog', 'show', '--format=%H%x09%gs', 'refs/heads/target').splitlines()
    dump(d / 'result.json', row)
    return row


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('plan', type=Path); ap.add_argument('out', type=Path)
    args = ap.parse_args(); plan = json.loads(args.plan.read_text())
    for name, expected in plan['sources'].items():
        if hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError('source drift: ' + name)
    args.out.mkdir(parents=True, exist_ok=False)
    dump(args.out / 'started.json', {'allocation': plan['allocation'], 'wall_ns': time.time_ns()})
    try:
        for c in plan['cases']:
            r = one(args.out, c)
            print(r['id'], r['reason'], flush=True)
    except Exception as exc:
        dump(args.out / 'failure.json', {'error': repr(exc)}); raise
    dump(args.out / 'completed.json', {'count': len(plan['cases'])})

if __name__ == '__main__': main()
