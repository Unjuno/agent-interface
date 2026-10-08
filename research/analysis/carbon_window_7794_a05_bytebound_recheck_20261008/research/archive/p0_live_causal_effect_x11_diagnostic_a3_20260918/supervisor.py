from __future__ import annotations
import argparse,hashlib,importlib.util,json,os,subprocess,sys,tempfile,time
from pathlib import Path

HERE=Path(__file__).resolve().parent
TASK='P0-LIVE-CAUSAL-EFFECT-X11-DIAGNOSTIC-A3-20260918-003'
ISSUE=1310
BRANCH='research/p0-live-causal-effect-diagnostic-a3-20260918-003'
SCIENCE=HERE/'science_runner.py'
SCIENCE_BLOB='d8c509a55fe5363dc5211aebe510a720e964f7f3'
W=320;H=240

def git_blob(p):
    b=Path(p).read_bytes();return hashlib.sha1(f'blob {len(b)}\\0'.encode()+b).hexdigest()
def load_json(p):return json.loads(Path(p).read_text())
def write_json(p,obj):Path(p).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\\n')
def load_science():
    n='science_summary_1310';s=importlib.util.spec_from_file_location(n,SCIENCE);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m

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

def safe_summary(science,rows):
    complete=all(r.get('science_row_present') is True for r in rows)
    base={'sessions':len(rows),'complete_science_rows':sum(r.get('science_row_present') is True for r in rows),
          'failed_or_missing_rows':sum(r.get('science_row_present') is not True for r in rows),
          'science_eligible':False,'science_summary':None,'summary_error':None}
    if not complete:return base
    clean=[]
    for r in rows:
        q=dict(r);q.pop('science_row_present',None);q.pop('child_status_path',None);q.pop('supervisor_row_path',None)
        clean.append(q)
    try:
        base['science_summary']=science.summarize(clean);base['science_eligible']=True
    except BaseException as e:
        base['summary_error']=type(e).__name__+': '+str(e)
    return base

def run_case(root,repo_root,arm,pair,position,display_num):
    root=Path(root);sup=root/f'supervisor_pair{pair:02d}_{position}_{arm}';sup.mkdir(parents=True,exist_ok=False)
    if Path(f'/tmp/.X11-unix/X{display_num}').exists():raise RuntimeError('display collision')
    auth=sup/'Xauthority';auth.write_bytes(b'');os.chmod(auth,0o600)
    env=os.environ.copy();env['XAUTHORITY']=str(auth);env['DISPLAY']=f':{display_num}'
    xv=subprocess.Popen(['Xvfb',f':{display_num}','-screen','0',f'{W}x{H}x24','-nolisten','tcp','-ac'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,env=env)
    child_out=sup/'row.json';status_path=sup/'child_status.json';supervisor_path=sup/'supervisor_row.json'
    row=None;status={'arm':arm,'pair':pair,'position':position,'display_num':display_num,'timeout':False,
                     'exit_code':None,'stdout_tail':'','stderr_tail':'','row_exists':False}
    try:
        wait_socket(display_num,True)
        cmd=[sys.executable,str(HERE/'case_child.py'),'--repo-root',str(repo_root),'--case-root',str(root/'case_rows'),
             '--arm',arm,'--pair',str(pair),'--position',str(position),'--display-num',str(display_num),'--out',str(child_out)]
        try:
            child=subprocess.run(cmd,capture_output=True,text=True,timeout=8,env=env)
            status.update({'exit_code':child.returncode,'stdout_tail':child.stdout[-4000:],
                           'stderr_tail':child.stderr[-4000:],'row_exists':child_out.exists()})
        except subprocess.TimeoutExpired as e:
            status.update({'timeout':True,'exit_code':None,
                           'stdout_tail':(e.stdout or '')[-4000:] if isinstance(e.stdout,str) else '',
                           'stderr_tail':(e.stderr or '')[-4000:] if isinstance(e.stderr,str) else '',
                           'row_exists':child_out.exists()})
        # Critical A3 ordering: persist process diagnostics before any row read/aggregation.
        write_json(status_path,status)
        if status['exit_code']==0 and status['row_exists']:
            row=load_json(child_out);row['science_row_present']=True
        else:
            row={'pair':pair,'position':position,'arm':arm,'exceptions':['session_child_incomplete'],
                 'controller_errors':[],'science_row_present':False}
        row['supervisor_child_stdout']=status['stdout_tail'];row['supervisor_child_stderr']=status['stderr_tail']
        row['supervisor_cleanup']={'child_exit_code':status['exit_code'],'child_pid':None,'row_pid':row.get('pid'),
                                   'server_pid':xv.pid,'socket_exists_before_server_stop':Path(f'/tmp/.X11-unix/X{display_num}').exists()}
    except BaseException as e:
        if not status_path.exists():
            status['stderr_tail']=type(e).__name__+': '+str(e);status['row_exists']=child_out.exists();write_json(status_path,status)
        row={'pair':pair,'position':position,'arm':arm,'exceptions':['supervisor_exception:'+type(e).__name__+': '+str(e)],
             'controller_errors':[],'science_row_present':False,'supervisor_cleanup':{}}
    finally:
        if xv.poll() is None:
            xv.terminate()
            try:xv.wait(timeout=.5)
            except subprocess.TimeoutExpired:xv.kill();xv.wait()
        try:wait_socket(display_num,False,1)
        except Exception:pass
        if row is None:row={'pair':pair,'position':position,'arm':arm,'exceptions':['no_row'],'controller_errors':[],'science_row_present':False,'supervisor_cleanup':{}}
        row.setdefault('supervisor_cleanup',{})['xvfb_exit_code']=xv.poll()
        row['supervisor_cleanup']['socket_exists_after_server_stop']=Path(f'/tmp/.X11-unix/X{display_num}').exists()
        row['supervisor_cleanup']['clients_exit_before_server_stop']=row['supervisor_cleanup'].get('child_exit_code')==0
        if 'cleanup' in row:row['inner_cleanup']=row.pop('cleanup')
        row['cleanup']={'child_exit_code':row['supervisor_cleanup'].get('child_exit_code'),'xvfb_exit_code':xv.poll(),
                        'socket_exists_after':row['supervisor_cleanup']['socket_exists_after_server_stop']}
        row['child_status_path']=str(status_path);row['supervisor_row_path']=str(supervisor_path)
        write_json(supervisor_path,row)
    return row

def static_diagnostic_self_test(science):
    incomplete={'arm':'V12_EFFECT','pair':1,'position':2,'science_row_present':False}
    s=safe_summary(science,[incomplete])
    if s['science_eligible'] or s['failed_or_missing_rows']!=1 or s['summary_error'] is not None:raise RuntimeError('safe summary incomplete')
    return {'safe_missing_row':True,'science_runner_blob':git_blob(SCIENCE)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--schedule',required=True);ap.add_argument('--repo-root',required=True)
    ap.add_argument('--grant');ap.add_argument('--out');ap.add_argument('--construction',action='store_true');ap.add_argument('--static-self-test',action='store_true');a=ap.parse_args()
    schedule=load_json(a.schedule)
    if git_blob(SCIENCE)!=SCIENCE_BLOB:raise RuntimeError('science runner drift')
    science=load_science()
    if a.static_self_test:
        with tempfile.TemporaryDirectory(prefix='ai1310-static-') as td:deps=science.source_gate(a.repo_root,td)
        print(json.dumps({'pass':True,'live_sessions':0,'source_gate':deps,'diagnostic':static_diagnostic_self_test(science)},sort_keys=True));return
    if not a.grant or not a.out:raise SystemExit('live requires grant/out')
    grant=check_grant(a.grant,schedule);out=Path(a.out)
    if out.exists():raise SystemExit('result exists')
    root=out.parent/'sessions';root.mkdir(parents=True,exist_ok=False);(root/'case_rows').mkdir()
    orders=[['NO_ACTION_CONTROL','V12_EFFECT']] if a.construction else schedule['pair_orders']
    n=2300 if a.construction else 2320;rows=[]
    for pair,order in enumerate(orders,1):
        for pos,arm in enumerate(order,1):
            rows.append(run_case(root,a.repo_root,arm,pair,pos,n));n+=1
    result={'task':TASK,'issue':ISSUE,'branch':BRANCH,'phase':'construction' if a.construction else 'formal',
            'formal_invocations':0 if a.construction else 1,'reruns':0,'grant_comment_id':grant['grant_comment_id'],
            'schedule':schedule,'science_runner_blob':git_blob(SCIENCE),'rows':rows,'summary':safe_summary(science,rows)}
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result['summary'],sort_keys=True))
if __name__=='__main__':main()
