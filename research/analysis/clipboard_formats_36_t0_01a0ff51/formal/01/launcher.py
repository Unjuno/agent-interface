from pathlib import Path
import subprocess,json,hashlib,datetime,shutil,sys
TASK=Path('/Users/taka/Documents/Codex/2026-10-03/new-chat')
SRC=TASK/'work/agent-interface-36/research/analysis/clipboard_formats_36_t0_01a0ff51'
ROOT=SRC/'formal/01'
GUEST='research-clipboard-36-01a0ff51-docker'
IMAGE='sha256:9e9b1a232f08b8c437834f8a40a5b39ca4be9c66b953833170930c70fdc66d89'
SOURCE_COMMIT='9cc86468601c2b68e7b9bbb595f55b5bf47d92b4'
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
NAMES=['candidate.py','audit.py','gates.py','cases.json','oracle.json','Dockerfile','test_gates.py','test_audit.py','PREREGISTRATION.md']
PINS={name:sha(SRC/name) for name in NAMES}
ROOT.mkdir(parents=True,exist_ok=False)
(ROOT/'audit').mkdir()
def write(name,value):(ROOT/name).write_text(json.dumps(value,indent=2)+'\n')
freeze={'allocation':'CLIPBOARD-FORMATS-36-QT-T0-20261003-01','policy':'FINAL-v5','worker':'01a0ff51-d447-7cb3-bb02-36d7e1d30b28','frozen_at':now(),'source_commit':SOURCE_COMMIT,'base_main':'f1416985d4ff9ce5bbf9f0f4be1be3d0ee669549','source_sha256':PINS,'image_id':IMAGE,'guest':GUEST,'candidate_limit':1,'audit_limit':1,'retries':0,'output_cap_bytes':1048576,'planned_outputs':['candidate/raw.json','candidate/C01-C12/{text.txt,document.html}','audit/audit.json'],'scope':'Qt offscreen diagnostic classifiers; no OS input/model/native clipboard','common_deadline':'unconfirmed; this allocation sets no fleet deadline'}
write('FREEZE.json',freeze)
PREFIX=['orb','run','-m',GUEST,'-u','root','docker']
def call(args,stdout=None,stderr=None):
 r=subprocess.run(args,capture_output=True,timeout=60)
 if stdout:(ROOT/stdout).write_bytes(r.stdout)
 if stderr:(ROOT/stderr).write_bytes(r.stderr)
 return r
image=call(PREFIX+['image','inspect',IMAGE]);(ROOT/'image-inspect.json').write_bytes(image.stdout)
if image.returncode!=0 or json.loads(image.stdout)[0]['Id']!=IMAGE:raise RuntimeError('STOP_IMAGE')
write('sources-pre.json',{n:sha(SRC/n) for n in NAMES})
for name in ('host-os.txt','host-hardware.txt','guest2-info.json','docker-version.txt'):shutil.copy2(TASK/'work/clipboard-36'/name,ROOT/name)
receipt={'allocation':freeze['allocation'],'started':now(),'operations':[],'candidate_invocations':0,'audit_invocations':0,'status':'RUNNING'}
write('RUN_RECEIPT.json',receipt)
def stage(kind,name,args,mounts):
 cmd=PREFIX+['create','--name',name,'--pull','never','--network','none','--cpus','0.25','--memory','256m','--pids-limit','64','--read-only','--tmpfs','/tmp:rw,nosuid,noexec,size=32m']
 for m in mounts:cmd+=['--mount',m]
 cmd += [IMAGE]+args
 op={'kind':kind,'target_container':name,'planned_create_command':cmd,'planned_start_command':PREFIX+['start','-a',name],'started':now()}
 receipt['operations'].append(op);write('RUN_RECEIPT.json',receipt)
 r=call(cmd,kind+'.create.stdout',kind+'.create.stderr');op['create_exit']=r.returncode
 if r.returncode!=0:raise RuntimeError('STOP_CREATE_'+kind)
 pre=call(PREFIX+['inspect',name]);(ROOT/(kind+'.inspect-pre.json')).write_bytes(pre.stdout)
 receipt[kind+'_invocations']+=1;write('RUN_RECEIPT.json',receipt)
 r=call(PREFIX+['start','-a',name],kind+'.stdout',kind+'.stderr')
 op['client_exit']=r.returncode;op['finished']=now()
 post=call(PREFIX+['inspect',name]);(ROOT/(kind+'.inspect-post.json')).write_bytes(post.stdout)
 state=json.loads(post.stdout)[0]['State'];op['container_exit']=state['ExitCode'];op['running']=state['Running']
 write('RUN_RECEIPT.json',receipt)
 if r.returncode!=0 or state['ExitCode']!=0 or state['Running']:raise RuntimeError('FAIL_PROCESS_'+kind)
mountsrc='type=bind,src=/mnt/mac'+str(SRC)+',dst=/src,readonly'
try:
 stage('candidate','clipboard36-formal01-candidate',['/src/candidate.py','--cases','/src/cases.json','--output','/out/candidate'],[mountsrc,'type=bind,src=/mnt/mac'+str(ROOT)+',dst=/out'])
 stage('audit','clipboard36-formal01-audit',['/src/audit.py','--oracle','/src/oracle.json','--raw','/raw/raw.json','--output','/out/audit.json'],[mountsrc,'type=bind,src=/mnt/mac'+str(ROOT/'candidate')+',dst=/raw,readonly','type=bind,src=/mnt/mac'+str(ROOT/'audit')+',dst=/out'])
 postpins={n:sha(SRC/n) for n in NAMES};write('sources-post.json',postpins)
 if postpins!=PINS:raise RuntimeError('FAIL_SOURCE_CHANGED')
 total=sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())
 if total>freeze['output_cap_bytes']:raise RuntimeError('FAIL_OUTPUT_CAP')
 result=json.loads((ROOT/'audit/audit.json').read_text())
 receipt['status']=result['status'];receipt['output_bytes_before_final_receipt']=total
except Exception as e:
 receipt['status']=str(e);receipt['exception_type']=type(e).__name__
finally:
 receipt['finished']=now();write('RUN_RECEIPT.json',receipt)
 print(json.dumps({'status':receipt['status'],'candidate':receipt['candidate_invocations'],'audit':receipt['audit_invocations'],'outputs':str(ROOT)}))
if receipt['status']!='PASS_METHOD_SCOPED':sys.exit(1)
