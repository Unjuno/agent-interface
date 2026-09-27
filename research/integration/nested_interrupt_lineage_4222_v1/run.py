"""Finite private-X11 first-outcome runner; output directories refuse reuse."""
import argparse, hashlib, json, os, secrets, selectors, shutil, subprocess, sys, time
from pathlib import Path
from Xlib import X, XK, display
from Xlib.ext import xtest
from policy import Continuation

BASE = Path(__file__).resolve().parent
SCENARIOS = ('NORMAL','DUPLICATE_CHILD','OLD_GENERATION_CHILD','FOREIGN_SESSION','WRONG_PARENT','MISSING_CHILD')
MODES = ('COUNT_ONLY_POP','LINEAGE_BOUND_POP')
SOURCE = ('app.py','policy.py','run.py','audit.py','controls.py','PLAN.md','ENVIRONMENT.json','test_policy.py')

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p, v): Path(p).write_text(json.dumps(v, sort_keys=True, indent=2)+'\n')
def hashes(): return {p:sha(BASE/p) for p in SOURCE}

def receive(proc, timeout=5):
    sel = selectors.DefaultSelector()
    sel.register(proc.stdout, selectors.EVENT_READ)
    ready = sel.select(timeout)
    sel.close()
    if not ready: raise TimeoutError('app receipt deadline')
    line = proc.stdout.readline()
    if not line: raise RuntimeError('app exited before receipt')
    obj = json.loads(line)
    if 'error' in obj: raise RuntimeError(obj['error'])
    return obj

def case(out, rep, index, scenario, mode, number):
    out.mkdir()
    session = out.name
    env = os.environ.copy()
    env.update(DISPLAY=':'+str(number), XAUTHORITY=str(out/'Xauthority'))
    lock = Path('/tmp/.X'+str(number)+'-lock')
    sock = Path('/tmp/.X11-unix/X'+str(number))
    if lock.exists() or sock.exists(): raise RuntimeError('owned display unavailable')
    subprocess.run(['xauth','-f',env['XAUTHORITY'],'add',env['DISPLAY'],'.',secrets.token_hex(16)],
                   check=True, capture_output=True)
    log = open(out/'process.stderr', 'wb')
    row = dict(session=session, rep=rep, index=index, scenario=scenario, mode=mode,
               sources=hashes(), events=[], status='RUNNING')
    xvfb = app = connection = None
    def event(kind, **kw):
        row['events'].append(dict(kind=kind, ns=time.monotonic_ns(), **kw))
    def command(**cmd):
        app.stdin.write(json.dumps(cmd)+'\n'); app.stdin.flush()
        result = receive(app)
        event('command', request=cmd, response=result)
        return result
    def key(letter):
        code = connection.keysym_to_keycode(XK.string_to_keysym(letter))
        for typ in (X.KeyPress, X.KeyRelease):
            xtest.fake_input(connection, typ, code)
            connection.sync()
            event('key', letter=letter, code=code, edge='down' if typ==X.KeyPress else 'up')
        time.sleep(.035)
    def notify(receipt):
        result = controller.deliver(receipt)
        event('delivery', receipt=receipt, transition=result)
        if result['resume']:
            event('suffix')
            key('b')
    try:
        xvfb = subprocess.Popen(['Xvfb',env['DISPLAY'],'-screen','0','640x480x24','-nolisten','tcp','-auth',env['XAUTHORITY']],stdout=log,stderr=log)
        deadline = time.monotonic()+5
        while not sock.exists():
            if xvfb.poll() is not None or time.monotonic()>deadline: raise RuntimeError('Xvfb not ready')
            time.sleep(.01)
        # Explicit authorization object; never inherit a host display connection.
        from Xlib import xauth
        old_auth = os.environ.get('XAUTHORITY')
        os.environ['XAUTHORITY'] = env['XAUTHORITY']
        try: connection = display.Display(env['DISPLAY'])
        finally:
            if old_auth is None: os.environ.pop('XAUTHORITY',None)
            else: os.environ['XAUTHORITY']=old_auth
        app = subprocess.Popen([sys.executable,'-B',str(BASE/'app.py'),session,str(out/'app.jsonl')],
                               stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,text=True,bufsize=1,env=env)
        event('ready', response=receive(app))
        row['initial_keymap'] = list(connection.query_keymap())
        key('a')
        row['prefix'] = command(op='snapshot')
        parent = command(op='open',id='P',generation=1)
        child = command(op='open',id='C',generation=1)
        old = None
        if scenario == 'OLD_GENERATION_CHILD':
            old = command(op='close',id='C')
            child = command(op='open',id='C',generation=2)
        row['initial_stack'] = [parent, child]
        controller = Continuation(row['initial_stack'], mode)
        if old is not None: notify(old)
        current = command(op='close',id='C')
        if scenario == 'FOREIGN_SESSION': notify(dict(current,session='foreign-session'))
        if scenario == 'WRONG_PARENT': notify(dict(current,parent='OTHER:1'))
        if scenario != 'MISSING_CHILD': notify(current)
        if scenario == 'DUPLICATE_CHILD': notify(current)
        parent_done = command(op='close',id='P')
        notify(parent_done)
        row['final_stack'] = controller.stack
        row['final'] = command(op='snapshot')
        row['final_keymap'] = list(connection.query_keymap())
        row['final_buttons'] = int(connection.screen().root.query_pointer().mask) & 0x1f00
        command(op='quit')
        row['app_exit'] = app.wait(timeout=5)
        connection.close(); connection=None
        xvfb.terminate()
        row['xvfb_exit'] = xvfb.wait(timeout=5)
        row['socket_removed'] = not sock.exists() and not lock.exists()
        row['status'] = 'COMPLETE'
    except BaseException as exc:
        row['status']='STOP'; row['error']=repr(exc)
        raise
    finally:
        if connection is not None:
            connection.close()
        for name, proc in [('app',app),('xvfb',xvfb)]:
            if proc is not None and proc.poll() is None:
                proc.terminate()
                try: proc.wait(timeout=2)
                except subprocess.TimeoutExpired: proc.kill(); proc.wait(timeout=2)
                row[name+'_cleanup_exit'] = proc.returncode
        log.close()
        if (out/'app.jsonl').exists(): row['app_journal_sha256']=sha(out/'app.jsonl')
        # Never publish private X authentication cookies.
        (out/'Xauthority').unlink(missing_ok=True)
        save(out/'row.json',row)
    return row

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--rep',type=int,choices=(0,1),required=True)
    ap.add_argument('--display-base',type=int,required=True)
    ap.add_argument('--construction',action='store_true')
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    if not args.construction:
        freeze=json.loads((BASE/'FREEZE.json').read_text())
        if hashes()!=freeze['sources']: raise RuntimeError('freeze mismatch')
    receipt=dict(rep=args.rep,construction=args.construction,pid=os.getpid(),
                 start_ns=time.monotonic_ns(),cases=[],status='STARTED')
    save(args.out/'BATCH.json',receipt)
    try:
        i=0
        for scenario in SCENARIOS:
            for mode in (MODES if args.rep==0 else tuple(reversed(MODES))):
                name=f'r{args.rep}-{i:02d}-{scenario}-{mode}'
                result=case(args.out/name,args.rep,i,scenario,mode,args.display_base+i)
                receipt['cases'].append(dict(path=name,row_sha256=sha(args.out/name/'row.json')))
                save(args.out/'BATCH.json',receipt)
                i+=1
        receipt['status']='COMPLETE'
    except BaseException as exc:
        receipt['status']='STOP';receipt['error']=repr(exc)
        raise
    finally:
        receipt['end_ns']=time.monotonic_ns()
        save(args.out/'BATCH.json',receipt)
    print(json.dumps(receipt,sort_keys=True))

if __name__=='__main__': main()
