#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, select, shutil, subprocess, sys, tempfile, time, uuid

HERE=pathlib.Path(__file__).resolve().parent
REPO=HERE.parents[2]
sys.path.insert(0,str(REPO))
sys.path.insert(0,str(REPO/'research'/'live_control'))
from Xlib import X, display
from native_handle_bridge_v1 import NativeHandleBridge

SOURCE_BLOBS={
 'research/live_control/native_handle_bridge_v1.py':'aa72a835a60ab9bf9f053c680a1a3d81e49c14d5',
 'research/live_control/scoped_target_handle_v3.py':'dd4f8c48c0617f4a6ad96565631efd54e0abaa62',
 'research/live_control/scoped_target_handle_v2.py':'736e1f073a7cf78cf473343f32d41c16bfb70e24',
 'research/live_control/scoped_target_handle_v1.py':'c4482bb7cd9c3a3e780c05bafa34073491a33ece',
 'research/live_control/coordinate_frame_transform_v1.py':'972daffee40a38d3effbd8155f3da133d664e445',
 'research/live_control/native_tail_v1.py':'29437a165d3f04a06a5ddd63744929bdb8ecb61e',
 'runtime/backends/x11_v1/backend.py':'9cae101a219348077668c8fc086acf8e13154afe',
 'runtime/backends/x11_v1/session.py':'e973b2f3f827951634344a320cd833a80a899d9e',
 'runtime/backends/x11_v1/capture_artifacts.py':'d20d67bc06d92d99859681f62fbeb9c2f13aab70',
 'runtime/core_v1/contract.py':'87154518107e4231a6f8ec06e976d2856b375d1d',
 'runtime/core_v1/sequence.py':'af7951e6b70193411b464e56c39c9c6dd7a4cd7e',
}

def blob(path):
    p=subprocess.run(['git','hash-object',str(REPO/path)],capture_output=True,text=True,check=True)
    return p.stdout.strip()

def verify_sources():
    got={p:blob(p) for p in SOURCE_BLOBS}
    bad={p:[SOURCE_BLOBS[p],got[p]] for p in got if got[p]!=SOURCE_BLOBS[p]}
    if bad: raise RuntimeError('SOURCE_BLOB_MISMATCH '+json.dumps(bad,sort_keys=True))
    return got

def readj(proc, timeout=5):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        ready,_,_=select.select([proc.stdout],[],[],0.1)
        if not ready: continue
        line=proc.stdout.readline()
        if not line: raise RuntimeError('actor EOF')
        line=line.strip()
        if line.startswith('{'):
            return json.loads(line)
    raise TimeoutError('actor response')

def send(proc,obj):
    proc.stdin.write(json.dumps(obj)+'\n'); proc.stdin.flush(); return readj(proc)

def wait_socket(n, timeout=5):
    p=pathlib.Path(f'/tmp/.X11-unix/X{n}'); end=time.monotonic()+timeout
    while time.monotonic()<end:
        if p.exists(): return p
        time.sleep(.05)
    raise TimeoutError(p)

def drain_observer(d, bound_xid, timeout=3):
    end=time.monotonic()+timeout; rows=[]
    while time.monotonic()<end:
        d.sync()
        while d.pending_events():
            e=d.next_event(); wid=int(getattr(getattr(e,'window',None),'id',0) or 0)
            row={'type':int(e.type),'window':wid,'send_event':bool(getattr(e,'send_event',False))}
            rows.append(row)
            if e.type==X.DestroyNotify and wid==bound_xid:
                return row,rows
        time.sleep(.01)
    return None,rows

def activate_managed(env, xid, bridge, timeout=4.0):
    end=time.monotonic()+timeout
    attempts=[]
    while time.monotonic()<end:
        p=subprocess.run(['wmctrl','-ia',hex(int(xid))],env=env,text=True,capture_output=True,check=False)
        attempts.append({'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
        time.sleep(0.04)
        if bridge._focus_within_target(int(xid)):
            return {'status':'FOCUSED_WITHIN_TARGET','attempts':attempts}
    raise RuntimeError('WM_ACTIVATION_FAILED '+json.dumps(attempts[-5:],sort_keys=True))

def one_session(index,out):
    display_n=230+index
    disp=f':{display_n}'
    auth=out/'Xauthority'; auth.write_bytes(b'')
    env=dict(os.environ,DISPLAY=disp,XAUTHORITY=str(auth),PYTHONUNBUFFERED='1')
    xvfb=subprocess.Popen(['Xvfb',disp,'-screen','0','800x600x24','-nolisten','tcp','-ac','-noreset'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
    socket=wait_socket(display_n)
    openbox=subprocess.Popen(['openbox','--sm-disable'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
    actor=subprocess.Popen([sys.executable,'-B',str(HERE/'actor.py')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
    bridge=None; observer=None
    row={'session':index,'display':disp,'formal_alias_attempts':0,'fresh_attempts':0,'source_blobs':verify_sources()}
    try:
        row['actor_ready']=readj(actor)
        c1=send(actor,{'op':'create'}); row['create_w1']=c1
        if not c1.get('ok'): raise RuntimeError('ACTOR_CREATE_W1_FAILED '+json.dumps(c1,sort_keys=True))
        xid=c1['xid']; row['w1']=c1
        # Independent observer: root diagnostics and exact bound-client structure events.
        observer=display.Display(disp)
        root=observer.screen().root
        root.change_attributes(event_mask=X.SubstructureNotifyMask)
        bound=observer.create_resource_object('window',xid)
        attrs=bound.get_attributes(); bound.change_attributes(event_mask=int(attrs.your_event_mask)|X.StructureNotifyMask)
        observer.sync()
        # Exact current bridge.
        bridge=NativeHandleBridge(disp,{'fixture':xid},'fixture',out/'bridge')
        row['activate_w1']=activate_managed(env,xid,bridge)
        s1=send(actor,{'op':'snapshot'}); row['snapshot_w1']=s1
        if not s1.get('ok'): raise RuntimeError('ACTOR_SNAPSHOT_W1_FAILED '+json.dumps(s1,sort_keys=True))
        c1['snapshot']=s1['snapshot']
        obs=bridge.observe(); geo=bridge.backend.geometry('fixture')
        point=[geo['x']+120,geo['y']+80]
        offset=bridge.mint('old',obs['sequence'],point,region_size=(24,38))
        row['initial']={'observation':obs,'geometry':geo,'point':point,'offset':offset,
                        'scope':bridge.scope,'binding_revision':bridge.binding_revision,
                        'emissions':bridge.backend.emissions}
        row['effect_initial']=send(actor,{'op':'effects'})
        # Destroy exact bound window and wait exact client DestroyNotify.
        row['destroy_cmd']=send(actor,{'op':'destroy'})
        destroy_event,events=drain_observer(observer,xid)
        row['observer_events']=events; row['destroy_event']=destroy_event
        if destroy_event is None: raise RuntimeError('BOUND_DESTROY_NOT_OBSERVED')
        # Composition adapter: authority-free invalidation only.
        bridge.review_required=True
        row['invalidation']={'review_required':bridge.review_required,'binding_revision':bridge.binding_revision,
                             'scope':bridge.scope,'emissions':bridge.backend.emissions}
        before=bridge.backend.emissions; e0=send(actor,{'op':'effects'})
        stale_pre=bridge.click('old',offset); row['formal_alias_attempts']+=1
        e1=send(actor,{'op':'effects'})
        row['stale_pre_review']={'result':stale_pre,'emissions_before':before,'emissions_after':bridge.backend.emissions,
                                 'effect_before':e0,'effect_after':e1}
        # Replacement from the SAME actor, deliberately reusing freed client XID.
        c2=send(actor,{'op':'create_reuse'}); row['create_w2']=c2; row['w2']=c2
        if not c2.get('ok'): raise RuntimeError('ACTOR_CREATE_W2_FAILED '+json.dumps(c2,sort_keys=True))
        if c2['xid']!=xid: raise RuntimeError('SAME_XID_REUSE_MISSING')
        row['activate_w2']=activate_managed(env,xid,bridge)
        s2=send(actor,{'op':'snapshot'}); row['snapshot_w2']=s2
        if not s2.get('ok'): raise RuntimeError('ACTOR_SNAPSHOT_W2_FAILED '+json.dumps(s2,sort_keys=True))
        c2['snapshot']=s2['snapshot']
        # Existing exact review machinery owns scope/revision transition.
        prev_scope=bridge.scope; prev_rev=bridge.binding_revision
        review=bridge.review_window(xid)
        row['review']={'receipt':review,'previous_scope':prev_scope,'previous_revision':prev_rev,
                       'scope':bridge.scope,'binding_revision':bridge.binding_revision}
        # Old alias after successful review must remain revoked.
        b2=bridge.backend.emissions; p0=send(actor,{'op':'effects'})
        stale_post=bridge.click('old',offset); row['formal_alias_attempts']+=1
        p1=send(actor,{'op':'effects'})
        row['stale_post_review']={'result':stale_post,'emissions_before':b2,'emissions_after':bridge.backend.emissions,
                                 'effect_before':p0,'effect_after':p1}
        # Fresh alias from exact reviewed observation.
        if review.get('status')!='reviewed': raise RuntimeError('REVIEW_FAILED')
        robs=review['observation']; rgeo=bridge.backend.geometry('fixture')
        rpoint=[rgeo['x']+120,rgeo['y']+80]
        fresh_offset=bridge.mint('fresh',robs['sequence'],rpoint,region_size=(24,38))
        fb=bridge.backend.emissions; f0=send(actor,{'op':'effects'})
        fresh=bridge.click('fresh',fresh_offset); row['fresh_attempts']+=1
        f1=send(actor,{'op':'effects'})
        row['fresh']={'result':fresh,'emissions_before':fb,'emissions_after':bridge.backend.emissions,
                      'effect_before':f0,'effect_after':f1,'offset':fresh_offset,'point':rpoint}
        row['terminal_release']=bridge.backend.release_all()
        row['status']='COMPLETE'
        return row
    except Exception as e:
        row['status']='STOP'; row['error']=repr(e); return row
    finally:
        if bridge is not None:
            try: bridge.close(); row['bridge_closed']=True
            except Exception as e: row['bridge_close_error']=repr(e)
        if observer is not None:
            try: observer.close()
            except Exception: pass
        if actor.poll() is None:
            try: row['actor_close']=send(actor,{'op':'close'})
            except Exception as e: row['actor_close_error']=repr(e)
        try: actor.wait(timeout=3)
        except Exception: actor.kill(); actor.wait()
        row['actor_exit']=actor.returncode
        try: openbox.terminate(); openbox.wait(timeout=3)
        except Exception:
            try: openbox.kill(); openbox.wait()
            except Exception: pass
        row['openbox_exit']=openbox.returncode
        try: xvfb.terminate(); xvfb.wait(timeout=3)
        except Exception:
            try: xvfb.kill(); xvfb.wait()
            except Exception: pass
        row['xvfb_exit']=xvfb.returncode
        row['socket_absent']=not socket.exists()
        try: row['actor_stderr']=actor.stderr.read()
        except Exception: pass
        try: row['openbox_stderr']=openbox.stderr.read()
        except Exception: pass
        try: row['xvfb_stderr']=xvfb.stderr.read()
        except Exception: pass

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',required=True); ap.add_argument('--sessions',type=int,default=1); ap.add_argument('--mode',choices=['construction','formal'],required=True)
    a=ap.parse_args(); out=pathlib.Path(a.out); out.mkdir(parents=True,exist_ok=False)
    data={'mode':a.mode,'main_sha':'7e5ad7c0b50027fcec5414821b0685868c5212d2','sessions':[],'started_ns':time.monotonic_ns()}
    for i in range(a.sessions):
        sdir=out/f'session-{i:02d}'; sdir.mkdir(); row=one_session(i,sdir); data['sessions'].append(row)
        (sdir/'ROW.json').write_text(json.dumps(row,indent=2,sort_keys=True)+'\n')
        if row.get('status')!='COMPLETE' and a.mode=='formal': break
    data['ended_ns']=time.monotonic_ns(); data['complete']=len(data['sessions'])==a.sessions and all(r.get('status')=='COMPLETE' for r in data['sessions'])
    (out/'RAW.json').write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'mode':a.mode,'sessions':len(data['sessions']),'complete':data['complete'],'statuses':[r.get('status') for r in data['sessions']]},sort_keys=True))
    raise SystemExit(0 if data['complete'] else 2)
if __name__=='__main__': main()
