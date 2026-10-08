"""Saved-only replay and applicable checks; never invokes formal producer."""
import hashlib,json,subprocess,sys
from pathlib import Path
from auditor import check,controls
ROOT=Path(__file__).resolve().parent
def main():
    result={'checks':[]}
    for cwd,args in [(ROOT,['-m','unittest','test_policy']),(ROOT.parents[2],['-m','unittest','discover','-s','research','-p','test_*workspace*.py']),(ROOT.parents[2],['-m','unittest','research/doom/test_map01_scorer_scheduler_replay_3270.py']),(ROOT.parents[2],['research/check_workspace_index.py','--git-tree'])]:
        if cwd==ROOT:args+=['test_runner']
        p=subprocess.run([sys.executable,'-B',*args],cwd=cwd,capture_output=True,text=True,timeout=60)
        result['checks'].append(dict(args=args,exit=p.returncode,stdout=p.stdout,stderr=p.stderr))
    for n,h in json.loads((ROOT/'FREEZE.json').read_text()).items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h
    raw=ROOT/'runs/candidate/raw.jsonl';rows=[json.loads(s) for s in raw.read_text().splitlines()]
    result['saved']=check(rows);assert controls(rows)==14
    audit=json.loads((ROOT/'runs/auditor/AUDIT.json').read_text());assert audit['raw_sha256']==hashlib.sha256(raw.read_bytes()).hexdigest()
    for k,v in result['saved'].items():assert audit[k]==v
    if (ROOT/'FILES.json').exists():
        for n,h in json.loads((ROOT/'FILES.json').read_text()).items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h
    if len(sys.argv)>1:
        with (ROOT/sys.argv[1]).open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result,indent=2));return int(any(x['exit'] for x in result['checks']))
if __name__=='__main__':sys.exit(main())
