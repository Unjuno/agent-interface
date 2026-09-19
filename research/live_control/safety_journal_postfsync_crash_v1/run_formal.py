import json, pathlib, shutil
from run_case import run
ROOT=pathlib.Path(__file__).parent
SCHEDULE=[
 ('f00','no_crash'),('f01','post_fsync_sigkill'),
 ('f02','post_fsync_sigkill'),('f03','no_crash'),
 ('f04','no_crash'),('f05','post_fsync_sigkill'),
 ('f06','post_fsync_sigkill'),('f07','no_crash'),
 ('f08','no_crash'),('f09','post_fsync_sigkill'),
]
out=ROOT/'formal'
if out.exists(): raise SystemExit('formal output exists')
out.mkdir()
rows=[]
for cid,pol in SCHEDULE:
    rows.append(run(cid,pol,out/cid))
agg={'task':'SAFETY-JOURNAL-POSTFSYNC-CRASH-RECOVERY-20260917-001','formal_invocations':1,'formal_reruns':0,'rows':rows}
(out/'aggregate.json').write_text(json.dumps(agg,sort_keys=True,indent=2)+'\n')
print(json.dumps({'rows':len(rows)},sort_keys=True))
