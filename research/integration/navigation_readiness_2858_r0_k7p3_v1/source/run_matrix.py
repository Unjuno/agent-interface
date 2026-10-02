import argparse,json,os,subprocess,sys,time
from pathlib import Path
POL=['NO_EXTRA_WAIT','FIXED_100MS','REOBSERVE_ACTIVE']; LOAD=['IDLE','CONTENDED']; PHASE=['FRESH','SEQUENTIAL']
# Prospectively fixed order rotates policy across each stratum/repetition.
SCHEDULE=[]
for rep in range(2):
 for ph in PHASE:
  for load in LOAD:
   order=POL[rep:]+POL[:rep]
   if (ph=='SEQUENTIAL')^(load=='CONTENDED'): order=list(reversed(order))
   for pol in order: SCHEDULE.append((f'r{rep}-{ph.lower()}-{load.lower()}-{pol.lower()}',pol,load,ph))
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--display-base',type=int,default=380); a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=False); cpu=sorted(os.sched_getaffinity(0))[0]; rows=[]
 for j,(cid,pol,load,ph) in enumerate(SCHEDULE):
  cmd=[sys.executable,'-B',str(Path(__file__).with_name('run_case.py')),'--out',str(a.out/cid),'--case-id',cid,'--policy',pol,'--load',load,'--phase',ph,'--display',str(a.display_base+j),'--cpu',str(cpu)]
  st=time.monotonic_ns(); cp=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=40); row={'case_id':cid,'policy':pol,'load':load,'phase':ph,'command':cmd,'returncode':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr,'started_ns':st,'ended_ns':time.monotonic_ns()}; rows.append(row); (a.out/'LAUNCHER.json').write_text(json.dumps(rows,indent=2)+'\n')
  if cp.returncode!=0: return cp.returncode
 return 0
if __name__=='__main__': raise SystemExit(main())
