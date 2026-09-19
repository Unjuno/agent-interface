from __future__ import annotations
import argparse,hashlib,importlib.util,json,os,subprocess,sys,tempfile,time
from pathlib import Path

HERE=Path(__file__).resolve().parent
TASK='P0-LIVE-CAUSAL-EFFECT-X11-TEARDOWN-A2-20260918-002'
ISSUE=1301
BRANCH='research/p0-live-causal-effect-x11-teardown-a2-1301'
SCIENCE=HERE/'science_runner.py'
SCIENCE_BLOB='d8c509a55fe5363dc5211aebe510a720e964f7f3'
W=320;H=240

def git_blob(p):
    b=Path(p).read_bytes();return hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()
def load_json(p):return json.loads(Path(p).read_text())
def load_science():
    n='science_summary_1301';s=importlib.util.spec_from_file_location(n,SCIENCE);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m

def wait_socket(n,present=True,timeout=5):
    p=Path(f'/tmp/.X11-unix/X{n}');end=time.monotonic()+timeout
    while time.monotonic()<end:
        if p.exists()==present:return
        time.sleep(.01)
    raise RuntimeError(('socket did not appear ' if present else 'socket did not disappear ')+str(n))

def check_grant(p,s):
    g=load_json(p)
    for k,v in {'authorized':True,'task':TASK,'issue':ISSUE,'branch':BRANCH}.items():
        if g.get(k)!=v:raise RuntimeError('grant '+k)
    if not isinstance(g.get('grant_comment_id'),int):raise RuntimeError('grant id')
    if (s.get('pairs'),s.get('sessions'),s.get('hold_ms'))!=(6,12,150):raise RuntimeError('schedule')
    return g

def run_case(root,repo_root,arm,pair,position,display_num):
    root=Path(root);sup=root/f'supervisor_pair{pair:02d}_{position}_{arm}';sup.mkdir(parents=True,exist_ok=False)
    if Path(f'/tmp/.X11-unix/X{display_num}').exists():raise RuntimeError('display collision')
    auth=sup/'Xauthority';auth.write_bytes(b'');os.chmod(auth,0o600)
    env=os.environ.copy();env['XAUTHORITY']=str(auth);env['DISPLAY']=f':{display_num}'
    xv=subprocess.Popen(['Xvfb',f':{display_num}','-screen','0',f'{W}x{H}x24','-nolisten','tcp','-ac'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,env=env)
    child=None;row=None;child_out=sup/'row.json';stdout='';stderr=''
    try:
        wait_socket(display_num,True)
        cmd=[sys.executable,str(HERE/'case_child.py'),'--repo-root',str(repo_root),'--case-root',str(root/'case_rows'),
             '--arm',arm,'--pair',str(pair),'--position',str(position),'--display-num',str(display_num),'--out',str(child_out)]
        child=subprocess.run(cmd,capture_output=True,text=True,timeout=8,env=env)
        stdout=child.stdout;stderr=child.stderr
        if child.returncode==0 and child_out.exists():row=load_json(child_out)
        else:
            row={'pair':pair,'position':position,'arm':arm,'exceptions':['session_child_failed'], 'controller_errors':[]}
        row['supervisor_child_stdout']=stdout[-4000:];row['supervisor_child_stderr']=stderr[-4000:]
        row['supervisor_cleanup']={'child_exit_code':child.returncode,'child_pid':None,'row_pid':row.get('pid'),
                                   'server_pid':xv.pid,'socket_exists_before_server_stop':Path(f'/tmp/.X11-unix/X{display_num}').exists()}
    except subprocess.TimeoutExpired as e:
        row={'pair':pair,'position':position,'arm':arm,'exceptions':['session_child_timeout'], 'controller_errors':[],
             'supervisor_child_stdout':(e.stdout or '')[-4000:] if isinstance(e.stdout,str) else '',
             'supervisor_child_stderr':(e.stderr or '')[-4000:] if isinstance(e.stderr,str) else '',
             'supervisor_cleanup':{'child_exit_code':None,'server_pid':xv.pid,'socket_exists_before_server_stop':Path(f'/tmp/.X11-unix/X{display_num}').exists()}}
    finally:
        if xv.poll() is None:
            xv.terminate()
            try:xv.wait(timeout=.5)
            except subprocess.TimeoutExpired:xv.kill();xv.wait()
        try:wait_socket(display_num,False,1)
        except Exception:pass
        if row is None:row={'pair':pair,'position':position,'arm':arm,'exceptions':['no_row'],'controller_errors':[],'supervisor_cleanup':{}}
        row.setdefault('supervisor_cleanup',{})['xvfb_exit_code']=xv.poll()
        row['supervisor_cleanup']['socket_exists_after_server_stop']=Path(f'/tmp/.X11-unix/X{display_num}').exists()
        row['supervisor_cleanup']['clients_exit_before_server_stop']=row['supervisor_cleanup'].get('child_exit_code')==0
        if 'cleanup' in row:
            row['inner_cleanup']=row.pop('cleanup')
        row['cleanup']={'child_exit_code':row['supervisor_cleanup'].get('child_exit_code'),
                        'xvfb_exit_code':xv.poll(),'socket_exists_after':row['supervisor_cleanup']['socket_exists_after_server_stop']}
    return row

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--schedule',required=True);ap.add_argument('--repo-root',required=True)
    ap.add_argument('--grant');ap.add_argument('--out');ap.add_argument('--construction',action='store_true');ap.add_argument('--static-self-test',action='store_true');a=ap.parse_args()
    schedule=load_json(a.schedule)
    if git_blob(SCIENCE)!=SCIENCE_BLOB:raise RuntimeError('science runner drift')
    science=load_science()
    if a.static_self_test:
        with tempfile.TemporaryDirectory(prefix='ai1301-static-') as td:deps=science.source_gate(a.repo_root,td)
        print(json.dumps({'pass':True,'live_sessions':0,'science_runner_blob':git_blob(SCIENCE),'source_gate':deps},sort_keys=True));return
    if not a.grant or not a.out:raise SystemExit('live requires grant/out')
    grant=check_grant(a.grant,schedule);out=Path(a.out)
    if out.exists():raise SystemExit('result exists')
    root=out.parent/'sessions';root.mkdir(parents=True,exist_ok=False);(root/'case_rows').mkdir()
    orders=[['NO_ACTION_CONTROL','V12_EFFECT']] if a.construction else schedule['pair_orders']
    n=2200 if a.construction else 2220;rows=[]
    for pair,order in enumerate(orders,1):
        for pos,arm in enumerate(order,1):
            rows.append(run_case(root,a.repo_root,arm,pair,pos,n));n+=1
    result={'task':TASK,'issue':ISSUE,'branch':BRANCH,'phase':'construction' if a.construction else 'formal',
            'formal_invocations':0 if a.construction else 1,'reruns':0,'grant_comment_id':grant['grant_comment_id'],
            'schedule':schedule,'science_runner_blob':git_blob(SCIENCE),'rows':rows,'summary':science.summarize(rows)}
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result['summary'],sort_keys=True))
if __name__=='__main__':main()
