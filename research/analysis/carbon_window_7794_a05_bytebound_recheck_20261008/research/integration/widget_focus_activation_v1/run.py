"""Bounded existing-backend activation recipe experiment; private display only."""
import argparse, hashlib, json, os, secrets, signal, subprocess, sys, time, traceback
from pathlib import Path
from Xlib import X, display
from support import App, identity, xstate, write
from loader import load_backend
ROOT=Path(__file__).resolve().parent
ROUTES=['TOPLEVEL_FOCUS','CHILD_XID_FOCUS','CLICK_ENTRY']
STATES=['STABLE_A','B_BEFORE_ACTIVATION','B_AFTER_ACTIVATION']
def freeze_check():
    data=(ROOT/'FREEZE.json').read_bytes(); f=json.loads(data)
    for name,digest in f['sha256'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest: raise RuntimeError('source changed '+name)
    return hashlib.sha256(data).hexdigest()
def cases(batch,construction):
    if construction: return [(r,s) for s in STATES for r in ROUTES]
    routes=ROUTES[batch:]+ROUTES[:batch]
    return [(r,s) for s in STATES for r in routes]+[('NO_INPUT','STABLE_A')]
def one(out,env,route,state,payload):
    out.mkdir(); app=backend=observer=None
    row={'case':out.name,'route':route,'state':state,'payload':payload,'snapshots':{},'server':{},'complete':False}
    try:
        app=App(out,env,str(out.relative_to(ROOT))); row['ready']=app.ready; ready=app.ready['snapshot']
        row['app_identity']=app.identity
        observer=display.Display(env['DISPLAY']); root=observer.screen().root
        wrapper=observer.create_resource_object('window',ready['client_xid']).query_tree().parent
        row['ancestry']={'client_xid':ready['client_xid'],'reported_frame_xid':ready['xid'],'client_parent':wrapper.id,'wrapper_parent':wrapper.query_tree().parent.id,'root':root.id,'natural_focus':getattr(observer.get_input_focus().focus,'id',None)}
        if row['ancestry']['wrapper_parent']!=root.id or row['ancestry']['natural_focus']!=wrapper.id: raise RuntimeError('target ancestry')
        row['wrapper']=wrapper.id; row['entry_a']=ready['widget_ids']['a']; row['entry_b']=ready['widget_ids']['b']
        entry=observer.create_resource_object('window',row['entry_a']); eg=entry.get_geometry(); et=root.translate_coords(entry,0,0)
        row['entry_geometry']=[et.x,et.y,eg.width,eg.height]
        row['click_point']=[et.x+eg.width//2,et.y+eg.height//2]
        backend=load_backend()(env['DISPLAY'],{'window':wrapper.id,'entry':row['entry_a']})
        def snap(label):
            row['snapshots'][label]=app.call('observe')
            row['server'][label]=xstate(observer,wrapper.id)
        snap('prepared')
        if row['snapshots']['prepared']['snapshot']['focus_widget']!='.a': raise RuntimeError('initial recipient')
        if state=='B_BEFORE_ACTIVATION': row['mutation']=app.call('focus_b')
        snap('before_activation')
        if route=='NO_INPUT': ops=[]
        elif route=='CHILD_XID_FOCUS': ops=[{'op':'focus','target':'entry'}]
        else:
            ops=[{'op':'focus','target':'window'}]
            if route=='CLICK_ENTRY':
                x,y=row['click_point'];ops += [{'op':'pointer_move','frame':'screen_physical_px','x':x,'y':y}, {'op':'pointer_button','button':'left','down':True}, {'op':'pointer_button','button':'left','down':False}, {'op':'release_all'}]
        row['activation_program']={'ops':ops}
        row['activation_started_ns']=time.monotonic_ns()
        row['activation']=backend.execute(row['activation_program']) if ops else None
        row['activation_returned_ns']=time.monotonic_ns()
        row['server']['activation_return']=xstate(observer,wrapper.id)
        snap('after_activation')
        if state=='B_AFTER_ACTIVATION': row['mutation']=app.call('focus_b')
        snap('before_text')
        row['text_program']={'ops':[{'op':'text','text':payload},{'op':'release_all'}]}
        row['text_started_ns']=time.monotonic_ns()
        row['text']=backend.execute(row['text_program']) if route!='NO_INPUT' else None
        row['text_returned_ns']=time.monotonic_ns()
        snap('final')
        geo=row['server']['final']['geometry'];image=wrapper.get_image(0,0,geo[2],geo[3],X.ZPixmap,0xffffffff)
        data=bytes(image.data);(out/'final.bgrx').write_bytes(data)
        row['frame']={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'depth':image.depth,'width':geo[2],'height':geo[3]}
        row['cleanup_release']=backend.release_all();row['server']['after_cleanup']=xstate(observer,wrapper.id)
        row['app_exit']=app.close();app=None
        if row['app_exit']!=0:raise RuntimeError('app exit')
        row['complete']=True
    except Exception as e:
        row['error']=repr(e); row['traceback']=traceback.format_exc(); raise
    finally:
        if backend:
            try:row['finally_release']=backend.release_all();backend.close()
            except Exception as e:row['cleanup_error']=repr(e)
        if app:
            try:row['app_exit']=app.close()
            except Exception as e:
                row['cleanup_error']=repr(e)
                if app.p.poll() is None:app.p.kill()
                row['emergency_exit']=app.p.wait(timeout=3);app.err.close()
        if observer:observer.close()
        write(out/'row.json',row)
    return row

def main():
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);p.add_argument('--batch',type=int,default=0);p.add_argument('--construction',action='store_true');a=p.parse_args()
    if a.batch not in range(3):raise ValueError('batch')
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    f=None if a.construction else freeze_check();jobs=cases(a.batch,a.construction)
    previous=None
    if not a.construction and a.batch:
        prev=out.parent/f'batch-{a.batch-1}'
        b=json.loads((prev/'BATCH.json').read_text());e=json.loads((prev/'EXTERNAL.json').read_text())
        if b['status']!='COMPLETE' or b['count']!=10 or e['returncode']!=0:raise RuntimeError('previous incomplete')
        previous={'batch_sha256':hashlib.sha256((prev/'BATCH.json').read_bytes()).hexdigest(),'external_sha256':hashlib.sha256((prev/'EXTERNAL.json').read_bytes()).hexdigest()}
    started=time.monotonic_ns();write(out/'START.json',{'pid':os.getpid(),'ns':started,'batch':a.batch,'construction':a.construction,'jobs':jobs,'freeze_sha256':f,'previous':previous})
    auth=out/'private.Xauthority';auth.touch(mode=0o600)
    number=next(i for i in range(3400,3900) if not Path(f'/tmp/.X11-unix/X{i}').exists() and not Path(f'/tmp/.X{i}-lock').exists())
    disp=f':{number}';subprocess.run(['xauth','-f',str(auth),'add',disp,'MIT-MAGIC-COOKIE-1',secrets.token_hex(16)],check=True,capture_output=True,timeout=3)
    env={k:os.environ[k] for k in ('PATH','LANG','LC_ALL') if k in os.environ}
    env.update(DISPLAY=disp,XAUTHORITY=str(auth),PYTHONUNBUFFERED='1',PYTHONDONTWRITEBYTECODE='1')
    os.environ['XAUTHORITY']=str(auth)
    rows=[];server=None;sid=None;status=None;error=None
    log=(out/'xvfb.log').open('xb')
    try:
        cmd=['Xvfb',disp,'-screen','0','640x360x24','-nolisten','tcp','-auth',str(auth),'-noreset']
        server=subprocess.Popen(cmd,stdout=log,stderr=log,start_new_session=True);sid=identity(server.pid)
        until=time.monotonic()+3
        while not Path(f'/tmp/.X11-unix/X{number}').exists():
            if time.monotonic()>until or server.poll() is not None:raise RuntimeError('server startup')
            time.sleep(.01)
        for i,(r,s) in enumerate(jobs): rows.append(one(out/f'case-{i:02d}',env,r,s,'3' if a.construction else '7'))
    except Exception as e:error=repr(e)
    finally:
        if server:
            server.terminate()
            try:status=server.wait(timeout=3)
            except subprocess.TimeoutExpired:server.kill();status=server.wait(timeout=3)
        log.close();auth.unlink(missing_ok=True)
        manifest={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob('case-*/*')) if p.is_file()}
        receipt={'status':'COMPLETE' if error is None else 'STOP','error':error,'count':len(rows),'batch':a.batch,'construction':a.construction,'started_ns':started,'ended_ns':time.monotonic_ns(),'server':sid,'server_command':cmd,'server_exit':status,'server_absent':not(server and Path(f'/proc/{server.pid}').exists()),'socket_absent':not Path(f'/tmp/.X11-unix/X{number}').exists(),'auth_absent':not auth.exists(),'freeze_sha256':f,'manifest':manifest}
        write(out/'BATCH.json',receipt)
    print(json.dumps({k:receipt[k] for k in ('status','count','error')}));return 0 if error is None else 2
if __name__=='__main__':sys.exit(main())
