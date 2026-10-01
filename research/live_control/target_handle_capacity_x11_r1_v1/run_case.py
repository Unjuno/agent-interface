import argparse,json,os,subprocess,sys,time
from collections import OrderedDict
from pathlib import Path
from PIL import Image
from Xlib import X,display
from Xlib.ext import xtest

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'vendor'))
from scoped_target_handle_v1 import TargetHandleStore
from patterns import SIZE,template_bytes

SCREEN_W,SCREEN_H=480,320

def wait_display(n,timeout=3):
    sock=f'/tmp/.X11-unix/X{n}';t=time.time()+timeout
    while time.time()<t:
        if os.path.exists(sock):return
        time.sleep(.01)
    raise RuntimeError('xvfb socket timeout')

def find_window(d,title):
    root=d.screen().root
    deadline=time.time()+3
    while time.time()<deadline:
        for w in root.query_tree().children:
            try:
                if w.get_wm_name()==title:return w
            except Exception:pass
        time.sleep(.01)
    raise RuntimeError('surface not found')

def capture(d):
    root=d.screen().root
    raw=root.get_image(0,0,SCREEN_W,SCREEN_H,X.ZPixmap,0xffffffff)
    return Image.frombytes('RGB',(SCREEN_W,SCREEN_H),raw.data,'raw','BGRX')

def full_find(image,label):
    data=image.tobytes(); W,H=image.size; stride=W*3; tpl=template_bytes(label); tw=SIZE;th=SIZE; row0=tpl[:tw*3]; hits=[]
    for y in range(H-th+1):
        lo=y*stride;hi=lo+stride; pos=data.find(row0,lo,hi)
        while pos!=-1:
            if (pos-lo)%3==0:
                x=(pos-lo)//3
                if x<=W-tw:
                    ok=True
                    for dy in range(1,th):
                        if data[(y+dy)*stride+x*3:(y+dy)*stride+(x+tw)*3] != tpl[dy*tw*3:(dy+1)*tw*3]: ok=False;break
                    if ok:hits.append((x,y))
            pos=data.find(row0,pos+1,hi)
    if len(hits)!=1:raise RuntimeError(f'ground {label} hits={hits[:5]} n={len(hits)}')
    return hits[0]

def geom(w):
    g=w.get_geometry();return [int(g.x),int(g.y),int(g.width),int(g.height)]

def obs(seq,ns,w,focus):
    if int(focus) != int(w.id):
        raise RuntimeError(f'focus mismatch focus={focus} surface={w.id}')
    return {'sequence':seq,'capture_ns':ns,'pointer_binding':{'focus':int(focus),'surface':int(w.id),'geometry':geom(w)}}

def click(d,x,y):
    xtest.fake_input(d,X.MotionNotify,x=int(x),y=int(y));d.sync()
    xtest.fake_input(d,X.ButtonPress,1);d.sync();xtest.fake_input(d,X.ButtonRelease,1);d.sync()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--capacity',type=int,required=True);ap.add_argument('--replace',action='store_true');ap.add_argument('--display',type=int,default=171);ap.add_argument('--out',required=True);args=ap.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True);logp=out/'fixture.jsonl';cmd=out/'cmd';cmd.write_text('')
    title=f'ai1704-{os.getpid()}-{args.capacity}-{int(args.replace)}';env=os.environ.copy();env['DISPLAY']=f':{args.display}';auth=out/'xauth';auth.write_bytes(b'');env['XAUTHORITY']=str(auth);os.environ['XAUTHORITY']=str(auth)
    xvfb=subprocess.Popen(['Xvfb',env['DISPLAY'],'-screen','0',f'{SCREEN_W}x{SCREEN_H}x24','-nolisten','tcp','-ac'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    fixture=None;d=None
    try:
        wait_display(args.display)
        fixture=subprocess.Popen([sys.executable,str(HERE/'fixture.py'),'--title',title,'--log',str(logp),'--command',str(cmd)],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
        d=display.Display(env['DISPLAY']);w=find_window(d,title);w.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync()
        store=TargetHandleStore('ai1704-session',id_factory=(f'h{i}' for i in range(20)).__next__);cache=OrderedDict();seq=0;ground=0;reuse=0;old_probes=[];steps=[]
        for idx,label in enumerate(('A','B','A','B')):
            if args.replace and idx==2:
                old_surface=int(w.id);cmd.write_text('replace')
                deadline=time.time()+3
                while time.time()<deadline:
                    try:nw=find_window(d,title)
                    except RuntimeError:continue
                    if int(nw.id)!=old_surface:w=nw;break
                    time.sleep(.01)
                else:raise RuntimeError('surface did not replace')
                w.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync(); seq+=1; capns=time.monotonic_ns();im=capture(d);focus=int(d.get_input_focus().focus.id);o=obs(seq,capns,w,focus)
                for key,hid in list(cache.items()):
                    rr=store.resolve_point(hid,[SIZE//2,SIZE//2],o,im,time.monotonic_ns(),session_scope='ai1704-session')
                    old_probes.append({'target':key,'status':rr['status'],'eligible':rr['eligible'],'old_surface':old_surface,'new_surface':int(w.id)})
                cache.clear()
            w=find_window(d,title);w.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync(); seq+=1;capns=time.monotonic_ns();im=capture(d);focus=int(d.get_input_focus().focus.id);o=obs(seq,capns,w,focus)
            source='reuse';rr=None
            if label in cache:
                hid=cache.pop(label);cache[label]=hid
                rr=store.resolve_point(hid,[SIZE//2,SIZE//2],o,im,time.monotonic_ns(),session_scope='ai1704-session')
                if rr['eligible']:reuse+=1
                else:cache.pop(label,None);rr=None
            if rr is None:
                source='ground';ground+=1;x,y=full_find(im,label)
                mint=store.mint(label,'screen_chrome',[x,y,SIZE,SIZE],o,im,time.monotonic_ns(),ttl_ms=30000,freshness_ms=1000,search_radius=0)
                cache[label]=mint['handle']
                while len(cache)>args.capacity:cache.popitem(last=False)
                rr=store.resolve_point(mint['handle'],[SIZE//2,SIZE//2],o,im,time.monotonic_ns(),session_scope='ai1704-session')
            if not rr['eligible']:raise RuntimeError(f'noneligible {rr}')
            px,py=rr['point'];click(d,px,py);time.sleep(.03)
            steps.append({'i':idx,'target':label,'source':source,'status':rr['status'],'surface':int(w.id),'point':rr['point']})
        time.sleep(.05)
        # fixture ledger read only after all actions
        led=[json.loads(x) for x in logp.read_text().splitlines() if x.strip()]
        clicks=[x for x in led if x['event']=='click'];surface_events=[x for x in led if x['event']=='surface']
        mask=int(d.screen().root.query_pointer().mask);neutral=(mask & int(X.Button1Mask))==0
        result={'capacity':args.capacity,'replace':args.replace,'groundings':ground,'reuses':reuse,'old_probes':old_probes,'steps':steps,'fixture_clicks':clicks,'surface_events':surface_events,'terminal_button_neutral':neutral}
        (out/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True))
    finally:
        if d is not None:
            try:d.close()
            except Exception:pass
        if fixture is not None:
            fixture.terminate()
            try:fixture.wait(timeout=2)
            except:fixture.kill()
        xvfb.terminate()
        try:xvfb.wait(timeout=2)
        except:xvfb.kill()
if __name__=='__main__':main()
