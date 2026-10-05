"""Excluded construction probe. Actual XTEST routing, not real-app task effect."""
import json,os,select,subprocess,sys,time
from pathlib import Path
from Xlib import X,display
from Xlib.ext import xtest
from policy import choose
def enrollment(pipe):
    deadline=time.monotonic()+5;data=bytearray()
    while time.monotonic()<deadline:
        if not select.select([pipe],[],[],max(0,deadline-time.monotonic()))[0]:break
        b=os.read(pipe.fileno(),1)
        if b==b'\n':return data.decode()
        if not b or len(data)>16:raise RuntimeError('invalid server enrollment')
        data.extend(b)
    raise TimeoutError('Xvfb enrollment')
def fixture(arm,mode,out):
    row=dict(arm=arm,mode=mode,construction_only=True);server=owner=sender=None;windows=[]
    with (out/f'{arm}-{mode}.stderr').open('xb') as err:
        try:
            server=subprocess.Popen(['Xvfb','-displayfd','1','-screen','0','100x80x24','-nolisten','tcp','-noreset'],stdout=subprocess.PIPE,stderr=err,bufsize=0)
            name=':'+enrollment(server.stdout);owner=display.Display(name);sender=display.Display(name)
            root=owner.screen().root
            for color in [0xdddddd,0x333333]:
                w=root.create_window(8,8,32,24,0,owner.screen().root_depth,X.InputOutput,X.CopyFromParent,background_pixel=color,override_redirect=True,event_mask=X.ButtonPressMask|X.ButtonReleaseMask);windows.append(w);w.map()
            target,cover=windows;owner.sync();row.update(target=target.id,cover=cover.id,display=name)
            def click():
                xtest.fake_input(sender,X.MotionNotify,x=24,y=20);sender.sync()
                while owner.pending_events():owner.next_event()
                try:xtest.fake_input(sender,X.ButtonPress,1);sender.sync()
                finally:xtest.fake_input(sender,X.ButtonRelease,1);sender.sync()
                owner.sync();events=[]
                while owner.pending_events():
                    e=owner.next_event()
                    if e.type in (X.ButtonPress,X.ButtonRelease):events.append(dict(type=e.type,window=e.window.id,detail=e.detail))
                return events
            row['prior_failure_events']=click()
            assert [e['window'] for e in row['prior_failure_events']]==[cover.id,cover.id],'prior failure not exposed'
            if mode in ('CLEAR','UNKNOWN'):cover.unmap()
            owner.sync();sender.sync()
            actual=sender.screen().root.query_pointer().child
            child=actual.id if actual else None
            row['native_pointer_child']=child;row['current_child']=None if mode=='UNKNOWN' else child
            row['decision']='TRY' if arm=='NO_MEMORY' else ('BLOCK' if arm=='TIMELESS_NOTE' else choose(row['current_child'],target.id,arm=='CONDITIONAL_MEMORY'))
            row['attempt_events']=click() if row['decision']=='TRY' else []
            row['target_presses']=sum(e['type']==X.ButtonPress and e['window']==target.id for e in row['attempt_events'])
            row['cover_presses']=sum(e['type']==X.ButtonPress and e['window']==cover.id for e in row['attempt_events'])
        except Exception as e:row['error']=repr(e)
        finally:
            if sender is not None:
                row['buttons_neutral']=not bool(sender.screen().root.query_pointer().mask&(X.Button1Mask|X.Button2Mask|X.Button3Mask));row['keymap_empty']=not any(sender.query_keymap());sender.close()
            if owner is not None:
                for w in windows:w.destroy()
                owner.sync();owner.close()
            if server is not None:server.terminate();row['server_exit']=server.wait(timeout=3)
    return row
def main():
    out=Path(sys.argv[1]);out.mkdir(exist_ok=False)
    with (out/'raw.jsonl').open('x') as f:
        for arm in ['NO_MEMORY','TIMELESS_NOTE','CONDITIONAL_MEMORY','FRESH_GUARD']:
            for mode in ['BLOCK','CLEAR','UNKNOWN']:
                row=fixture(arm,mode,out);f.write(json.dumps(row,sort_keys=True)+'\n');f.flush();os.fsync(f.fileno());print(json.dumps(row),flush=True)
                if 'error' in row:raise RuntimeError(row['error'])
    with (out/'ENV.json').open('x') as f:json.dump({'python':sys.version,'cgroups':{n:Path('/sys/fs/cgroup',n).read_text().strip() for n in ['cpu.max','memory.max','memory.swap.max','pids.max']}},f,indent=2)
if __name__=='__main__':main()
