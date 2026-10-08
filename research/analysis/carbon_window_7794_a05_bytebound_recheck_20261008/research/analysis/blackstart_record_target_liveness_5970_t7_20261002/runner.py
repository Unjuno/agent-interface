from __future__ import annotations
import json,subprocess,sys,time
from pathlib import Path
from Xlib import X,display

def wait(fn,timeout=5):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        v=fn()
        if v:return v
        time.sleep(.01)
    raise TimeoutError('bounded fixture wait expired')
def main():
    out=Path(sys.argv[1]);appsrc=Path(sys.argv[2]);target=int(sys.argv[3]);out.mkdir(parents=True,exist_ok=True);tk=out/'tk';app=None;d=None
    raw={'schema':'blackstart-record-target-liveness-t7-raw-v1','input_dispatched':False,'target_xid':target,'error':None}
    try:
        app=subprocess.Popen([sys.executable,str(appsrc),str(tk),str(out/'actions.json')],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
        sf=tk/'state.json';wait(lambda:json.loads(sf.read_text()) if sf.exists() else None);state=wait(lambda:(s if (s:=(json.loads(sf.read_text()) if sf.exists() else {})).get('focus_widget') else None))
        d=display.Display();root=d.create_resource_object('window',int(state['root_xid']));tree=[]
        def scan(w,parent=None,depth=0):
            a=w.get_attributes();tree.append({'xid':int(w.id),'parent_xid':parent,'depth':depth,'map_state':int(a.map_state),'all_event_masks':int(a.all_event_masks),'observer_event_mask':int(a.your_event_mask)})
            for c in w.query_tree().children:scan(c,int(w.id),depth+1)
        scan(root)
        raw.update({'state':state,'tree':tree,'target_in_tree':any(n['xid']==target for n in tree)})
        tw=d.create_resource_object('window',target)
        try:
            a=tw.get_attributes();q=tw.query_tree();tw.change_attributes(event_mask=X.KeyPressMask|X.KeyReleaseMask);d.sync()
            raw['target_query']={'result':'success','map_state':int(a.map_state),'all_event_masks':int(a.all_event_masks),'observer_event_mask_before':int(a.your_event_mask),'parent_xid':int(q.parent.id),'children_xids':[int(c.id) for c in q.children],'selection':'success'}
        except Exception as e:
            try:d.sync()
            except Exception:pass
            raw['target_query']={'result':'error','error_type':type(e).__name__,'error_code':int(getattr(e,'code',-1)),'error_text':str(e)}
    except Exception as e:raw['error']={'type':type(e).__name__,'message':str(e)}
    finally:
        if d is not None:d.close()
        if app is not None and app.poll() is None:
            app.terminate()
            try:app.wait(timeout=2)
            except subprocess.TimeoutExpired:app.kill();app.wait(timeout=2)
        raw['app_returncode']=app.returncode if app else None
        (out/'candidate.raw.json').write_text(json.dumps(raw,indent=2,sort_keys=True)+'\n')
    return 0 if raw['error'] is None else 2
if __name__=='__main__':raise SystemExit(main())
