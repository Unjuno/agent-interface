#!/usr/bin/env python3
import json, select, subprocess, sys, time
from pathlib import Path
from Xlib import X, XK, display
from Xlib.ext import xtest

ARMS=('FOCUS_ONLY','FOCUS_KEYBOARD_PROBE')
STATES=('CLEAR','GRAB_BEFORE_PROBE','GRAB_AFTER_PROBE')
SCHEDULE=[]
for rep in range(3):
    order=ARMS if rep%2==0 else ARMS[::-1]
    for state in STATES:
        for arm in order:
            SCHEDULE.append({'arm':arm,'state':state,'rep':rep})
SCHEDULE += [
    {'arm':'NO_TASK_INPUT','state':'CLEAR','rep':0},
    {'arm':'NO_TASK_INPUT','state':'GRAB_BEFORE_PROBE','rep':0},
]

def jprint(obj):
    print(json.dumps(obj,separators=(',',':')),flush=True)

def recv(proc, timeout=3):
    if not select.select([proc.stdout],[],[],timeout)[0]:
        raise TimeoutError('child response')
    line=proc.stdout.readline()
    if not line:
        raise RuntimeError('child EOF')
    return json.loads(line)

def send(proc,obj):
    proc.stdin.write(json.dumps(obj,separators=(',',':'))+'\n'); proc.stdin.flush()
    return recv(proc)

def app_mode():
    import tkinter as tk
    root=tk.Tk(); root.geometry('360x180+80+60'); root.title('keyboard-grab-focus-study')
    a=tk.Entry(root,name='a',width=18); b=tk.Entry(root,name='b',width=18)
    a.place(x=40,y=55,width=160,height=30); b.place(x=40,y=105,width=160,height=30)
    keys=[]
    for widget,name in ((a,'a'),(b,'b')):
        widget.bind('<KeyPress>',lambda e,n=name: keys.append({'kind':'press','target':n,'keysym':e.keysym,'t_ns':time.monotonic_ns()}),add='+')
        widget.bind('<KeyRelease>',lambda e,n=name: keys.append({'kind':'release','target':n,'keysym':e.keysym,'t_ns':time.monotonic_ns()}),add='+')
    root.update(); b.focus_force(); root.update()
    def snap():
        root.update(); f=root.focus_get()
        return {'a':a.get(),'b':b.get(),'focus':str(f) if f else None,'a_xid':a.winfo_id(),
                'a_geo':[a.winfo_rootx(),a.winfo_rooty(),a.winfo_width(),a.winfo_height()],
                'keys':list(keys),'t_ns':time.monotonic_ns()}
    jprint({'kind':'ready','root_xid':root.winfo_id(),**snap()})
    for line in sys.stdin:
        q=json.loads(line); op=q['op']
        if op=='snapshot': result=snap()
        elif op=='close':
            result=snap(); jprint({'id':q['id'],'ok':True,'snapshot':result}); root.destroy(); return
        else: result={'error':'bad op'}
        jprint({'id':q['id'],'ok':'error' not in result,'snapshot':result})

def grabber_mode(display_name):
    d=display.Display(display_name); root=d.screen().root
    w=root.create_window(420,70,140,90,1,d.screen().root_depth,X.InputOutput,X.CopyFromParent,
        background_pixel=d.screen().white_pixel,event_mask=X.KeyPressMask|X.KeyReleaseMask)
    w.set_wm_name('keyboard-grabber'); w.map(); d.sync()
    press=release=0; events=[]; active=False
    jprint({'kind':'ready','xid':w.id})
    for line in sys.stdin:
        q=json.loads(line); op=q['op']
        if op=='grab':
            status=w.grab_keyboard(False,X.GrabModeAsync,X.GrabModeAsync,X.CurrentTime)
            d.sync(); active=(status==X.GrabSuccess); result={'status':int(status),'active':active}
        elif op=='drain':
            d.sync()
            while d.pending_events():
                e=d.next_event()
                if e.type==X.KeyPress:
                    press+=1; events.append({'kind':'press','detail':int(e.detail)})
                elif e.type==X.KeyRelease:
                    release+=1; events.append({'kind':'release','detail':int(e.detail)})
            result={'press':press,'release':release,'events':list(events),'active':active}
        elif op=='ungrab':
            d.ungrab_keyboard(X.CurrentTime); d.sync(); active=False; result={'active':False}
        elif op=='close':
            if active:
                d.ungrab_keyboard(X.CurrentTime); d.sync(); active=False
            w.destroy(); d.sync(); jprint({'id':q['id'],'ok':True,'result':{'press':press,'release':release,'events':events}}); d.close(); return
        else: result={'error':'bad op'}
        jprint({'id':q['id'],'ok':'error' not in result,'result':result})

def click_a(d,geo):
    x,y,w,h=geo; cx=x+w//2; cy=y+h//2
    xtest.fake_input(d,X.MotionNotify,x=cx,y=cy); d.sync()
    xtest.fake_input(d,X.ButtonPress,1); d.sync(); xtest.fake_input(d,X.ButtonRelease,1); d.sync()

def type7(d):
    code=d.keysym_to_keycode(XK.string_to_keysym('7'))
    xtest.fake_input(d,X.KeyPress,code); d.sync(); xtest.fake_input(d,X.KeyRelease,code); d.sync()
    return code

def server_neutral(d):
    keymap=d.query_keymap(); mask=d.screen().root.query_pointer().mask
    return (not any(keymap)) and not (mask & (X.Button1Mask|X.Button2Mask|X.Button3Mask))

def run_case(display_name,cfg):
    app=subprocess.Popen([sys.executable,__file__,'app'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    grab=subprocess.Popen([sys.executable,__file__,'grabber',display_name],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    ready=recv(app); gready=recv(grab); d=display.Display(display_name)
    click_a(d,ready['a_geo']); time.sleep(.02)
    pre=send(app,{'id':1,'op':'snapshot'})['snapshot']
    if pre['focus']!='.a': raise RuntimeError('focus A not established')
    before_grab=send(grab,{'id':1,'op':'grab'})['result'] if cfg['state']=='GRAB_BEFORE_PROBE' else None
    probe=None; allow_key=(cfg['arm']!='NO_TASK_INPUT')
    if cfg['arm']=='FOCUS_KEYBOARD_PROBE':
        status=d.screen().root.grab_keyboard(False,X.GrabModeAsync,X.GrabModeAsync,X.CurrentTime)
        d.sync(); probe=int(status)
        if status==X.GrabSuccess:
            d.ungrab_keyboard(X.CurrentTime); d.sync()
        allow_key=(status==X.GrabSuccess)
    elif cfg['arm']=='NO_TASK_INPUT':
        allow_key=False
    after_grab=send(grab,{'id':2,'op':'grab'})['result'] if cfg['state']=='GRAB_AFTER_PROBE' else None
    sent=False; keycode=None
    if allow_key:
        keycode=type7(d); sent=True; time.sleep(.02)
    final=send(app,{'id':2,'op':'snapshot'})['snapshot']
    gr=send(grab,{'id':3,'op':'drain'})['result']
    neutral=server_neutral(d)
    if gr['active']: send(grab,{'id':4,'op':'ungrab'})
    gend=send(grab,{'id':5,'op':'close'}); aend=send(app,{'id':3,'op':'close'})
    d.close(); app.wait(2); grab.wait(2)
    return {'cfg':cfg,'ready':ready,'grabber_ready':gready,'pre':pre,'before_grab':before_grab,'after_grab':after_grab,
        'probe':probe,'allow_key':allow_key,'sent':sent,'keycode':keycode,'final':final,'grabber':gr,'neutral':neutral,
        'app_exit':app.returncode,'grabber_exit':grab.returncode,'app_stderr':app.stderr.read(),'grabber_stderr':grab.stderr.read(),
        'app_close':aend,'grabber_close':gend}

def run_all(out,display_name,schedule=None):
    out=Path(out); out.mkdir()
    rows=[]
    for i,base in enumerate(schedule or SCHEDULE):
        cfg={**base,'index':i}; row=run_case(display_name,cfg); rows.append(row)
        (out/f'case-{i:02d}.json').write_text(json.dumps(row,indent=2,sort_keys=True)+'\n')
    (out/'rows.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
    return rows

def main():
    if len(sys.argv)>=2 and sys.argv[1]=='app': return app_mode()
    if len(sys.argv)>=3 and sys.argv[1]=='grabber': return grabber_mode(sys.argv[2])
    if len(sys.argv)>=4 and sys.argv[1]=='run': return run_all(sys.argv[2],sys.argv[3])
    raise SystemExit('usage')
if __name__=='__main__': main()
