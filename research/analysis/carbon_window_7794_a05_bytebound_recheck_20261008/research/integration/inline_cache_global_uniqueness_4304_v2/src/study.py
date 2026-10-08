"""Issue 4304: private X11 unique-target guard boundary. No production authority.

Modes: actor (ordinary X application), policy (bytes-only proposal), construct,
formal. Read-only audit lives in a separate module and imports no study code.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import platform
import select
import secrets
import socket
import struct
import shutil
import subprocess
import sys
import time
import traceback
from typing import Any
from normalize import normalize

W, H, SIZE = 320, 120, 16
SCENARIOS = ('STABLE', 'UNRELATED', 'DUPLICATE', 'MOVED', 'ABSENT', 'DUPLICATE_FULL_UNAVAILABLE')
ARMS = ('LOCAL_PATCH', 'GLOBAL_UNIQUENESS')
SOURCE = Path(__file__).resolve().parent
ALLOCATION = 'inline-cache-uniqueness-4304-20260928-02'

def canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True)

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def store(path: Path, obj: Any) -> None:
    with path.open('x', encoding='utf-8') as f:
        f.write(canonical(obj) + '\n')
        f.flush()
        os.fsync(f.fileno())

def source_hashes() -> dict[str, str]:
    files={p.name:p for p in sorted(SOURCE.glob('*'))
           if p.suffix in ('.py', '.md', '.json', '.sh') and p.name != 'FREEZE.json'}
    files.update({'PATH_GIT_ATTRIBUTES':SOURCE.parent/'.gitattributes',
                  'PLAN.md':SOURCE.parent/'PLAN.md',
                  'ENVIRONMENT.json':SOURCE.parent/'ENVIRONMENT.json'})
    return {name:sha(path.read_bytes()) for name,path in sorted(files.items())}

def rgb(raw: dict) -> bytes:
    b = base64.b64decode(raw['b64'], validate=True)
    if raw['depth'] != 24 or len(b) != raw['w'] * raw['h'] * 4:
        raise ValueError('unsupported pixel ABI')
    return b

def components(raw: dict) -> list[list[int]]:
    """Candidate: group matching horizontal runs by equal x-range and consecutive y."""
    b, w, h = rgb(raw), raw['w'], raw['h']
    stripes: dict[tuple[int, int], list[int]] = {}
    for y in range(h):
        xs = [x for x in range(w) if b[4*(y*w+x):4*(y*w+x)+3] == b'\x00\xff\x00']
        start = prev = None
        for x in xs + [w+1]:
            if prev is not None and x != prev+1:
                stripes.setdefault((start, prev+1), []).append(y)
                start = None
            if x <= w and start is None:
                start = x
            prev = x
    out = []
    for (a, z), ys in stripes.items():
        if z-a == SIZE and len(ys) == SIZE and ys == list(range(ys[0], ys[0]+SIZE)):
            out.append([a, ys[0], SIZE, SIZE])
    return sorted(out)

def policy(req: dict) -> dict:
    """No scenario, actor state, display, scorer path, or future bytes are inputs."""
    out = {'binding': req['binding'], 'authority_granted': False,
           'scan_pixels': 0, 'disposition': 'YIELD', 'point': None, 'cache': None}
    if req['mode'] == 'cold':
        full = req['full']
        cs = components(full)
        out['scan_pixels'] = full['w'] * full['h']
        if len(cs) != 1:
            raise ValueError('cold acquisition must be unique')
        x,y,w,h = cs[0]
        b = rgb(full)
        patch = b''.join(b[4*((y+j)*W+x):4*((y+j)*W+x+w)] for j in range(h))
        out.update(disposition='CACHED', cache={'rect': cs[0], 'patch_sha':sha(patch),
                                               'binding':req['binding']})
        return out
    cache = req['cache']
    if cache['binding'] != req['binding']:
        out['reason'] = 'BINDING_MISMATCH'
        return out
    if req['arm'] == 'LOCAL_PATCH':
        patch = req['patch']
        b = rgb(patch)
        out['scan_pixels'] += patch['w'] * patch['h']
        if sha(b) == cache['patch_sha']:
            x,y,w,h = cache['rect']
            out.update(disposition='PROPOSE', point=[x+w//2,y+h//2], reason='LOCAL_HIT')
            return out
        out['reason'] = 'DEOPT'
    elif req['arm'] != 'GLOBAL_UNIQUENESS':
        raise ValueError('unknown arm')
    if req.get('full') is None:
        out['reason'] = 'FULL_UNAVAILABLE'
        return out
    full = req['full']
    cs = components(full)
    out['scan_pixels'] += full['w'] * full['h']
    if len(cs) == 1:
        x,y,w,h = cs[0]
        out.update(disposition='PROPOSE', point=[x+w//2,y+h//2], reason='FULL_UNIQUE')
    else:
        out['reason'] = 'AMBIGUOUS' if cs else 'ABSENT'
    return out

def actor(logpath: Path) -> None:
    from Xlib import X, display
    d = display.Display()
    root = d.screen().root
    win = root.create_window(0,0,W,H,0,d.screen().root_depth,X.InputOutput,X.CopyFromParent,
                             background_pixel=0,override_redirect=True,
                             event_mask=X.ButtonPressMask|X.ButtonReleaseMask|X.StructureNotifyMask)
    win.set_wm_name('Issue4304 private unique-target fixture')
    gc = win.create_gc()
    win.map(); d.sync()
    targets: list[list[int]] = []
    events: list[dict] = []
    effects: list[dict] = []
    down = None
    log = logpath.open('x', encoding='utf-8')
    def journal(kind: str, **kw: Any) -> dict:
        rec = {'kind':kind,'ns':time.monotonic_ns(),'pid':os.getpid(),**kw}
        log.write(canonical(rec)+'\n'); log.flush()
        return rec
    def drain() -> None:
        nonlocal down
        while d.pending_events():
            ev = d.next_event()
            if ev.type not in (X.ButtonPress, X.ButtonRelease):
                continue
            item = journal('input',type=ev.type,button=ev.detail,x=ev.event_x,y=ev.event_y,
                           server_time=ev.time,send_event=bool(ev.send_event),window=ev.window.id)
            events.append(item)
            hit = next((r for r in targets if r[0] <= ev.event_x < r[0]+r[2]
                        and r[1] <= ev.event_y < r[1]+r[3]), None)
            if ev.type == X.ButtonPress:
                down = hit
            else:
                if hit is not None and down == hit and ev.detail == 1:
                    effects.append(journal('effect',target=hit,ordinal=len(effects)+1))
                down = None
    journal('ready',window=win.id)
    print(canonical({'ready':True,'pid':os.getpid(),'window':win.id}), flush=True)
    while True:
        r,_,_ = select.select([sys.stdin,d.fileno()],[],[],5)
        if not r:
            raise TimeoutError('actor idle bound')
        drain()
        if sys.stdin not in r:
            continue
        line = sys.stdin.readline()
        if not line:
            raise EOFError('actor command pipe')
        cmd = json.loads(line)
        journal('command',command=cmd)
        if cmd['op'] == 'draw':
            targets = cmd['targets']
            gc.change(foreground=0); win.fill_rectangle(gc,0,0,W,H)
            gc.change(foreground=0x00ff00)
            for rect in targets:
                win.fill_rectangle(gc,*rect)
            if cmd['nuisance']:
                gc.change(foreground=0x0000ff); win.fill_rectangle(gc,100,8,12,12)
            d.sync(); drain()
            journal('draw',targets=targets,nuisance=cmd['nuisance'])
        elif cmd['op'] not in ('snapshot','close'):
            raise ValueError('actor command')
        d.sync(); drain()
        reply = {'id':cmd['id'],'pid':os.getpid(),'window':win.id,'ns':time.monotonic_ns(),
                 'events':list(events),'effects':list(effects)}
        journal('reply',reply=reply)
        print(canonical(reply), flush=True)
        if cmd['op'] == 'close':
            journal('exit'); log.close(); d.close()
            return

class Peer:
    def __init__(self, argv: list[str], cwd: Path, env: dict, err: Path):
        self.err = err.open('xb')
        self.p = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=self.err,cwd=cwd,env=env,bufsize=0)
        self.argv, self.wire, self.buf = argv, [], b''
    def read(self) -> dict:
        until = time.monotonic()+4
        while b'\n' not in self.buf:
            remaining = until-time.monotonic()
            if remaining <= 0 or not select.select([self.p.stdout],[],[],remaining)[0]:
                raise TimeoutError('peer read')
            block = os.read(self.p.stdout.fileno(),65536)
            if not block:
                raise EOFError('peer exited')
            self.buf += block
        raw,self.buf = self.buf.split(b'\n',1)
        self.wire.append({'direction':'recv','ns':time.monotonic_ns(),'text':raw.decode()+'\n'})
        return json.loads(raw)
    def call(self, cmd: dict) -> dict:
        raw = (canonical(cmd)+'\n').encode()
        self.wire.append({'direction':'send','ns':time.monotonic_ns(),'text':raw.decode()})
        sent=0
        while sent<len(raw):
            n=os.write(self.p.stdin.fileno(),raw[sent:])
            if n<=0: raise IOError('short pipe write made no progress')
            sent+=n
        return self.read()
    def finish(self) -> dict:
        if self.p.poll() is None:
            self.p.terminate()
        try:
            code = self.p.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.p.kill(); code=self.p.wait(timeout=3)
        self.err.close()
        return {'pid':self.p.pid,'argv':self.argv,'exit':code,'wire':self.wire}

def observe(d: Any, window: Any, rect: list[int], role: str) -> dict:
    from Xlib import X
    start = time.monotonic_ns()
    image = window.get_image(*rect,X.ZPixmap,0xffffffff)
    end = time.monotonic_ns()
    b = normalize(image.data)
    assert image.depth == 24 and len(b)==rect[2]*rect[3]*4
    return {'rect':rect,'w':rect[2],'h':rect[3],'depth':image.depth,
            'python_data_type':type(image.data).__name__,
            'b64':base64.b64encode(b).decode(),'sha256':sha(b),'nbytes':len(b),
            'start_ns':start,'end_ns':end,'role':role,'window':window.id}

def neutrality(d: Any) -> dict:
    return {'keymap':list(d.query_keymap()),'button_mask':d.screen().root.query_pointer().mask & 0x1f00,
            'ns':time.monotonic_ns()}

def one_case(out: Path, caseid: str, arm: str, scenario: str, rep: int) -> dict:
    from Xlib import X, display
    from Xlib.ext import xtest
    case = out/caseid; case.mkdir()
    result: dict = {'id':caseid,'arm':arm,'scenario':scenario,'rep':rep,'binding_generation':1,
                    'controller_pid':os.getpid(),'status':'STARTED','input':[], 'sources':source_hashes()}
    store(case/'START.json',result)
    app=pol=xproc=None; d=None; display_num=None
    readfd,writefd=os.pipe()
    xerr=(case/'xvfb.stderr').open('xb')
    cookie=secrets.token_bytes(16)
    def authority(family, address, number):
        fields=(address,number,b'MIT-MAGIC-COOKIE-1',cookie)
        return struct.pack('!H',family)+b''.join(struct.pack('!H',len(x))+x for x in fields)
    server_auth=case/'server.Xauthority'; client_auth=case/'client.Xauthority'
    server_auth.write_bytes(authority(65535,b'',b'')); server_auth.chmod(0o600)
    try:
        # Only this fresh disposable local display. No host DISPLAY, TCP, or GUI data.
        argv=[shutil.which('Xvfb'),'-displayfd',str(writefd),'-screen','0',f'{W}x{H}x24',
              '-nolisten','tcp','-auth',str(server_auth),'-noreset']
        xproc=subprocess.Popen(argv,pass_fds=(writefd,),stdout=subprocess.DEVNULL,stderr=xerr)
        os.close(writefd); writefd=-1
        if not select.select([readfd],[],[],4)[0]: raise TimeoutError('Xvfb ready')
        display_num=int(os.read(readfd,64).strip())
        if xproc.poll() is not None: raise RuntimeError('Xvfb exited')
        result['display']=display_num
        env=dict(os.environ,DISPLAY=f':{display_num}')
        client_auth.write_bytes(authority(256,socket.gethostname().encode(),str(display_num).encode()))
        client_auth.chmod(0o600)
        env['XAUTHORITY']=str(client_auth)
        result['auth']={'server_sha256':sha(server_auth.read_bytes()),
                        'client_sha256':sha(client_auth.read_bytes()),'scheme':'MIT-MAGIC-COOKIE-1'}
        app=Peer([sys.executable,'-B',str(SOURCE/'study.py'),'actor',str(case/'actor.jsonl')],case,env,case/'actor.stderr')
        ready=app.read(); result['ready']=ready
        old_auth=os.environ.get('XAUTHORITY')
        os.environ['XAUTHORITY']=str(client_auth)
        try: d=display.Display(f':{display_num}')
        finally:
            if old_auth is None: os.environ.pop('XAUTHORITY',None)
            else: os.environ['XAUTHORITY']=old_auth
        assert d.has_extension('XTEST')
        window=d.create_resource_object('window',ready['window'])
        assert window.get_attributes().map_state==X.IsViewable
        result['window_geometry']={'width':window.get_geometry().width,'height':window.get_geometry().height}
        result['pre_neutral']=neutrality(d)
        seq=0
        def call(op: str, **kw: Any) -> dict:
            nonlocal seq
            seq+=1
            return app.call({'op':op,'id':seq,**kw})
        result['cold_draw']=call('draw',targets=[[32,48,SIZE,SIZE]],nuisance=False)
        cold=observe(d,window,[0,0,W,H],'candidate_cold')
        binding={'session':caseid,'window':ready['window'],'generation':1,'domain':[0,0,W,H]}
        # Policy child has no DISPLAY or scorer path; stdin carries its complete contract.
        penv={k:v for k,v in os.environ.items() if k not in ('DISPLAY','XAUTHORITY')}
        pol=Peer([sys.executable,'-B',str(SOURCE/'study.py'),'policy'],SOURCE,penv,case/'policy.stderr')
        cr={'mode':'cold','binding':binding,'full':cold}
        cp=pol.call(cr); result['cold']={'request':cr,'response':cp}
        if cp['disposition']!='CACHED': raise ValueError('no cold cache')
        targets={'STABLE':[[32,48,SIZE,SIZE]],'UNRELATED':[[32,48,SIZE,SIZE]],
                 'DUPLICATE':[[32,48,SIZE,SIZE],[240,48,SIZE,SIZE]],
                 'MOVED':[[240,48,SIZE,SIZE]],'ABSENT':[],
                 'DUPLICATE_FULL_UNAVAILABLE':[[32,48,SIZE,SIZE],[240,48,SIZE,SIZE]]}[scenario]
        result['warm_draw']=call('draw',targets=targets,nuisance=scenario=='UNRELATED')
        witness=observe(d,window,[0,0,W,H],'scorer_only')
        result['witness']=witness
        req={'mode':'warm','arm':arm,'binding':binding,'cache':cp['cache'],'full':None,'patch':None}
        available=scenario!='DUPLICATE_FULL_UNAVAILABLE'
        if arm=='LOCAL_PATCH':
            req['patch']=observe(d,window,cp['cache']['rect'],'candidate_patch')
            # Lazy full observation is requested only when the same exact-patch condition fails.
            if req['patch']['sha256']!=cp['cache']['patch_sha'] and available:
                req['full']=observe(d,window,[0,0,W,H],'candidate_full')
        elif available:
            req['full']=observe(d,window,[0,0,W,H],'candidate_full')
        result['full_available']=available
        result['warm_request_ns']=time.monotonic_ns()
        prop=pol.call(req); result['warm']={'request':req,'response':prop}
        result['warm_response_ns']=time.monotonic_ns()
        if prop['disposition']=='PROPOSE':
            x,y=prop['point']
            assert type(x) is int and type(y) is int and 0<=x<W and 0<=y<H
            d.xtest_fake_input(X.MotionNotify,x=x,y=y); d.sync()
            for kind in (X.ButtonPress,X.ButtonRelease):
                before=time.monotonic_ns()
                d.xtest_fake_input(kind,detail=1); d.sync()
                result['input'].append({'type':kind,'button':1,'x':x,'y':y,
                                        'start_ns':before,'end_ns':time.monotonic_ns()})
        result['final_snapshot']=call('snapshot')
        result['post_neutral']=neutrality(d)
        result['final_witness']=observe(d,window,[0,0,W,H],'scorer_only_final')
        result['close']=call('close')
        assert app.p.wait(timeout=3)==0
        pol.p.stdin.close(); assert pol.p.wait(timeout=3)==0
        result['status']='COMPLETE'
    except BaseException as exc:
        result['status']='STOP'
        result['exception']=type(exc).__name__+': '+str(exc)
        result['traceback']=traceback.format_exc()
    finally:
        # Unconditional safety release if an exception interrupted a click; do not label success.
        if d is not None:
            try:
                if d.screen().root.query_pointer().mask & X.Button1Mask:
                    d.xtest_fake_input(X.ButtonRelease,detail=1);d.sync()
                    result['emergency_release']=True
                d.close()
            except Exception as exc: result['cleanup_error']=repr(exc)
        if app: result['actor_process']=app.finish()
        if pol: result['policy_process']=pol.finish()
        if xproc:
            xproc.terminate()
            try: code=xproc.wait(timeout=3)
            except subprocess.TimeoutExpired: xproc.kill();code=xproc.wait(timeout=3)
            result['xvfb_process']={'pid':xproc.pid,'argv':argv,'exit':code}
        if writefd>=0: os.close(writefd)
        os.close(readfd); xerr.close()
        result['socket_absent']=display_num is not None and not Path(f'/tmp/.X11-unix/X{display_num}').exists()
        result['lock_absent']=display_num is not None and not Path(f'/tmp/.X{display_num}-lock').exists()
        for auth in (server_auth,client_auth):
            auth.unlink(missing_ok=True)
        result['auth_removed']=not server_auth.exists() and not client_auth.exists()
        result['completed_ns']=time.monotonic_ns()
        store(case/'RAW.json',result)
    return result

def batch(out: Path, rep: int, construction: bool=False) -> None:
    out.mkdir(parents=True,exist_ok=False)
    store(out/'INVOCATION.json',{'allocation':ALLOCATION,'rep':rep,'construction':construction,
         'sources':source_hashes(),'start_ns':time.monotonic_ns(),'pid':os.getpid(),
         'argv':sys.argv,'platform':platform.platform(),'python':sys.version})
    schedule = [('STABLE','LOCAL_PATCH'),('MOVED','LOCAL_PATCH'),
                ('DUPLICATE','GLOBAL_UNIQUENESS'),('ABSENT','GLOBAL_UNIQUENESS')] if construction else [
        (s,a) for s in (SCENARIOS if rep==0 else tuple(reversed(SCENARIOS)))
        for a in (ARMS if rep==0 else tuple(reversed(ARMS)))]
    completed=[]
    for i,(scenario,arm) in enumerate(schedule):
        caseid=f'{"construction" if construction else "formal"}-{rep}-{i:02d}'
        rec=one_case(out,caseid,arm,scenario,rep)
        completed.append({'id':caseid,'status':rec['status'],'raw_sha256':sha((out/caseid/'RAW.json').read_bytes())})
        print(canonical({'id':caseid,'status':rec['status'],'exception':rec.get('exception')}),flush=True)
        if rec['status']!='COMPLETE':
            store(out/'BATCH.json',{'status':'STOP','completed':completed,'end_ns':time.monotonic_ns()})
            raise SystemExit(2)
    store(out/'BATCH.json',{'status':'COMPLETE','completed':completed,'end_ns':time.monotonic_ns()})

if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='actor': actor(Path(sys.argv[2]))
    elif mode=='policy':
        for line in sys.stdin:
            print(canonical(policy(json.loads(line))),flush=True)
    elif mode=='construct': batch(Path(sys.argv[2]).resolve(),0,True)
    elif mode=='formal':
        root=Path(sys.argv[2]).resolve(); rep=int(sys.argv[3])
        if rep not in (0,1): raise ValueError('rep must be 0 or 1')
        freeze=json.loads((SOURCE/'FREEZE.json').read_text())
        if freeze['sources']!=source_hashes(): raise ValueError('SOURCE FREEZE MISMATCH')
        if rep==0:
            root.mkdir(exist_ok=False)
        else:
            if not root.is_dir() or {p.name for p in root.iterdir()}!={'batch-0'}:
                raise ValueError('unexpected formal output root contents')
            if json.loads((root/'batch-0'/'BATCH.json').read_text())['status']!='COMPLETE':
                raise ValueError('prior batch incomplete')
        batch(root/f'batch-{rep}',rep)
    else: raise ValueError('mode')
