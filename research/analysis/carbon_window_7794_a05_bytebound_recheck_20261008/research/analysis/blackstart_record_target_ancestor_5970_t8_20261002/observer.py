import json,select,sys
from Xlib import X,display
d=display.Display();root=d.create_resource_object('window',int(sys.argv[1],0));out=sys.argv[2]
nodes={};order=[]
def add(w,parent,depth,kind):
    xid=int(w.id)
    if xid in nodes:return
    n={'xid':xid,'parent_xid':parent,'depth':depth,'kind':kind};nodes[xid]=n;order.append(xid)
    try:w.change_attributes(event_mask=X.KeyPressMask|X.KeyReleaseMask);d.sync();n['selected']=True
    except Exception as e:
        try:d.sync()
        except Exception:pass
        n['selected']=False;n['error_type']=type(e).__name__;n['error_code']=int(getattr(e,'code',-1))
def down(w,parent=None,depth=0):
    add(w,parent,depth,'subtree')
    for c in w.query_tree().children:down(c,int(w.id),depth+1)
anc=[];cur=root;seen={int(root.id)}
while True:
    p=cur.query_tree().parent;pid=int(p.id)
    if pid in seen:break
    seen.add(pid);anc.append(p);cur=p
for i,w in enumerate(anc,1):add(w,int(anc[i-2].id) if i>1 else int(root.id),-i,'ancestor')
for w in anc:down(w,None,-1)
down(root,None,0)
selected=[x for x in order if nodes[x]['selected']]
print(json.dumps({'ready':True,'tk_root_xid':int(root.id),'selected_xids':selected,'windows':[nodes[x] for x in order]},sort_keys=True),flush=True)
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
