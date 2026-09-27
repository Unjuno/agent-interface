from __future__ import annotations
import argparse,hashlib,importlib.util,json,os,subprocess,sys,tempfile,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
TASK='P0-LIVE-CAUSAL-EFFECT-X11-STACK-DURABLE-A5-20260918-005';ISSUE=1324;BRANCH='research/p0-live-causal-effect-stack-durable-stderr-a5-20260918-005'
SCIENCE=HERE/'science_runner.py';SCIENCE_BLOB='d8c509a55fe5363dc5211aebe510a720e964f7f3';W=320;H=240

def git_blob(p):
    b=Path(p).read_bytes();return hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()
def sha256_bytes(b):return hashlib.sha256(b).hexdigest()
def load_json(p):return json.loads(Path(p).read_text())
def load_science():
    n='science_summary_1324';s=importlib.util.spec_from_file_location(n,SCIENCE);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def wait_socket(n,present=True,timeout=5):
    p=Path(f'/tmp/.X11-unix/X{n}');end=time.monotonic()+timeout
    while time.monotonic()<end:
        if p.exists()==present:return
        time.sleep(.01)
    raise RuntimeError(('socket did not appear ' if present else 'socket did not disappear ')+str(n))
def durable_json(path,obj):
    p=Path(path)
    with p.open('w') as f:
        json.dump(obj,f,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
def check_grant(p,s):
    g=load_json(p)
    for k,v in {'authorized':True,'task':TASK,'issue':ISSUE,'branch':BRANCH}.items():
        if g.get(k)!=v:raise RuntimeError('grant '+k)
    if not isinstance(g.get('grant_comment_id'),int):raise RuntimeError('grant id')
    if (s.get('pairs'),s.get('sessions'),s.get('hold_ms'))!=(6,12,150):raise RuntimeError('schedule')
    return g

def app_ok(r):return [(x.get('kind'),x.get('key')) for x in r.get('application_events',[])]==[('KeyPress','F8'),('KeyRelease','F8')]
def phys_ok(r):
    try:
        d=r['down_result']['physical_key_measurement'];u=r['up_result']['physical_key_measurement']
        return d['classification']=='CONFIRMED_PHYSICAL_DOWN' and u['classification']=='CONFIRMED_PHYSICAL_UP' and r['composition']['status']=='COMPOSED_PHYSICAL_ACTUATION'
    except Exception:return False
def lineage_ok(r):
    try:
        aid=r['composition']['actuation']['actuation_id'];e=r['effect_records'];return len(e)==1 and e[0]['actuation_id']==aid and bool(aid)
    except Exception:return False
def temporal_ok(r):
    try:
        e=r['temporal_analysis']['effects'];return r['clock_disposition']=='useful_bound' and e['useful_bound']==1 and all(e[k]==0 for k in e if k!='useful_bound')
    except Exception:return False
def safe_summary(rows):
    eff=[r for r in rows if r.get('arm')=='V12_EFFECT'];ctl=[r for r in rows if r.get('arm')=='NO_ACTION_CONTROL']
    return {'sessions':len(rows),'effect_sessions':len(eff),'control_sessions':len(ctl),
            'effect_application_ok':sum(bool(app_ok(r)) for r in eff),'effect_physical_ok':sum(bool(phys_ok(r)) for r in eff),
            'effect_lineage_ok':sum(bool(lineage_ok(r)) for r in eff),'effect_independent_score_ok':sum(bool(r.get('pre_left') and r.get('post_goal')) for r in eff),
            'effect_temporal_clock_ok':sum(bool(temporal_ok(r)) for r in eff),'effect_terminal_up':sum(r.get('terminal_key_down') is False for r in eff),
            'control_no_effect_ok':sum(bool(r.get('pre_left') and r.get('post_left') and not r.get('effect_records') and not r.get('application_events')) for r in ctl),
            'child_failures':sum(r.get('supervisor_cleanup',{}).get('child_exit_code')!=0 for r in rows),
            'exceptions':sum(len(r.get('exceptions',[]))+len(r.get('controller_errors',[])) for r in rows)}

def run_case(root,repo_root,arm,pair,position,display_num):
    root=Path(root);sup=root/f'supervisor_pair{pair:02d}_{position}_{arm}';sup.mkdir(parents=True,exist_ok=False)
    if Path(f'/tmp/.X11-unix/X{display_num}').exists():raise RuntimeError('display collision')
    auth=sup/'Xauthority';auth.write_bytes(b'');os.chmod(auth,0o600);env=os.environ.copy();env['XAUTHORITY']=str(auth);env['DISPLAY']=f':{display_num}'
    xv=subprocess.Popen(['Xvfb',f':{display_num}','-screen','0',f'{W}x{H}x24','-nolisten','tcp','-ac'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,env=env)
    row=None;child_out=sup/'row.json';status_path=sup/'child_status.json';supervisor_row=sup/'supervisor_row.json'
    stdout_path=sup/'child.stdout.log';stderr_path=sup/'child.stderr.log'
    status={'arm':arm,'pair':pair,'position':position,'display_num':display_num,'timeout':False,'returncode':None,'row_exists':False,
            'stdout_path':str(stdout_path),'stderr_path':str(stderr_path),'stdout_bytes':0,'stderr_bytes':0,'stdout_sha256':None,'stderr_sha256':None,
            'stdout_tail':'','stderr_tail':''}
    try:
        wait_socket(display_num,True)
        cmd=[sys.executable,str(HERE/'case_child.py'),'--repo-root',str(repo_root),'--case-root',str(root/'case_rows'),'--arm',arm,'--pair',str(pair),'--position',str(position),'--display-num',str(display_num),'--out',str(child_out)]
        with stdout_path.open('wb') as so, stderr_path.open('wb') as se:
            try:
                cp=subprocess.run(cmd,stdout=so,stderr=se,timeout=8,env=env)
                status['returncode']=cp.returncode
            except subprocess.TimeoutExpired:
                status['timeout']=True;status['returncode']=None
            finally:
                so.flush();os.fsync(so.fileno());se.flush();os.fsync(se.fileno())
        stdout_bytes=stdout_path.read_bytes();stderr_bytes=stderr_path.read_bytes()
        status.update(row_exists=child_out.exists(),
                      stdout_bytes=len(stdout_bytes),stderr_bytes=len(stderr_bytes),
                      stdout_sha256=sha256_bytes(stdout_bytes),stderr_sha256=sha256_bytes(stderr_bytes),
                      stdout_tail=stdout_bytes[-8000:].decode('utf-8','replace'),
                      stderr_tail=stderr_bytes[-8000:].decode('utf-8','replace'))
        durable_json(status_path,status)
        if status['returncode']==0 and status['row_exists']:row=load_json(child_out)
        else:row={'pair':pair,'position':position,'arm':arm,'exceptions':['session_child_incomplete'],'controller_errors':[]}
        row['diagnostic_status']=status
        row['supervisor_cleanup']={'child_exit_code':status['returncode'],'server_pid':xv.pid,'socket_exists_before_server_stop':Path(f'/tmp/.X11-unix/X{display_num}').exists()}
    finally:
        if xv.poll() is None:
            xv.terminate()
            try:xv.wait(timeout=.5)
            except subprocess.TimeoutExpired:xv.kill();xv.wait()
        try:wait_socket(display_num,False,1)
        except Exception:pass
        if row is None:row={'pair':pair,'position':position,'arm':arm,'exceptions':['no_row'],'controller_errors':[],'diagnostic_status':status,'supervisor_cleanup':{}}
        sc=row.setdefault('supervisor_cleanup',{});sc['xvfb_exit_code']=xv.poll();sc['socket_exists_after_server_stop']=Path(f'/tmp/.X11-unix/X{display_num}').exists();sc['clients_exit_before_server_stop']=sc.get('child_exit_code')==0
        if 'cleanup' in row:row['inner_cleanup']=row.pop('cleanup')
        row['cleanup']={'child_exit_code':sc.get('child_exit_code'),'xvfb_exit_code':xv.poll(),'socket_exists_after':sc['socket_exists_after_server_stop']}
        durable_json(supervisor_row,row)
    return row

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--schedule',required=True);ap.add_argument('--repo-root',required=True);ap.add_argument('--grant');ap.add_argument('--out');ap.add_argument('--construction',action='store_true');ap.add_argument('--static-self-test',action='store_true');a=ap.parse_args()
    schedule=load_json(a.schedule)
    if git_blob(SCIENCE)!=SCIENCE_BLOB:raise RuntimeError('science runner drift')
    science=load_science()
    if a.static_self_test:
        with tempfile.TemporaryDirectory(prefix='ai1324-static-') as td:deps=science.source_gate(a.repo_root,td)
        synthetic=[{'arm':'NO_ACTION_CONTROL','pre_left':True,'post_left':True,'effect_records':[],'application_events':[],'exceptions':[],'controller_errors':[],'supervisor_cleanup':{'child_exit_code':0}}, {'arm':'V12_EFFECT','exceptions':['synthetic-failure'],'controller_errors':[],'supervisor_cleanup':{'child_exit_code':1}}]
        print(json.dumps({'pass':True,'live_sessions':0,'science_runner_blob':git_blob(SCIENCE),'failure_tolerant_summary':safe_summary(synthetic),'source_gate':deps},sort_keys=True));return
    if not a.grant or not a.out:raise SystemExit('live requires grant/out')
    grant=check_grant(a.grant,schedule);out=Path(a.out)
    if out.exists():raise SystemExit('result exists')
    root=out.parent/'sessions';root.mkdir(parents=True,exist_ok=False);(root/'case_rows').mkdir()
    orders=[['NO_ACTION_CONTROL','V12_EFFECT']] if a.construction else schedule['pair_orders'];n=2400 if a.construction else 2420;rows=[]
    for pair,order in enumerate(orders,1):
        for pos,arm in enumerate(order,1):rows.append(run_case(root,a.repo_root,arm,pair,pos,n));n+=1
    result={'task':TASK,'issue':ISSUE,'branch':BRANCH,'phase':'construction' if a.construction else 'formal','formal_invocations':0 if a.construction else 1,'reruns':0,'grant_comment_id':grant['grant_comment_id'],'schedule':schedule,'science_runner_blob':git_blob(SCIENCE),'rows':rows,'summary':safe_summary(rows)}
    durable_json(out,result);print(json.dumps(result['summary'],sort_keys=True))
if __name__=='__main__':main()
