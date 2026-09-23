import argparse,copy,json,shutil,subprocess,sys,tempfile
from pathlib import Path
M=['observer_duration','observer_drop','case_summary','grab_time','ungrab_time','socket_leak','owner_exit','condition','repetition','xvfb_alive','kill_order','missing_grab']

def jread(p): return json.loads(p.read_text())
def jwrite(p,x): p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def first_dir(root, token): return sorted(p for p in root.iterdir() if p.is_dir() and token in p.name)[0]
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--schedule',required=True); ap.add_argument('--audit',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
 src=Path(a.root); results=[]
 for m in M:
  with tempfile.TemporaryDirectory() as td:
   dst=Path(td)/'formal'; shutil.copytree(src,dst)
   d=first_dir(dst,'HEALTHY_20MS')
   if m=='observer_duration':
    x=jread(d/'observer.json'); x['rows'][0]['duration_ns']+=1; jwrite(d/'observer.json',x)
   elif m=='observer_drop':
    x=jread(d/'observer.json'); x['rows'].pop(0); [r.__setitem__('i',i) for i,r in enumerate(x['rows'])]; jwrite(d/'observer.json',x)
   elif m=='case_summary':
    x=jread(d/'CASE.json'); x['max_spanning_duration_ns']+=1; jwrite(d/'CASE.json',x)
   elif m=='grab_time':
    p=d/'owner.events.jsonl'; xs=[json.loads(z) for z in p.read_text().splitlines() if z.strip()]
    next(z for z in xs if z['event']=='GRABBED')['grab_sync_end_ns']+=1; p.write_text(''.join(json.dumps(z,sort_keys=True)+'\n' for z in xs))
   elif m=='ungrab_time':
    p=d/'owner.events.jsonl'; xs=[json.loads(z) for z in p.read_text().splitlines() if z.strip()]
    next(z for z in xs if z['event']=='UNGRABBED')['ungrab_sync_end_ns']+=1; p.write_text(''.join(json.dumps(z,sort_keys=True)+'\n' for z in xs))
   elif m=='socket_leak':
    x=jread(d/'XSERVER_EXIT.json'); x['socket_exists_after']=True; jwrite(d/'XSERVER_EXIT.json',x)
   elif m=='owner_exit':
    x=jread(d/'CASE.json'); x['owner_returncode']=23; jwrite(d/'CASE.json',x)
   elif m=='condition':
    x=jread(d/'CASE.json'); x['condition']='NO_GRAB'; jwrite(d/'CASE.json',x)
   elif m=='repetition':
    x=jread(d/'CASE.json'); x['repetition']=99; jwrite(d/'CASE.json',x)
   elif m=='xvfb_alive':
    x=jread(d/'CASE.json'); x['xvfb_alive_at_score']=False; jwrite(d/'CASE.json',x)
   elif m=='kill_order':
    d=first_dir(dst,'KILL_OWNER_20MS'); x=jread(d/'CASE.json'); x['kill_signal_ns']=x['owner_death_observed_ns']+1; jwrite(d/'CASE.json',x)
   elif m=='missing_grab':
    p=d/'owner.events.jsonl'; xs=[json.loads(z) for z in p.read_text().splitlines() if z.strip() and json.loads(z).get('event')!='GRABBED']; p.write_text(''.join(json.dumps(z,sort_keys=True)+'\n' for z in xs))
   q=subprocess.run([sys.executable,a.audit,str(dst),'--schedule',a.schedule],text=True,capture_output=True)
   results.append({'mutation':m,'rejected':q.returncode!=0,'returncode':q.returncode})
 out={'controls':results,'rejected':sum(x['rejected'] for x in results),'total':len(results)}; jwrite(Path(a.out),out); print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if out['rejected']==len(M) else 1)
if __name__=='__main__': main()
