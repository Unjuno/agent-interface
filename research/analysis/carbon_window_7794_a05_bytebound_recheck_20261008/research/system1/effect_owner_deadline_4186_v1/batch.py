#!/usr/bin/env python3
import argparse,json,pathlib,time
import run

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--out',required=True); ap.add_argument('--rep',type=int,required=True,choices=[0,1,2]); a=ap.parse_args()
 root=pathlib.Path(a.out); root.mkdir(parents=True,exist_ok=False); rows=[]
 for sched in run.SCHEDULES:
  for policy in run.POLICIES:
   rows.append(run.run_case(root,policy,sched,a.rep,'formal2'))
 (root/'ROWS.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
 (root/'END.json').write_text(json.dumps({'rep':a.rep,'rows':len(rows),'exit':0,'end_ns':time.monotonic_ns()},indent=2,sort_keys=True)+'\n')
 print(json.dumps({'rep':a.rep,'rows':len(rows),'out':str(root)},sort_keys=True))
if __name__=='__main__': main()
