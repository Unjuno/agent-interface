"""Native acquisition and process receipts; the cue is never an application key."""
import base64
import hashlib
import json
import os
from pathlib import Path
import select
import socket
import struct
import subprocess
import sys
import tempfile
import time
import traceback
from Xlib import X, display

ROOT = Path(__file__).resolve().parent.parent
SCENARIOS = ('NO_CUE', 'VALID', 'OLD_GENERATION', 'FOREIGN_SESSION', 'WRONG_SURFACE',
             'FUTURE_TIME', 'EXPIRED_TIME', 'ROI_OUTSIDE', 'MISSING_HISTORY', 'AUTHORITY_FIELD')


def dump(path, value):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(value, f, sort_keys=True, indent=2)
        f.write('\n')


def one(out, name, session):
    out.mkdir(parents=True, exist_ok=False)
    record = {'scenario': name, 'session': session, 'wire': [], 'processes': [], 'error': None}
    children, conn = [], None
    temp = tempfile.TemporaryDirectory(prefix='ac41-')
    private = Path(temp.name)
    try:
        n = next(n for n in range(700, 1700) if not Path(f'/tmp/.X11-unix/X{n}').exists()
                 and not Path(f'/tmp/.X{n}-lock').exists())
        auth = private/'auth'
        fields = (socket.gethostname().encode(), str(n).encode(), b'MIT-MAGIC-COOKIE-1', os.urandom(16))
        auth.write_bytes(struct.pack('>H', 256)+b''.join(struct.pack('>H',len(v))+v for v in fields))
        auth.chmod(0o600)
        env = dict(os.environ, DISPLAY=f':{n}', XAUTHORITY=str(auth), PYTHONDONTWRITEBYTECODE='1')
        args = ['Xvfb', f':{n}', '-screen', '0', '128x96x24', '-nolisten', 'tcp', '-auth', str(auth), '-noreset']
        server_log = (out/'server.stderr').open('wb')
        server = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=server_log, env=env)
        children.append(('server', server, args, server_log))
        until = time.monotonic()+5
        while not Path(f'/tmp/.X11-unix/X{n}').exists():
            if server.poll() is not None or time.monotonic()>until:
                raise RuntimeError('X_SERVER_START_FAILED')
            time.sleep(.01)
        old_auth = os.environ.get('XAUTHORITY')
        os.environ['XAUTHORITY'] = str(auth)
        try:
            conn = display.Display(f':{n}')
        finally:
            if old_auth is None: os.environ.pop('XAUTHORITY', None)
            else: os.environ['XAUTHORITY'] = old_auth
        fmt = [f for f in conn.display.info.pixmap_formats if f.depth == 24][0]
        record['layout'] = {'depth':24,'bits_per_pixel':fmt.bits_per_pixel,
                            'image_byte_order':conn.display.info.image_byte_order,
                            'scanline_pad':fmt.scanline_pad}
        if fmt.bits_per_pixel != 32 or conn.display.info.image_byte_order != 0:
            raise RuntimeError('UNSUPPORTED_PIXEL_LAYOUT')
        args = [sys.executable, '-B', str(ROOT/'source/actor.py')]
        actor_log = (out/'actor.stderr').open('wb')
        actor = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=actor_log, text=True, env=env)
        children.append(('actor', actor, args, actor_log))
        def receive():
            if not select.select([actor.stdout], [], [], 5)[0]:
                raise RuntimeError('ACTOR_REPLY_TIMEOUT')
            line = actor.stdout.readline()
            if not line: raise RuntimeError('ACTOR_EOF')
            answer = json.loads(line)
            record['wire'].append({'direction':'receive','value':answer})
            return answer
        def ask(op, **kw):
            cmd = {'op':op, **kw}
            record['wire'].append({'direction':'send','value':cmd})
            actor.stdin.write(json.dumps(cmd)+'\n'); actor.stdin.flush()
            return receive()
        ready = receive()
        win = conn.create_resource_object('window', ready['surface'])
        current = {'session':session, 'surface':win.id,'generation':3}
        def capture(i):
            raw = win.get_image(0,0,64,48,X.ZPixmap,0xffffffff)
            return {**current,'frame_id':i,'captured_ns':time.monotonic_ns(),
                    'pixels_b64':base64.b64encode(raw.data.encode('latin1') if isinstance(raw.data,str) else raw.data).decode('ascii')}
        frames=[]
        for i in (1,2,3):
            ask('DRAW',state=i)
            frames.append(capture(i))
        record['all_frames'] = frames
        record['before'] = ask('INSPECT')
        record['keymap_before'] = bytes(conn.query_keymap()).hex()
        record['buttons_before'] = conn.screen().root.query_pointer().mask
        stamp = time.monotonic_ns()
        cue = {'cue_id':session+'-cue','session':session,'surface':win.id,'generation':3,
               'emitted_ns':stamp,'roi':[32,8,16,16]}
        if name == 'NO_CUE': cue=None
        elif name == 'OLD_GENERATION': cue['generation']=2
        elif name == 'FOREIGN_SESSION': cue['session']='other-session'
        elif name == 'WRONG_SURFACE': cue['surface']+=1
        elif name == 'FUTURE_TIME': cue['emitted_ns']+=10_000_000_000
        elif name == 'EXPIRED_TIME': cue['emitted_ns']-=3_000_000_000
        elif name == 'ROI_OUTSIDE': cue['roi']=[60,40,16,16]
        elif name == 'AUTHORITY_FIELD': cue['authority_granted']=True
        req={'current':current,'frames':frames[-1:] if name=='MISSING_HISTORY' else frames,'cue':cue}
        record['request']=req
        args=[sys.executable,'-B',str(ROOT/'source/engine.py')]
        engine=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
        children.append(('engine',engine,args,None))
        engine_in=json.dumps(req,sort_keys=True)+'\n'
        engine_out, engine_err=engine.communicate(engine_in,timeout=8)
        record['engine_stdin']=engine_in
        record['engine_stdout']=engine_out
        record['engine_stderr']=engine_err
        if engine.returncode: raise RuntimeError('ENGINE_FAILED')
        record['response']=json.loads(engine_out)
        record['after']=ask('INSPECT')
        record['frame_after']=capture(3)
        record['keymap_after']=bytes(conn.query_keymap()).hex()
        record['buttons_after']=conn.screen().root.query_pointer().mask
        ask('CLOSE'); actor.stdin.close(); actor.wait(timeout=5)
        conn.close(); conn=None
    except Exception:
        record['error']=traceback.format_exc()
    finally:
        if conn is not None:
            try: conn.close()
            except Exception: pass
        for role, p, argv, handle in reversed(children):
            if p.poll() is None: p.terminate()
            try: rc=p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill(); rc=p.wait(timeout=5)
            if handle: handle.close()
            record['processes'].append({'role':role,'pid':p.pid,'argv':argv,'returncode':rc})
        record['socket_removed']=not Path(f'/tmp/.X11-unix/X{n}').exists() if 'n' in locals() else False
        temp.cleanup()
        dump(out/'case.json',record)
    if record['error']: raise RuntimeError(record['error'])


def main():
    phase, batch = sys.argv[1], int(sys.argv[2])
    if phase not in ('construction','formal'): raise ValueError('phase')
    directory=ROOT/phase/f'b{batch}'
    directory.mkdir(parents=True,exist_ok=False)
    cases = [('VALID',0),('OLD_GENERATION',0),('MISSING_HISTORY',0)] if phase=='construction' else [
        (SCENARIOS[i%10],i//10) for i in range(batch*5,batch*5+5)]
    dump(directory/'START.json',{'pid':os.getpid(),'phase':phase,'batch':batch,'cases':cases,'at_ns':time.monotonic_ns()})
    for i,(name,rep) in enumerate(cases):
        one(directory/f'c{i}',name,f'ac41-{phase}-b{batch}-c{i}-r{rep}')
    dump(directory/'END.json',{'cases':len(cases),'at_ns':time.monotonic_ns()})
    print(json.dumps({'batch':batch,'cases':len(cases)}))


if __name__=='__main__': main()
