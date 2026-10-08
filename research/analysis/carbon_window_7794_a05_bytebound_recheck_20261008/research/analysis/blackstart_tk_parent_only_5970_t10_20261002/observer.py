import json,select,sys
from Xlib import X,display
d=display.Display();root=d.create_resource_object('window',int(sys.argv[1],0));out=sys.argv[2];parent=root.query_tree().parent;pid=int(parent.id)
try:parent.change_attributes(event_mask=X.KeyPressMask|X.KeyReleaseMask);d.sync();selected=True;err=None
except Exception as e:
    try:d.sync()
    except Exception:pass
    selected=False;err={'type':type(e).__name__,'code':int(getattr(e,'code',-1)),'text':str(e)}
print(json.dumps({'ready':True,'tk_root_xid':int(root.id),'parent_xid':pid,'selected_xids':[pid] if selected else [],'selection_error':err},sort_keys=True),flush=True)
fd=d.fileno();fi=sys.stdin.fileno();seq=0
with open(out,'a',encoding='utf8',buffering=1) as f:
    while True:
        rr,_,_=select.select([fd,fi],[],[],.05)
        if fi in rr:
            line=sys.stdin.readline()
            if not line or line.strip()=='stop':break
        if fd in rr:
            while d.pending_events():
                e=d.next_event();seq+=1
                if e.type in (X.KeyPress,X.KeyRelease):f.write(json.dumps({'seq':seq,'type':int(e.type),'kind':'KeyPress' if e.type==X.KeyPress else 'KeyRelease','detail':int(e.detail),'time':int(e.time),'window_xid':int(e.window.id),'root_xid':int(e.root.id),'state':int(e.state)},sort_keys=True)+'\n')
d.close()
