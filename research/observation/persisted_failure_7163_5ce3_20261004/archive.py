"""Saved-only local CI and exclusive manifest seal. Never launches native probe."""
if not __debug__:raise RuntimeError('STOP_OPTIMIZED_ARCHIVE')
import hashlib,json,subprocess,sys
from pathlib import Path
from audit import check,controls
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
def verify():
    freeze=json.loads((ROOT/'CONSTRUCTION_FREEZE.json').read_text())
    for n,h in freeze.items():
        if hashlib.sha256((ROOT/n).read_bytes()).hexdigest()!=h:raise ValueError('source drift '+n)
    raw=(ROOT/'runs/native/raw.jsonl').read_bytes();rows=[json.loads(x) for x in raw.splitlines()]
    result=check(rows,ROOT/'runs/native');copies=controls(rows)
    saved=json.loads((ROOT/'runs/AUDIT.json').read_text())
    if saved['raw_sha256']!=hashlib.sha256(raw).hexdigest() or saved['status']!=result['status']:raise ValueError('audit drift')
    receipt=json.loads((ROOT/'runs/receipt.json').read_text());i=json.loads(receipt['inspect']['stdout'])[0]
    if rows!=[json.loads(x) for x in receipt['run']['stdout'].splitlines()] or receipt['source_sha256']!=freeze or receipt['source_unchanged'] is not True:raise ValueError('execution continuity')
    if receipt['create']['stdout'].strip()!=i['Id'] or i['Image']!='sha256:b2ae049f7c500a3f6b6d162b0351297331434cff5a43f66e1bb41aff90478c96' or i['Config']['Labels']['research.owner']!='01a0b98b-5ce3-7f53-82f3-e09294f24d57':raise ValueError('container identity')
    if receipt['run']['exit']!=0 or i['State']['Running'] or i['State']['ExitCode']!=0 or i['State']['OOMKilled']:raise ValueError('terminal')
    env=json.loads((ROOT/'runs/native/ENV.json').read_text())
    if env['cgroups']!={'cpu.max':'100000 100000','memory.max':'536870912','memory.swap.max':'0','pids.max':'128'}:raise ValueError('actual limits')
    if i['HostConfig']['NetworkMode']!='none' or i['HostConfig']['ReadonlyRootfs'] is not True or {(m['Destination'],m['RW']) for m in i['Mounts']}!={('/study',False),('/out',True)}:raise ValueError('isolation')
    ci=[]
    for cwd,args in [(ROOT,['-m','unittest','test_policy','test_audit']),
                     (REPO,['-m','unittest','discover','-s','research','-p','test_*workspace*.py']),
                     (REPO,['-m','unittest','research/doom/test_map01_scorer_scheduler_replay_3270.py']),
                     (REPO,['research/check_workspace_index.py','--git-tree'])]:
        p=subprocess.run([sys.executable,'-B',*args],cwd=cwd,capture_output=True,text=True,timeout=30)
        ci.append(dict(args=args,exit=p.returncode,stdout=p.stdout,stderr=p.stderr))
        if p.returncode:raise ValueError(json.dumps(ci[-1]))
    if (ROOT/'FILES.json').exists():
        manifest=json.loads((ROOT/'FILES.json').read_text())
        paths={str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file() and p.name!='FILES.json'}
        if paths!=set(manifest):raise ValueError('manifest membership')
        for n,h in manifest.items():
            if hashlib.sha256((ROOT/n).read_bytes()).hexdigest()!=h:raise ValueError('manifest '+n)
    return dict(saved=result,copied_controls_rejected=copies,checks=ci,provenance_scope='saved parent-generated records, no independent authenticity or exhaustive history certificate')
def main():
    result=verify()
    if sys.argv[1:]==['--seal']:
        with (ROOT/'LOCAL_CI.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
        manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='FILES.json'}
        with (ROOT/'FILES.json').open('x') as f:json.dump(manifest,f,indent=2);f.write('\n')
        result['manifest_targets']=len(manifest)
    print(json.dumps(result))
if __name__=='__main__':main()
