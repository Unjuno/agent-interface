import argparse, json, pathlib
from run import run_case, SCHEDULES, sha
ap=argparse.ArgumentParser(); ap.add_argument('--out',required=True); ap.add_argument('--rep',type=int,required=True); ap.add_argument('--display-base',type=int,required=True); a=ap.parse_args()
out=pathlib.Path(a.out)
if out.exists(): raise SystemExit('output exists')
out.mkdir(parents=True); rows=[]
for i,s in enumerate(SCHEDULES): rows.append(run_case(out,s,a.rep,a.display_base+i))
json.dump(rows,open(out/'RAW.json','w'),sort_keys=True,indent=2)
files={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='MANIFEST.json'}
json.dump({'files':files,'count':len(files)},open(out/'MANIFEST.json','w'),sort_keys=True,indent=2)
print(json.dumps({'cases':len(rows),'rep':a.rep,'out':str(out)}))
