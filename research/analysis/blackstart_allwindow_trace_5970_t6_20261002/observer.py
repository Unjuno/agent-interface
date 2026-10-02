import json,select,sys,time
from Xlib import X,display
d=display.Display(); root=d.create_resource_object('window',int(sys.argv[1],0)); out=sys.argv[2]
nodes=[]; failures=[]
def walk(w,parent=None,depth=0):
    a=w.get_attributes(); row={'xid':int(w.id),'parent_xid':parent,'depth':depth,'map_state':int(a.map_state)}; nodes.append(row)
    try: w.change_attributes(event_mask=X.KeyPressMask|X.KeyReleaseMask); d.sync(); row['selected']=True
    except Exception as e:
        try:d.sync()
        except Exception:pass
        row['selected']=False; row['error_type']=type(e).__name__; row['error_code']=int(getattr(e,'code',-1)); failures.append(row.copy())
    for c in w.query_tree().children: walk(c,int(w.id),depth+1)
walk(root)
print(json.dumps({'ready':True,'root_xid':int(root.id),'selected_xids':[n['xid'] for n in nodes if n.get('selected')],'nodes':nodes,'selection_failures':failures},sort_keys=True),flush=True)
fd=d.fileno(); fi=sys.stdin.fileno(); seq=0
with open(out,'a',encoding='utf8',buffering=1) as f:
    while True:
        rr,_,_=select.select([fd,fi],[],[],.05)
        if fi in rr:
            line=sys.stdin.readline()
            if not line or line.strip()=='stop':break
        if fd in rr:
            while d.pending_events():
                e=d.next_event(); seq+=1
                if e.type in (X.KeyPress,X.KeyRelease):
                    f.write(json.dumps({'seq':seq,'type':int(e.type),'kind':'KeyPress' if e.type==X.KeyPress else 'KeyRelease','detail':int(e.detail),'time':int(e.time),'window_xid':int(e.window.id),'root_xid':int(e.root.id),'state':int(e.state)},sort_keys=True)+'\n')
d.close()
