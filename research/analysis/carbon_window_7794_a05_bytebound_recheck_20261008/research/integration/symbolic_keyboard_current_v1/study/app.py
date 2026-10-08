import argparse,json,os,signal,sys,tkinter as tk,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--mode',choices=['EDITOR','MODAL'],required=True);a=p.parse_args()
state_path=Path(a.state)
state={'mode':a.mode,'undo':0,'redo':0,'confirm':0,'stray_return':0,'events':[],'ready':False}
def save():
    tmp=state_path.with_suffix('.tmp');tmp.write_text(json.dumps(state,sort_keys=True));os.replace(tmp,state_path)
root=tk.Tk();root.title('symbolic-keyboard-fixture');root.geometry('420x160+10+10')
e=tk.Entry(root,width=32);e.pack(padx=20,pady=30);e.insert(0,'seed');e.focus_force()
def log(kind,event):
    state['events'].append({'kind':kind,'keysym':event.keysym,'state':int(event.state),'ns':time.monotonic_ns()})
def undo(event):
    log('UNDO',event);state['undo']+=1;save();return 'break'
def redo(event):
    log('REDO',event);state['redo']+=1;save();return 'break'
e.bind('<Control-y>',redo)
def ret(event):
    if state['mode']=='MODAL': log('CONFIRM',event);state['confirm']+=1
    else: log('STRAY_RETURN',event);state['stray_return']+=1
    save();return 'break'
e.bind('<Control-z>',undo);e.bind('<Return>',ret)
def toggle(sig,frame):
    state['mode']='EDITOR' if state['mode']=='MODAL' else 'MODAL';save()
def stop(sig,frame): root.after(0,root.destroy)
signal.signal(signal.SIGUSR1,toggle);signal.signal(signal.SIGTERM,stop)
root.update_idletasks();root.update();e.focus_force();root.update()
state['ready']=True;state['window_id']=int(e.winfo_id());save();print(json.dumps({'ready':True,'window_id':state['window_id'],'pid':os.getpid()}),flush=True)
root.mainloop();state['ready']=False;save()
