"""Read-only saved replay, no private X11 input or producer invocation."""
import hashlib,json,subprocess,sys
from pathlib import Path
from saved_audit import check,controls
ROOT=Path(__file__).resolve().parent
def main():
    checks=[]
    for cwd,args in [(ROOT,['-m','unittest','test_policy']),(ROOT.parents[2],['-m','unittest','discover','-s','research','-p','test_*workspace*.py']),(ROOT.parents[2],['-m','unittest','research/doom/test_map01_scorer_scheduler_replay_3270.py']),(ROOT.parents[2],['research/check_workspace_index.py','--git-tree'])]:
        p=subprocess.run([sys.executable,'-B',*args],cwd=cwd,capture_output=True,text=True,timeout=60);checks.append(dict(args=args,exit=p.returncode,stdout=p.stdout,stderr=p.stderr))
    for n,h in json.loads((ROOT/'CONSTRUCTION_FREEZE.json').read_text()).items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h
    raw=ROOT/'runs/preflight/raw.jsonl';rows=[json.loads(s) for s in raw.read_text().splitlines()];saved=check(rows);assert controls(rows)==8
    audit=json.loads((ROOT/'SAVED_AUDIT.json').read_text());assert audit['raw_sha256']==hashlib.sha256(raw.read_bytes()).hexdigest()
    for k,v in saved.items():assert audit[k]==v
    if (ROOT/'FILES.json').exists():
        for n,h in json.loads((ROOT/'FILES.json').read_text()).items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h
    result=dict(checks=checks,saved=saved)
    if len(sys.argv)>1:
        with (ROOT/sys.argv[1]).open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result,indent=2));return int(any(c['exit'] for c in checks))
if __name__=='__main__':sys.exit(main())
