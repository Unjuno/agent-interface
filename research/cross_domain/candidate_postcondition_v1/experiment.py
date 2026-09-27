"""Finite native-Git candidate validation experiment; only generated bare repos."""
from __future__ import annotations
import argparse, hashlib, json, os, re, subprocess, time
from pathlib import Path

POLICIES = ('scope_only', 'scope_and_postcondition')
SCENARIOS = ('correct', 'unrelated_preserved', 'wrong_bytes', 'wrong_mode',
             'wrong_kind', 'target_deleted', 'extra_change', 'no_op',
             'wrong_parent', 'read_conflict', 'write_conflict', 'ref_race')
WRITE = 'output/effect.txt'
READS = ('declared.txt', 'hidden.txt')
REF = 'refs/heads/target'
BASE = '0dd239b7db10831a4e8ac078d3a32d4be6370e3d'


def dump(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')


def clean_env():
    e = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    e.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null',
             GIT_AUTHOR_NAME='Fixture', GIT_AUTHOR_EMAIL='fixture@example.invalid',
             GIT_COMMITTER_NAME='Fixture', GIT_COMMITTER_EMAIL='fixture@example.invalid',
             GIT_AUTHOR_DATE='2026-09-16T00:00:00+00:00',
             GIT_COMMITTER_DATE='2026-09-16T00:00:00+00:00', LC_ALL='C')
    return e


class NativeGit:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.repo = self.directory / 'repo.git'
        self.log = self.directory / 'commands.jsonl'

    def run(self, *args, data=None, check=True, extra=None):
        env = clean_env(); env.update(extra or {})
        start = time.perf_counter_ns()
        p = subprocess.run(['git', '--no-replace-objects', '-C', str(self.repo), *args],
                           input=data, capture_output=True, env=env, timeout=10)
        end = time.perf_counter_ns()
        record = dict(argv=list(args), stdin_hex=None if data is None else data.hex(),
                      stdout_hex=p.stdout.hex(), stderr=p.stderr.decode(errors='replace'),
                      rc=p.returncode, start_ns=start, end_ns=end)
        with self.log.open('a') as f: f.write(json.dumps(record, sort_keys=True) + '\n')
        if check and p.returncode: raise RuntimeError(record)
        return p

    def text(self, *args, **kwargs):
        return self.run(*args, **kwargs).stdout.decode().strip()

    def init(self):
        # Empty template means no copied hooks; no user config or working tree.
        template = self.directory / 'template'; template.mkdir()
        subprocess.run(['git', 'init', '--bare', '--quiet', '--object-format=sha1',
                        '--template=' + str(template.resolve()), str(self.repo)],
                       env=clean_env(), check=True, capture_output=True, timeout=10)
        self.run('config', 'core.logAllRefUpdates', 'true')
        self.run('config', 'gc.auto', '0')

    def entries(self, oid):
        result = {}
        for item in self.run('ls-tree', '-rz', oid).stdout.split(b'\0'):
            if item:
                metadata, name = item.split(b'\t', 1)
                result[name.decode()] = metadata.decode().split()
        return result

    def build(self, files, parent, message):
        # Each candidate construction uses its own index, including nested paths.
        index = self.directory / ('index-' + str(len(list(self.directory.glob('index-*')))))
        extra = {'GIT_INDEX_FILE': str(index.resolve())}
        self.run('read-tree', '--empty', extra=extra)
        for name, (mode, data) in sorted(files.items()):
            if not name or '\0' in name or name.startswith('/') or '..' in name.split('/'):
                raise ValueError('invalid generated path')
            blob = self.text('hash-object', '-w', '--stdin', data=data)
            self.run('update-index', '--add', '--cacheinfo', f'{mode},{blob},{name}', extra=extra)
        tree = self.text('write-tree', extra=extra)
        args = ['commit-tree', tree, '-m', message]
        if parent is not None: args += ['-p', parent]
        return self.text(*args)

    def parents(self, oid):
        headers = self.run('cat-file', '-p', oid).stdout.split(b'\n\n', 1)[0]
        return [line[7:].decode() for line in headers.splitlines() if line.startswith(b'parent ')]


def inspect_candidate(git, request, current, candidate, policy):
    """No ref mutation: evaluate one immutable candidate against a caller request."""
    if policy not in POLICIES: raise ValueError('unknown policy')
    for oid in (current, candidate, request['plan_oid']):
        if not isinstance(oid, str) or not re.fullmatch('[0-9a-f]{40}', oid):
            raise ValueError('full immutable SHA1 OID required')
        if git.text('cat-file', '-t', oid) != 'commit': raise ValueError('commit required')
    before = git.entries(current); after = git.entries(candidate)
    changed = [p.decode() for p in git.run('diff-tree', '--no-commit-id', '--name-only',
               '-r', '-z', '--no-renames', current, candidate).stdout.split(b'\0') if p]
    read_ok = all(before.get(k) == v for k, v in request['reads'].items())
    write_ok = all(before.get(k) == v for k, v in request['before'].items())
    scope_ok = sorted(changed) == sorted(request['after'])
    parent_ok = git.parents(candidate) == [current]
    post_ok = all(after.get(k) == v for k, v in request['after'].items())
    checks = dict(read_ok=read_ok, write_ok=write_ok, scope_ok=scope_ok,
                  parent_ok=parent_ok, post_ok=post_ok, changed_paths=sorted(changed))
    # The only policy difference is whether post_ok gates publication.
    reason = next((label for ok, label in ((read_ok, 'read_conflict'),
        (write_ok, 'write_conflict'), (scope_ok, 'scope_mismatch'),
        (parent_ok, 'parent_mismatch'),
        (post_ok or policy == 'scope_only', 'postcondition_mismatch')) if not ok), 'eligible')
    return dict(checks, reason=reason)


def one(root, case):
    if case['policy'] not in POLICIES or case['scenario'] not in SCENARIOS: raise ValueError(case)
    d = Path(root) / case['id']; d.mkdir(parents=True, exist_ok=False)
    g = NativeGit(d); g.init()
    # Same bytes, commit metadata and IDs within each paired policy/scenario/rep.
    token = f"r{case['rep']:02d}-{case['scenario']}"
    files = {'declared.txt': ('100644', b'allow\n'),
             'hidden.txt': ('100644', b'allow\n'),
             WRITE: ('100644', ('old-' + token + '\n').encode()),
             'keep/unrelated.txt': ('100644', ('keep-' + token + '\n').encode()),
             'keep/mode.txt': ('100755', b'unchanged executable mode\n')}
    planned_ns = time.perf_counter_ns()
    a = g.build(files, None, 'planned state'); g.run('update-ref', '-m', 'baseline', REF, a)
    desired = ('desired-' + token + '\n').encode()
    expected_blob = g.text('hash-object', '-w', '--stdin', data=desired)
    base_entries = g.entries(a)
    request = dict(plan_oid=a, reads={p: base_entries[p] for p in READS},
                   before={WRITE: base_entries[WRITE]},
                   after={WRITE: ['100644', 'blob', expected_blob]},
                   expected_bytes_hex=desired.hex())
    dump(d / 'request.json', request)
    scenario = case['scenario']; current_files = dict(files)
    if scenario == 'unrelated_preserved': current_files['keep/unrelated.txt'] = ('100644', b'new unrelated\n')
    if scenario == 'read_conflict': current_files['hidden.txt'] = ('100644', b'deny\n')
    if scenario == 'write_conflict': current_files[WRITE] = ('100644', b'new competing edit\n')
    current = a
    if current_files != files:
        current = g.build(current_files, a, 'precheck change')
        g.run('update-ref', '-m', 'precheck change', REF, current, a)
    proposed_files = dict(current_files); proposed_files[WRITE] = ('100644', desired)
    if scenario == 'wrong_bytes': proposed_files[WRITE] = ('100644', b'incorrect result\n')
    if scenario == 'wrong_mode': proposed_files[WRITE] = ('100755', desired)
    if scenario == 'wrong_kind': proposed_files[WRITE] = ('120000', desired)
    if scenario == 'target_deleted': del proposed_files[WRITE]
    if scenario == 'extra_change': proposed_files['keep/unrelated.txt'] = ('100644', b'collateral edit\n')
    if scenario == 'no_op': proposed_files = dict(current_files)
    parent = None if scenario == 'wrong_parent' else current
    candidate = g.build(proposed_files, parent, 'proposed edit')
    # The proposed object exists even on refusal, but is not published to target.
    receipt = inspect_candidate(g, request, current, candidate, case['policy'])
    validated_ns = time.perf_counter_ns(); precommit = current
    if scenario == 'ref_race':
        raced = dict(current_files); raced['keep/unrelated.txt'] = ('100644', b'after validation\n')
        precommit = g.build(raced, current, 'postcheck actor')
        g.run('update-ref', '-m', 'postcheck actor', REF, precommit, current)
    start = time.perf_counter_ns(); rc = None; stderr = ''; reason = receipt['reason']
    if reason == 'eligible':
        p = g.run('update-ref', '-m', 'publish candidate', REF, candidate, current, check=False)
        rc = p.returncode; stderr = p.stderr.decode()
        reason = 'applied' if rc == 0 else 'cas_rejected'
        if rc != 0 and scenario != 'ref_race': raise RuntimeError(('unexpected CAS error', stderr))
    end = time.perf_counter_ns()
    row = dict(case, plan_oid=a, current=current, candidate=candidate, precommit=precommit,
               final=g.text('rev-parse', REF), receipt=receipt, reason=reason, returncode=rc,
               stderr=stderr, planned_ns=planned_ns, validated_ns=validated_ns,
               publish_start_ns=start, publish_end_ns=end)
    dump(d / 'result.json', row)
    return row


def main():
    p = argparse.ArgumentParser(); p.add_argument('plan', type=Path); p.add_argument('out', type=Path)
    a = p.parse_args(); plan = json.loads(a.plan.read_text())
    for name, digest in plan['sources'].items():
        if hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest() != digest:
            raise RuntimeError('source mismatch: ' + name)
    a.out.mkdir(parents=True, exist_ok=False)
    dump(a.out / 'started.json', {'allocation': plan['allocation'], 'wall_ns': time.time_ns()})
    try:
        for case in plan['cases']:
            r = one(a.out, case); print(r['id'], r['reason'], flush=True)
    except Exception as e:
        dump(a.out / 'failure.json', {'error': repr(e)}); raise
    dump(a.out / 'completed.json', {'count': len(plan['cases'])})

if __name__ == '__main__': main()
