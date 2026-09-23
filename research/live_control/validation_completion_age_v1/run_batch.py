"""One seven-case private-X11 batch. Explicit verification-delay injection only."""
from __future__ import annotations
import argparse, base64, hashlib, json, os, selectors, socket, struct, subprocess, sys, time, traceback
from pathlib import Path
from Xlib import display as xdisplay, X
import legacy_transport as legacy
from candidate import finalize

HERE=Path(__file__).resolve().parent
CASES=['PROMPT_VALID','DELAYED_UNCHANGED','DELAYED_CHANGED','PROMPT_CHANGED',
       'STALE_BEFORE_RECEIPT','BAD_DIGEST','WRONG_ID']
DELAY_NS=60_000_000

def write_json(path: Path, obj: object) -> None:
    with path.open('x',encoding='utf-8') as f:
        json.dump(obj,f,separators=(',',':'),sort_keys=True); f.write('\n'); f.flush(); os.fsync(f.fileno())

def wait_until(deadline: int) -> None:
    while (left:=deadline-time.monotonic_ns())>0: time.sleep(left/1e9)

def read_line(proc: subprocess.Popen, timeout: float=2) -> tuple[bytes,int]:
    out=bytearray(); end=time.monotonic()+timeout
    with selectors.DefaultSelector() as sel:
        sel.register(proc.stdout,selectors.EVENT_READ)
        while not out.endswith(b'\n'):
            if not sel.select(max(0,end-time.monotonic())): raise TimeoutError('fixture response timeout')
            block=os.read(proc.stdout.fileno(),32768)
            if not block: raise EOFError('fixture response ended')
            out.extend(block)
            if len(out)>32768 or b'\n' in out[:-1]: raise ValueError('unbounded/multiple fixture response')
    return bytes(out),time.monotonic_ns()

def rpc(proc: subprocess.Popen, request: dict, transcript: list) -> tuple[dict,int]:
    wire=(json.dumps(request,separators=(',',':'))+'\n').encode()
    before=time.monotonic_ns(); count=proc.stdin.write(wire)
    if count!=len(wire): raise OSError('short fixture request')
    raw,received=read_line(proc); obj=json.loads(raw)
    if obj.get('op')!=request['op'] or obj.get('pid')!=proc.pid: raise ValueError('fixture identity mismatch')
    transcript.append({'request':wire.decode(),'response':raw.decode(),'before_ns':before,'received_ns':received})
    return obj['result'],received

def auth_bytes(cookie: bytes, number: str='') -> bytes:
    fields=[socket.gethostname().encode(),number.encode(),b'MIT-MAGIC-COOKIE-1',cookie]
    return struct.pack('!H',256)+b''.join(struct.pack('!H',len(x))+x for x in fields)

def oracle(d) -> dict:
    root=d.screen().root; before=time.monotonic_ns()
    im=root.get_image(48,48,32,32,X.ZPixmap,0xffffffff)
    keys=d.query_keymap(); keys=list(keys.encode('latin1') if isinstance(keys,str) else keys)
    pixels=im.data.encode('latin1') if isinstance(im.data,str) else bytes(im.data)
    mask=root.query_pointer().mask; after=time.monotonic_ns()
    if im.depth!=24 or len(pixels)!=4096: raise RuntimeError('independent Xlib capture layout mismatch')
    return {'before_ns':before,'after_ns':after,'pixels_b64':base64.b64encode(pixels).decode(),
            'keymap':keys,'pointer_mask':mask,'depth':im.depth,'authority':False}

def run(index: int, out: Path, construction: bool) -> None:
    if index not in range(3): raise ValueError('batch index outside frozen schedule')
    out.mkdir(parents=True,exist_ok=False)
    state={'batch':index,'construction':construction,'cases':[],'model_calls':0,'input_calls':0,'authority':False,
           'status':'STARTED','python':sys.version,'pid':os.getpid(),'started_ns':time.monotonic_ns()}
    xv=actor=d=None; readfd=writefd=None
    oldauth=os.environ.get('XAUTHORITY'); auth=out/'private.xauth'; cookie=os.urandom(16)
    auth.write_bytes(auth_bytes(cookie)); auth.chmod(0o600); os.environ['XAUTHORITY']=str(auth)
    try:
        readfd,writefd=os.pipe()
        cmd=['Xvfb','-displayfd',str(writefd),'-screen','0','128x128x24','-nolisten','tcp','-noreset','-auth',str(auth)]
        with (out/'xvfb.stderr').open('xb') as err:
            xv=subprocess.Popen(cmd,pass_fds=(writefd,),stdout=subprocess.DEVNULL,stderr=err)
        os.close(writefd);writefd=None
        with selectors.DefaultSelector() as sel:
            sel.register(readfd,selectors.EVENT_READ)
            if not sel.select(3): raise TimeoutError('Xvfb readiness timeout')
        number=os.read(readfd,100).decode().strip()
        if not number.isdecimal(): raise ValueError('invalid display number')
        auth.write_bytes(auth_bytes(cookie,number)); disp=':'+number
        state.update({'xvfb_pid':xv.pid,'xvfb_command':cmd,'display':disp,'auth_enabled':True,
                      'display_socket':f'/tmp/.X11-unix/X{number}'})
        d=xdisplay.Display(disp)
        acmd=[sys.executable,'-B',str(HERE/'actor.py'),disp]
        with (out/'actor.stderr').open('xb') as err:
            actor=subprocess.Popen(acmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,bufsize=0)
        line,stamp=read_line(actor); ready=json.loads(line)
        if ready.get('pid')!=actor.pid or ready.get('event')!='ready': raise ValueError('actor readiness invalid')
        state.update({'actor_pid':actor.pid,'actor_command':acmd,'ready_wire':line.decode(),'ready_ns':stamp})
        order=CASES[index:]+CASES[:index]
        for mode in order:
            cid=f'{"construction" if construction else "formal"}-b{index}-{mode}'; wire=[]
            initial,_=rpc(actor,{'op':'paint','count':0},wire)
            before=oracle(d)
            cap,received=rpc(actor,{'op':'capture','case_id':cid,'bad_digest':mode=='BAD_DIGEST',
                                    'wrong_id':mode=='WRONG_ID'},wire)
            packet=base64.b64decode(cap['packet_b64'],validate=True)
            transport_received=received
            if mode=='STALE_BEFORE_RECEIPT':
                wait_until(received+DELAY_NS);received=time.monotonic_ns()
            digest=[]; original=legacy.pixel_digest
            def delayed_digest(pixels: bytes, chunked: bool=False) -> str:
                entry=time.monotonic_ns(); detail={'entry_ns':entry,'input_sha256':hashlib.sha256(pixels).hexdigest()}
                if mode in ('DELAYED_CHANGED','PROMPT_CHANGED'):
                    changed,_=rpc(actor,{'op':'paint','count':1024},wire);detail['paint']=changed
                if mode in ('DELAYED_UNCHANGED','DELAYED_CHANGED'): wait_until(entry+DELAY_NS)
                value=original(pixels,chunked)
                detail.update({'exit_ns':time.monotonic_ns(),'digest':value});digest.append(detail)
                return value
            legacy.pixel_digest=delayed_digest
            try: status,meta=legacy.inspect(packet,received,cid,0)
            finally: legacy.pixel_digest=original
            sampled=time.monotonic_ns(); candidate=finalize(status,meta,received,sampled)
            after=oracle(d)
            row={'case_id':cid,'mode':mode,'batch':index,'initial_paint':initial,'before':before,'after':after,
                 'packet_b64':cap['packet_b64'],'capture':cap['capture'],'transport_received_ns':transport_received,
                 'received_ns':received,'sampled_ns':sampled,'digest':digest,'legacy':status,'candidate':candidate,
                 'wire':wire,'authority':False,'model_calls':0,'input_calls':0}
            write_json(out/(mode+'.json'),row);state['cases'].append(cid)
        closing=[]; result,_=rpc(actor,{'op':'quit'},closing)
        actor.stdin.close();state['actor_exit']=actor.wait(timeout=2);state['quit_wire']=closing
        if state['actor_exit']!=0 or result!={'stopped':True}: raise RuntimeError('fixture exit mismatch')
        state['status']='COMPLETE'
    except BaseException:
        state['status']='STOP';state['exception']=traceback.format_exc();raise
    finally:
        if actor is not None:
            if actor.poll() is None:
                actor.terminate()
                try:actor.wait(timeout=2)
                except subprocess.TimeoutExpired:actor.kill();actor.wait(timeout=2)
            state['actor_exit']=actor.returncode
            if actor.stdout:actor.stdout.close()
        if d is not None:d.close()
        if xv is not None:
            xv.terminate()
            try:xv.wait(timeout=2)
            except subprocess.TimeoutExpired:xv.kill();xv.wait(timeout=2)
            state['xvfb_exit']=xv.returncode;state['xvfb_reaped']=xv.poll() is not None
            state['socket_removed']=not Path(state.get('display_socket','/nonexistent')).exists()
        for fd in (readfd,writefd):
            if fd is not None:os.close(fd)
        auth.unlink(missing_ok=True)  # Ephemeral fixture cookie, never a retained credential.
        if oldauth is None:os.environ.pop('XAUTHORITY',None)
        else:os.environ['XAUTHORITY']=oldauth
        state['ended_ns']=time.monotonic_ns();write_json(out/'batch.json',state)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--index',type=int,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--construction',action='store_true');a=p.parse_args();run(a.index,a.out.resolve(),a.construction)
