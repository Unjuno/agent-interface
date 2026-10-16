import subprocess,sys,json,time
from pathlib import Path
base=Path(sys.argv[1]);inp=base/'input';out=base/'output';name='wslc-typed-replay-a03-20261013';image='python@sha256:b9767f56a1cc620aa72d38cc3557d26412e38a4597c92953476136b78894ccbd';w='wslc.exe';cidfile=out/'container.cid'
cmd=[w,'run','--rm','--name',name,'--cidfile',str(cidfile),'--pull','never','--network','none','--memory','512M','--cpus','1','--volume',f'{inp}:/input:ro','--volume',f'{out}:/out:rw',image,'python','-B','/input/runner.py','/input/report.json','/input/events.jsonl','/input/observable_signal_guard_v2.py','/input/candidate.py','/input/auditor.py','/out']
def query(kind,value):
 q=subprocess.run([w,'container','list','--all','--filter',f'{kind}={value}','--format','json'],capture_output=True,timeout=10)
 (out/f'scoped-{kind}-query.stdout.bin').write_bytes(q.stdout);(out/f'scoped-{kind}-query.stderr.bin').write_bytes(q.stderr)
 text=q.stdout.decode('utf-8',errors='replace').strip()
 if q.returncode:return {'exit':q.returncode,'text':text,'verified':False,'rows':None}
 if not text or text=='[]':return {'exit':0,'text':text,'verified':True,'rows':[]}
 try: rows=json.loads(text)
 except Exception:return {'exit':0,'text':text,'verified':False,'rows':None}
 return {'exit':0,'text':text,'verified':isinstance(rows,list),'rows':rows if isinstance(rows,list) else None}
def fullcid():
 try:s=cidfile.read_text().strip()
 except OSError:return None
 return s if len(s)==64 and all(c in '0123456789abcdefABCDEF' for c in s) else None
def cleanup_id(cid):
 stop=subprocess.run([w,'container','stop','--time','2',cid],capture_output=True,timeout=10)
 remove=subprocess.run([w,'container','remove','--force',cid],capture_output=True,timeout=10)
 return {'stop_exit':stop.returncode,'stop_stdout':stop.stdout.decode('utf-8',errors='replace'),'stop_stderr':stop.stderr.decode('utf-8',errors='replace'),'remove_exit':remove.returncode,'remove_stdout':remove.stdout.decode('utf-8',errors='replace'),'remove_stderr':remove.stderr.decode('utf-8',errors='replace'),'absence':query('id',cid)}
started=time.time_ns();phase='run';proc=None;err=None;cleanup=None
try:
 proc=subprocess.run(cmd,capture_output=True,timeout=60)
 (out/'wslc.stdout.bin').write_bytes(proc.stdout);(out/'wslc.stderr.bin').write_bytes(proc.stderr)
except subprocess.TimeoutExpired as e:
 phase='host_timeout_60s';err='host subprocess deadline 60 seconds';(out/'wslc.stdout.bin').write_bytes(e.stdout or b'');(out/'wslc.stderr.bin').write_bytes(e.stderr or b'')
 cid=fullcid()
 if cid:cleanup=cleanup_id(cid)
 else:
  q=query('name',name);cleanup={'name_query':q,'targeted_action':'none; full ID unavailable'};rows=q.get('rows')
  if isinstance(rows,list) and len(rows)==1:
   row=rows[0];rid=row.get('id') or row.get('ID');rn=row.get('name') or row.get('Names');names=rn if isinstance(rn,list) else [rn]
   if isinstance(rid,str) and len(rid)==64 and any(str(x).lstrip('/')==name for x in names):cleanup['targeted_cleanup']=cleanup_id(rid)
except Exception as e:
 phase='launcher_error';err=repr(e);(out/'wslc.stdout.bin').write_bytes(b'');(out/'wslc.stderr.bin').write_bytes(err.encode('utf-8'))
cid=fullcid()
if phase=='run':
 if cid:
  try:cleanup={'id_query':query('id',cid)}
  except Exception as e:cleanup={'error':repr(e),'verified':False}
 else:
  try:
   q=query('name',name);cleanup={'name_query':q};rows=q.get('rows')
   if isinstance(rows,list) and len(rows)==1:
    row=rows[0];rid=row.get('id') or row.get('ID');rn=row.get('name') or row.get('Names');names=rn if isinstance(rn,list) else [rn]
    if isinstance(rid,str) and len(rid)==64 and any(str(x).lstrip('/')==name for x in names):cleanup['targeted_cleanup']=cleanup_id(rid)
  except Exception as e:cleanup={'error':repr(e),'verified':False}
absent=(cleanup or {}).get('id_query',{}).get('verified') is True
if isinstance(cleanup,dict) and cleanup.get('targeted_cleanup'):absent=cleanup['targeted_cleanup'].get('absence',{}).get('verified') is True
if isinstance(cleanup,dict) and cleanup.get('name_query'):absent=cleanup['name_query'].get('verified') is True and cleanup['name_query'].get('rows')==[]
receipt={'schema':'wslc-typed-policy-replay-run-receipt-v1','allocation':'WSLC-TYPED-POLICY-REPLAY-A03-20261013-01','phase':phase,'command':cmd,'container_name':name,'cid':cid,'started_ns':started,'finished_ns':time.time_ns(),'process_exit':None if proc is None else proc.returncode,'error':err,'cleanup':cleanup,'candidate_and_audit_outputs_present':(out/'candidate.json').is_file() and (out/'audit.json').is_file(),'scoped_container_absent':absent}
receipt['overall_scoped_pass']=phase=='run' and proc is not None and proc.returncode==0 and receipt['candidate_and_audit_outputs_present'] and absent
(out/'run-receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(receipt,indent=2,sort_keys=True));sys.exit(0 if receipt['overall_scoped_pass'] else 1)
