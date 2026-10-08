from __future__ import annotations
import json,subprocess,sys,time
from pathlib import Path
from Xlib import X,display

def wait(fn,timeout=5):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        x=fn()
        if x:return x
        time.sleep(.01)
    raise TimeoutError('bounded no-input fixture wait expired')

def main():
    out=Path(sys.argv[1]); app_src=Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
    tk=out/'tk'; app=None; observer=None; raw={'schema':'blackstart-xevent-target-t5-raw-v1','input_dispatched':False,'error':None}
    try:
        app=subprocess.Popen([sys.executable,str(app_src),str(tk),str(out/'actions.json')],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
        state_path=tk/'state.json'
        wait(lambda: json.loads(state_path.read_text()) if state_path.exists() else None)
        state=wait(lambda:(s if (s:=(json.loads(state_path.read_text()) if state_path.exists() else {})).get('focus_widget') else None))
        observer=display.Display(); xid_map={}; nodes=[]
        def scan(xid,parent=None,depth=0):
            w=observer.create_resource_object('window',xid)
            attrs=w.get_attributes()
            item={'xid':int(xid),'parent_xid':parent,'depth':depth,'map_state':int(attrs.map_state),'all_event_masks':int(attrs.all_event_masks),'observer_event_mask_before':int(attrs.your_event_mask)}
            nodes.append(item); xid_map[int(xid)]=w
            for child in w.query_tree().children: scan(int(child.id),int(xid),depth+1)
        scan(int(state['root_xid']))
        entry=int(state['entry_xid']); candidates=[n for n in nodes if n['xid']!=entry and n['all_event_masks']&X.KeyPressMask]
        selected_target=candidates[-1] if candidates else None
        raw.update({'state':state,'window_tree':nodes,'entry_xid':entry,'app_selected_keypress_candidates':candidates,'selection_tests':[]})
        def attempt(target,label):
            w=xid_map[target]
            try:
                w.change_attributes(event_mask=X.KeyPressMask); observer.sync()
                result={'target_xid':target,'label':label,'result':'success','error_code':None}
            except Exception as exc:
                observer.sync(); result={'target_xid':target,'label':label,'result':'error','error_type':type(exc).__name__,'error_code':int(getattr(exc,'code',-1)),'error_text':str(exc)}
            raw['selection_tests'].append(result)
        attempt(entry,'entry')
        if selected_target is not None: attempt(selected_target['xid'],'app-selected-target')
        else: raw['selection_target_missing']=True
    except Exception as exc:
        raw['error']={'type':type(exc).__name__,'message':str(exc)}
    finally:
        if observer is not None: observer.close()
        if app is not None and app.poll() is None:
            app.terminate()
            try: app.wait(timeout=2)
            except subprocess.TimeoutExpired: app.kill(); app.wait(timeout=2)
        raw['app_returncode']=app.returncode if app else None
        (out/'candidate.raw.json').write_text(json.dumps(raw,indent=2,sort_keys=True)+'\n')
    return 0 if raw['error'] is None else 2
if __name__=='__main__': raise SystemExit(main())
