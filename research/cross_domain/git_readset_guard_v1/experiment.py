from __future__ import annotations
import argparse, json, subprocess, time
from pathlib import Path


def run(repo: Path, *args: str, check: bool = True):
    p = subprocess.run(args, cwd=repo, text=True, capture_output=True)
    if check and p.returncode != 0:
        raise RuntimeError((args, p.returncode, p.stdout, p.stderr))
    return p


def git(repo: Path, *args: str) -> str:
    return run(repo, 'git', *args).stdout.strip()


def write_files(repo: Path, declared: str, hidden: str, unrelated: str, effect: str):
    (repo/'declared.txt').write_text(declared + '\n')
    (repo/'hidden.txt').write_text(hidden + '\n')
    (repo/'unrelated.txt').write_text(unrelated + '\n')
    (repo/'effect.txt').write_text(effect + '\n')
    git(repo, 'add', '.')


def commit(repo: Path, msg: str) -> str:
    git(repo, '-c', 'user.name=fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-m', msg)
    return git(repo, 'rev-parse', 'HEAD')


def blob(repo: Path, oid: str, path: str) -> str:
    return git(repo, 'rev-parse', f'{oid}:{path}')


class ReadTracer:
    def __init__(self, repo: Path, oid: str):
        self.repo = repo; self.oid = oid; self.reads = []
    def read_text(self, path: str) -> str:
        b = blob(self.repo, self.oid, path)
        val = git(self.repo, 'show', f'{self.oid}:{path}').rstrip('\n')
        self.reads.append({'path': path, 'blob_oid': b})
        return val


def action_allowed(tracer: ReadTracer) -> bool:
    # Both values are semantically required. This is the authoritative fixture predicate.
    declared = tracer.read_text('declared.txt')
    hidden = tracer.read_text('hidden.txt')
    return declared == 'allow' and hidden == 'allow'


def setup_repo(root: Path):
    repo = root/'repo'; repo.mkdir()
    git(repo, 'init', '-q')
    write_files(repo, 'allow', 'allow', 'u0', 'old')
    A = commit(repo, 'A baseline')
    # B is desired effect commit based on A.
    write_files(repo, 'allow', 'allow', 'u0', 'B')
    B = commit(repo, 'B desired')
    git(repo, 'checkout', '-q', '-b', 'fixtures', A)
    write_files(repo, 'deny', 'allow', 'u0', 'old')
    D = commit(repo, 'D declared changed')
    git(repo, 'reset', '--hard', A)
    write_files(repo, 'allow', 'deny', 'u0', 'old')
    H = commit(repo, 'H hidden changed')
    git(repo, 'reset', '--hard', A)
    write_files(repo, 'allow', 'allow', 'u1', 'old')
    U = commit(repo, 'U unrelated changed')
    git(repo, 'checkout', '-q', '-B', 'target', A)
    git(repo, 'branch', '-f', 'desired', B)
    return repo, {'A':A,'B':B,'D':D,'H':H,'U':U}


def one(case: dict, out: Path):
    out.mkdir(parents=True, exist_ok=False)
    repo, ids = setup_repo(out)
    A,B,D,H,U = [ids[k] for k in ['A','B','D','H','U']]
    tracer = ReadTracer(repo, A)
    assert action_allowed(tracer)
    plan_reads = tracer.reads
    planner_declared = ['declared.txt']
    planned_ns = time.perf_counter_ns()
    schedule = case['schedule']
    if schedule == 'declared_changed':
        git(repo, 'update-ref', 'refs/heads/target', D, A)
    elif schedule == 'hidden_changed':
        git(repo, 'update-ref', 'refs/heads/target', H, A)
    elif schedule == 'unrelated_changed':
        git(repo, 'update-ref', 'refs/heads/target', U, A)
    elif schedule != 'stable':
        raise ValueError(schedule)
    current = git(repo, 'rev-parse', 'refs/heads/target')
    paths = planner_declared if case['policy'] == 'planner_declared' else [r['path'] for r in plan_reads]
    expected_blobs = {r['path']: r['blob_oid'] for r in plan_reads}
    validation = []
    valid = True
    for path in paths:
        cur_blob = blob(repo, current, path)
        ok = cur_blob == expected_blobs[path]
        validation.append({'path':path,'expected_blob':expected_blobs[path],'current_blob':cur_blob,'equal':ok})
        valid &= ok
    delivered_ns = time.perf_counter_ns()
    rc = None; stderr = ''
    if valid:
        p = run(repo, 'git', 'update-ref', 'refs/heads/target', B, current, check=False)
        rc = p.returncode; stderr = p.stderr
    else:
        rc = 97; stderr = 'semantic dependency validation failed'
    finished_ns = time.perf_counter_ns()
    final_target = git(repo, 'rev-parse', 'refs/heads/target')
    expected_final = B if schedule in ('stable','unrelated_changed') else (D if schedule=='declared_changed' else H)
    row = {
        **case, **ids,
        'planned_ns':planned_ns,'delivered_ns':delivered_ns,'finished_ns':finished_ns,
        'planner_declared':planner_declared,'plan_read_set':plan_reads,'validated_paths':paths,
        'validation':validation,'pre_delivery_target':current,'returncode':rc,'stderr':stderr,
        'final_target':final_target,'expected_final':expected_final,
        'ground_truth_correct': final_target == expected_final,
        'final_effect': git(repo, 'show', f'{final_target}:effect.txt').strip(),
        'reflog': git(repo, 'reflog', 'show', '--format=%H%x09%gs', 'refs/heads/target').splitlines(),
    }
    (out/'result.json').write_text(json.dumps(row,indent=2,sort_keys=True)+'\n')
    return row


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('plan',type=Path); ap.add_argument('out',type=Path); a=ap.parse_args()
    plan=json.loads(a.plan.read_text()); a.out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for c in plan['cases']:
        rows.append(one(c,a.out/c['id']))
    (a.out/'rows.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')

if __name__=='__main__': main()
