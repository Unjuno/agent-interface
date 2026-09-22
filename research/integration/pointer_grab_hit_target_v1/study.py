#!/usr/bin/env python3
import json,select,subprocess,sys,time
from pathlib import Path
from Xlib import X,XK,display
from Xlib.ext import xtest

ARMS=('HIT_ONLY','HIT_GRAB_PROBE')
STATES=('CLEAR','GRAB_BEFORE_CHECK','GRAB_AFTER_CHECK')
SCHEDULE=[]
for rep in range(3):
    order=ARMS if rep%2==0 else ARMS[::-1]
    for st in STATES:
        for arm in order:SCHEDULE.append({'arm':arm,'state':st,'rep':rep})
SCHEDULE += [ {'arm':'NO_TASK_INPUT','state':'CLEAR','rep':0}, {'arm':'NO_TASK_INPUT','state':'GRAB_BEFORE_CHECK','rep':0} ]

def jprint(x): print(json.dumps(x,separators=(',',':')),flush=True)
def recv(p,t=3):
    if not select.select([p.stdout],[],[],t)[0]: raise TimeoutError('child response')
    line=p.stdout.readline()
    if not line: raise RuntimeError('child EOF')
    return json.loads(line)
def send(p,x): p.stdin.write(json.dumps(x,separators=(',',':'))+'\n');p.stdin.flush();return recv(p)

def app_mode():
    import tkinter as tk
    root=tk.Tk();root.geometry('360x180+80+60');root.title('pointer-grab-study')
    a=tk.Entry(root,name='a',width=18);b=tk.Entry(root,name='b',width=18)
    a.place(x=40,y=55,width=160,height=30);b.place(x=40,y=105,width=160,height=30)
    events=[]
    a.bind('<ButtonPress-1>',lambda e: events.append({'kind':'a_press','t_ns':time.monotonic_ns()}),add='+')
    root.update();b.focus_force();root.update()
    def snap():
        root.update();f=root.focus_get()
        return {'a':a.get(),'b':b.get(),'focus':str(f) if f else None,'a_xid':a.winfo_id(),
                'a_geo':[a.winfo_rootx(),a.winfo_rooty(),a.winfo_width(),a.winfo_height()],
                'events':list(events),'t_ns':time.monotonic_ns()}
    jprint({'kind':'ready','root_xid':root.winfo_id(),**snap()})
    for line in sys.stdin:
        q=json.loads(line);op=q['op']
        if op=='snapshot': r=snap()
        elif op=='close':
            r=snap();jprint({'id':q['id'],'ok':True,'snapshot':r});root.destroy();return
        else:r={'error':'bad op'}
        jprint({'id':q['id'],'ok':'error' not in r,'snapshot':r})

def grabber_mode(display_name):
    d=display.Display(display_name);root=d.screen().root
    w=root.create_window(420,70,120,80,1,d.screen().root_depth,X.InputOutput,X.CopyFromParent,
                         background_pixel=d.screen().white_pixel,event_mask=X.ButtonPressMask|X.ButtonReleaseMask)
    w.set_wm_name('grabber');w.map();d.sync();press=0;release=0;active=False
    jprint({'kind':'ready','xid':w.id})
    for line in sys.stdin:
        q=json.loads(line);op=q['op']
        if op=='grab':
            status=w.grab_pointer(False,X.ButtonPressMask|X.ButtonReleaseMask,X.GrabModeAsync,X.GrabModeAsync,X.NONE,X.NONE,X.CurrentTime)
            d.sync();active=(status==X.GrabSuccess);r={'status':int(status),'active':active}
        elif op=='drain':
            d.sync()
            while d.pending_events():
                e=d.next_event()
                if e.type==X.ButtonPress: press+=1
                elif e.type==X.ButtonRelease: release+=1
            r={'press':press,'release':release,'active':active}
        elif op=='ungrab':
            d.ungrab_pointer(X.CurrentTime);d.sync();active=False;r={'active':False}
        elif op=='close':
            if active:d.ungrab_pointer(X.CurrentTime);d.sync()
            w.destroy();d.sync();jprint({'id':q['id'],'ok':True,'result':{'press':press,'release':release}});d.close();return
        else:r={'error':'bad op'}
        jprint({'id':q['id'],'ok':'error' not in r,'result':r})

def leaf_at(d,x,y):
    w=d.screen().root;chain=[]
    while True:
        q=w.query_pointer();chain.append({'window':w.id,'child':getattr(q.child,'id',0) or 0})
        if not q.child or getattr(q.child,'id',0)==0:return w.id,chain
        w=q.child

def click(d):
    xtest.fake_input(d,X.ButtonPress,1);d.sync();xtest.fake_input(d,X.ButtonRelease,1);d.sync()
def type7(d):
    code=d.keysym_to_keycode(XK.string_to_keysym('7'))
    xtest.fake_input(d,X.KeyPress,code);d.sync();xtest.fake_input(d,X.KeyRelease,code);d.sync()
def keymap_neutral(d):
    return not any(d.query_keymap()) and not (d.screen().root.query_pointer().mask & (X.Button1Mask|X.Button2Mask|X.Button3Mask))

def run_case(display_name,cfg):
    app=subprocess.Popen([sys.executable,__file__,'app'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    g=subprocess.Popen([sys.executable,__file__,'grabber',display_name],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    ready=recv(app);gready=recv(g);d=display.Display(display_name)
    x,y,w,h=ready['a_geo'];cx=x+w//2;cy=y+h//2
    xtest.fake_input(d,X.MotionNotify,x=cx,y=cy);d.sync();time.sleep(.02)
    before_grab=send(g,{'id':1,'op':'grab'})['result'] if cfg['state']=='GRAB_BEFORE_CHECK' else None
    leaf,chain=leaf_at(d,cx,cy)
    probe=None;allow_click=True
    if cfg['arm']=='HIT_GRAB_PROBE':
        status=d.screen().root.grab_pointer(False,X.ButtonPressMask|X.ButtonReleaseMask,X.GrabModeAsync,X.GrabModeAsync,X.NONE,X.NONE,X.CurrentTime)
        d.sync();probe=int(status)
        if status==X.GrabSuccess:d.ungrab_pointer(X.CurrentTime);d.sync()
        allow_click=(leaf==ready['a_xid'] and status==X.GrabSuccess)
    elif cfg['arm']=='HIT_ONLY':allow_click=(leaf==ready['a_xid'])
    elif cfg['arm']=='NO_TASK_INPUT':allow_click=False
    after_grab=send(g,{'id':2,'op':'grab'})['result'] if cfg['state']=='GRAB_AFTER_CHECK' else None
    clicked=False;typed=False
    if allow_click:
        click(d);clicked=True;time.sleep(.02)
        s=send(app,{'id':1,'op':'snapshot'})['snapshot']
        if s['focus']=='.a':type7(d);typed=True;time.sleep(.02)
    final=send(app,{'id':2,'op':'snapshot'})['snapshot']
    gr=send(g,{'id':3,'op':'drain'})['result'];neutral=keymap_neutral(d)
    if gr['active']:send(g,{'id':4,'op':'ungrab'})
    gend=send(g,{'id':5,'op':'close'});aend=send(app,{'id':3,'op':'close'})
    d.close();app.wait(2);g.wait(2)
    return {'cfg':cfg,'ready':ready,'grabber_ready':gready,'before_grab':before_grab,'after_grab':after_grab,
            'leaf':leaf,'chain':chain,'probe':probe,'allow_click':allow_click,'clicked':clicked,'typed':typed,
            'final':final,'grabber':gr,'neutral':neutral,'app_exit':app.returncode,'grabber_exit':g.returncode,
            'app_stderr':app.stderr.read(),'grabber_stderr':g.stderr.read(),'app_close':aend,'grabber_close':gend}

def run_all(out,display_name):
    out=Path(out);out.mkdir()
    rows=[]
    for i,cfg in enumerate(SCHEDULE):
        row=run_case(display_name,{**cfg,'index':i});rows.append(row)
        (out/f'case-{i:02d}.json').write_text(json.dumps(row,indent=2,sort_keys=True)+'\n')
    (out/'rows.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')

def main():
    if sys.argv[1]=='app':return app_mode()
    if sys.argv[1]=='grabber':return grabber_mode(sys.argv[2])
    if sys.argv[1]=='run':return run_all(sys.argv[2],sys.argv[3])
if __name__=='__main__':main()
