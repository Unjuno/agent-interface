"""Private X11 input plus authored tiny-app file effect. Not a stock app study."""
if not __debug__:raise RuntimeError('STOP_OPTIMIZED_PROBE')
import hashlib,json,os,select,subprocess,sys,time
from pathlib import Path
from Xlib import X,XK,display
from Xlib.ext import xtest
from policy import FIELDS,learn,decide
ARMS=('NO_MEMORY','NOTE','TYPED','FRESH','TYPED_PLUS_FRESH')
MODES=('RECUR','CLEAR','WITHHELD','NEW_FAILURE')

def enrollment(pipe):
    end=time.monotonic()+5;data=bytearray()
    while time.monotonic()<end:
        if not select.select([pipe],[],[],max(0,end-time.monotonic()))[0]:break
        b=os.read(pipe.fileno(),1)
        if b==b'\n':return data.decode('ascii')
        if not b or len(data)>16:raise RuntimeError('invalid enrollment')
        data.extend(b)
    raise TimeoutError('Xvfb enrollment')

def fixture(field,mode,arm,out):
    cell=out/f'{field}-{mode}-{arm}';cell.mkdir(exist_ok=False)
    row={'field':field,'mode':mode,'arm':arm,'construction_only':True}
    server=owner=sender=None;windows=[];cleanup=[]
    with (cell/'server.stderr').open('xb') as err:
        try:
            server=subprocess.Popen(['Xvfb','-displayfd','1','-screen','0','100x80x24','-nolisten','tcp','-noreset'],stdout=subprocess.PIPE,stderr=err,bufsize=0)
            name=':'+enrollment(server.stdout);owner=display.Display(name);sender=display.Display(name)
            root=owner.screen().root
            for color in (0xdddddd,0x333333):
                w=root.create_window(8,8,32,24,0,owner.screen().root_depth,X.InputOutput,X.CopyFromParent,
                                     background_pixel=color,override_redirect=True,event_mask=X.ButtonPressMask|X.ButtonReleaseMask|X.KeyPressMask|X.KeyReleaseMask)
                windows.append(w)
            target,cover=windows;target.map();owner.sync()
            atoms={k:owner.intern_atom('AI_TEST_'+k.upper()) for k in ('pending','business')}
            keycode=sender.keysym_to_keycode(XK.string_to_keysym('F8'))
            if not keycode:raise RuntimeError('F8 absent')
            row.update(display=name,target=target.id,cover=cover.id,keycode=keycode)
            def configure(bad):
                target.configure(x=60 if bad=='geometry' else 8,y=8)
                if bad=='cover':cover.map();cover.configure(stack_mode=X.Above)
                else:cover.unmap()
                # Focus failure uses a separate mapped window away from the pointer.
                if bad=='focus':cover.configure(x=60,y=40);cover.map()
                else:cover.configure(x=8,y=8)
                (cover if bad=='focus' else target).set_input_focus(X.RevertToParent,X.CurrentTime)
                for k,atom in atoms.items():target.change_property(atom,Xatom_STRING,8,b'BAD' if bad==k else b'OK')
                owner.sync();sender.sync()
                xtest.fake_input(sender,X.MotionNotify,x=24,y=20);sender.sync()
                while owner.pending_events():owner.next_event()
            def observe():
                child=sender.screen().root.query_pointer().child
                focus=sender.get_input_focus().focus
                geom=target.get_geometry()
                obs={'cover':(child.id if child else None)!=cover.id,
                     'geometry':geom.x==8 and geom.y==8 and geom.width==32 and geom.height==24,
                     'focus':getattr(focus,'id',focus)==target.id}
                for k,atom in atoms.items():obs[k]=bytes(target.get_full_property(atom,Xatom_STRING).value)==b'OK'
                return obs
            def action(phase):
                events=[];button_held=False
                try:
                    button_held=True;xtest.fake_input(sender,X.ButtonPress,1);sender.sync()
                    xtest.fake_input(sender,X.ButtonRelease,1);sender.sync();button_held=False
                    xtest.fake_input(sender,X.KeyPress,keycode);sender.sync()
                finally:
                    xtest.fake_input(sender,X.KeyRelease,keycode);sender.sync()
                    if button_held:xtest.fake_input(sender,X.ButtonRelease,1);sender.sync()
                owner.sync()
                while owner.pending_events():
                    e=owner.next_event()
                    if e.type in (X.ButtonPress,X.ButtonRelease,X.KeyPress,X.KeyRelease):
                        events.append(dict(type=e.type,window=e.window.id,detail=e.detail))
                # Application effect requires target click, then target F8, plus app readiness/business state.
                target_presses=[e['type'] for e in events if e['window']==target.id and e['type'] in (X.ButtonPress,X.KeyPress)]
                ready=all(bytes(target.get_full_property(a,Xatom_STRING).value)==b'OK' for a in atoms.values())
                committed=target_presses==[X.ButtonPress,X.KeyPress] and ready
                if committed:
                    with (cell/f'{phase}.saved').open('xb') as f:f.write(b'COMMITTED\n');f.flush();os.fsync(f.fileno())
                    target.change_property(owner.intern_atom('AI_TEST_EFFECT'),Xatom_STRING,8,b'COMMITTED');owner.sync()
                return {'events':events,'committed':committed,'saved_bytes':(cell/f'{phase}.saved').read_bytes().hex() if committed else None}
            configure(field);prior_obs=observe();row['prior_observed']=prior_obs
            row['prior']=action('prior')
            if row['prior']['committed'] or prior_obs[field] is not False:raise RuntimeError('initial failure not exposed')
            memory=cell/'memory.json'
            evidence=hashlib.sha256(json.dumps(row['prior'],sort_keys=True).encode()).hexdigest()
            learn(memory,str(target.id),'click_then_F8',prior_obs,field,evidence)
            row['memory']=json.loads(memory.read_text());row['memory_sha256']=hashlib.sha256(memory.read_bytes()).hexdigest()
            current_bad=field if mode=='RECUR' else (FIELDS[(FIELDS.index(field)+1)%len(FIELDS)] if mode=='NEW_FAILURE' else None)
            configure(current_bad);row['current_observed']=observe()
            obs=dict(row['current_observed'])
            if mode=='WITHHELD':obs[field]=None
            supplied={field:obs[field]} if arm=='TYPED' else obs
            row['supplied_observed']=supplied;row['decision']=decide(arm,memory,supplied,str(target.id),'click_then_F8')
            row['attempt']=action('attempt') if row['decision']=='TRY' else {'events':[],'committed':False,'saved_bytes':None}
            row['memory_unchanged']=hashlib.sha256(memory.read_bytes()).hexdigest()==row['memory_sha256']
        except BaseException as exc:row['error']=repr(exc)
        finally:
            # Every cleanup stage is attempted even if an earlier one fails.
            if sender is not None:
                try:
                    xtest.fake_input(sender,X.KeyRelease,row.get('keycode',74));sender.sync()
                    xtest.fake_input(sender,X.ButtonRelease,1);sender.sync()
                    row['keymap_empty']=not any(sender.query_keymap())
                    row['buttons_neutral']=not bool(sender.screen().root.query_pointer().mask&(X.Button1Mask|X.Button2Mask|X.Button3Mask))
                except BaseException as exc:cleanup.append('input:'+repr(exc))
                try:sender.close()
                except BaseException as exc:cleanup.append('sender:'+repr(exc))
            if owner is not None:
                for w in windows:
                    try:w.destroy()
                    except BaseException as exc:cleanup.append('window:'+repr(exc))
                try:owner.sync();owner.close()
                except BaseException as exc:cleanup.append('owner:'+repr(exc))
            if server is not None:
                try:server.terminate();row['server_exit']=server.wait(timeout=3)
                except BaseException as exc:
                    cleanup.append('server:'+repr(exc))
                    try:server.kill();row['server_exit']=server.wait(timeout=3)
                    except BaseException as nested:cleanup.append('kill:'+repr(nested))
                if server.stdout:server.stdout.close()
            row['cleanup_errors']=cleanup
    return row

Xatom_STRING=31
def main():
    out=Path(sys.argv[1]);out.mkdir(exist_ok=False)
    with (out/'raw.jsonl').open('x') as f:
        for field in FIELDS:
            for mode in MODES:
                for arm in ARMS:
                    row=fixture(field,mode,arm,out);line=json.dumps(row,sort_keys=True)
                    f.write(line+'\n');f.flush();os.fsync(f.fileno());print(line,flush=True)
                    if 'error' in row or row['cleanup_errors']:raise RuntimeError('first construction STOP preserved')
    with (out/'ENV.json').open('x') as f:json.dump({'python':sys.version,'cgroups':{n:Path('/sys/fs/cgroup',n).read_text().strip() for n in ('cpu.max','memory.max','memory.swap.max','pids.max')}},f,indent=2)
if __name__=='__main__':main()
