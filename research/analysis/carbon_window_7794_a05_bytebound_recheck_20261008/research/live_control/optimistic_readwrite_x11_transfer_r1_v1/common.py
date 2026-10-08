from __future__ import annotations
import json, os, socket, subprocess, tempfile, time
from pathlib import Path
from Xlib import X, Xatom, display

WIDTH=900; HEIGHT=600
LOCAL_ATOM='_AI_LOCAL_GEN'
EFFECT_ATOM='_AI_EFFECT'
GLOBAL_ATOM='_AI_GLOBAL_GEN'
BUTTON_MASK=X.Button1Mask|X.Button2Mask|X.Button3Mask|X.Button4Mask|X.Button5Mask

PARALLEL='PARALLEL'; SERIALIZE='SERIALIZE'; REVALIDATE='REVALIDATE'

def candidate(ra:set[str],wa:set[str],rb:set[str],wb:set[str],changed:set[str])->str:
    if (ra|rb)&changed: return REVALIDATE
    if wa&wb or wa&rb or wb&ra: return SERIALIZE
    return PARALLEL

def pick_display(start=120,end=160):
    sock=Path('/tmp/.X11-unix')
    for n in range(start,end):
        if not (sock/f'X{n}').exists(): return n
    raise RuntimeError('no free display')

def start_xvfb(work:Path):
    auth=work/'empty.Xauthority'; auth.write_bytes(b'')
    n=pick_display(); name=f':{n}'
    os.environ['DISPLAY']=name; os.environ['XAUTHORITY']=str(auth)
    env=os.environ.copy(); env['DISPLAY']=name; env['XAUTHORITY']=str(auth)
    p=subprocess.Popen(['Xvfb',name,'-screen','0',f'{WIDTH}x{HEIGHT}x24','-nolisten','tcp'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
    deadline=time.time()+4; last=None
    while time.time()<deadline:
        if p.poll() is not None: raise RuntimeError('Xvfb exited: '+(p.stderr.read() if p.stderr else ''))
        try:
            d=display.Display(name); d.close(); return p,name,env
        except Exception as e:
            last=e; time.sleep(.03)
    p.terminate(); p.wait(timeout=2); raise RuntimeError(f'Xvfb readiness {last!r}')

def stop_proc(p):
    if p is None or p.poll() is not None: return
    p.terminate()
    try:p.wait(timeout=2)
    except subprocess.TimeoutExpired:
        p.kill();p.wait(timeout=2)

def wait_json(path:Path,timeout=4):
    deadline=time.time()+timeout
    while time.time()<deadline:
        if path.exists():
            return json.loads(path.read_text())
        time.sleep(.02)
    raise TimeoutError(path)

def send_cmd(sock_path:str, cmd:dict, timeout=4):
    s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM); s.settimeout(timeout); s.connect(sock_path)
    s.sendall((json.dumps(cmd,sort_keys=True)+'\n').encode())
    buf=b''
    while b'\n' not in buf:
        part=s.recv(65536)
        if not part: break
        buf+=part
    s.close()
    if not buf: raise RuntimeError('empty worker response')
    return json.loads(buf.split(b'\n',1)[0])

def set_cardinal(d,win,atom_name,value):
    atom=d.intern_atom(atom_name); win.change_property(atom,Xatom.CARDINAL,32,[int(value)]); d.sync()

def get_cardinal(d,win,atom_name):
    atom=d.intern_atom(atom_name); p=win.get_full_property(atom,Xatom.CARDINAL)
    if p is None or len(p.value)<1: raise RuntimeError(f'missing {atom_name}')
    return int(p.value[0])

def get_effect(d,win):
    atom=d.intern_atom(EFFECT_ATOM); p=win.get_full_property(atom,Xatom.STRING)
    if p is None: raise RuntimeError('missing effect')
    v=p.value
    if isinstance(v,str): return v
    if isinstance(v,bytes): return v.decode()
    return bytes(v).decode()

def read_receipts(d,a_win,b_win):
    root=d.screen().root
    return {
      'A_LOCAL':get_cardinal(d,a_win,LOCAL_ATOM),
      'B_LOCAL':get_cardinal(d,b_win,LOCAL_ATOM),
      'GLOBAL':get_cardinal(d,root,GLOBAL_ATOM),
    }
