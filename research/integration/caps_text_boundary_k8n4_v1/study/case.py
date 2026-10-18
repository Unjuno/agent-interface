"""One exclusively named private-X11 public-dispatch case; no retries."""
import argparse, hashlib, json, os, select, socket, struct, subprocess, sys, time, traceback
from pathlib import Path

def dump(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True)+'\n', encoding='utf-8')
def line(process, timeout=8):
    if not select.select([process.stdout], [], [], timeout)[0]:
        raise TimeoutError('fixture response timeout')
    result=process.stdout.readline()
    if not result: raise RuntimeError('fixture EOF')
    return result

def main():
    p=argparse.ArgumentParser(); p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True); p.add_argument('--condition',required=True)
    p.add_argument('--arm',required=True); p.add_argument('--session',required=True)
    a=p.parse_args(); a.out.mkdir(parents=True,exist_ok=False)
    source=a.source.resolve(); sys.path.insert(0,str(source))
    from Xlib import X, XK, display
    from Xlib.ext import xtest
    from runtime.cli_v1.api import dispatch
    record={'session':a.session,'condition':a.condition,'arm':a.arm,'driver_pid':os.getpid(),
            'started_ns':time.monotonic_ns(),'source_root':str(source),'ipc':[], 'errors':[]}
    xv=None; app=None; witness=None; auth=a.out/'private.Xauthority'
    handles=[]
    try:
        # Do not connect to any existing display. Xvfb also refuses collisions.
        unix=Path('/proc/net/unix').read_text()
        number=next(n for n in range(2200,2800) if not Path(f'/tmp/.X{n}-lock').exists()
                    and not Path(f'/tmp/.X11-unix/X{n}').exists()
                    and f'/tmp/.X11-unix/X{n}\n' not in unix)
        display_name=f':{number}'
        def field(b): return struct.pack('!H',len(b))+b
        auth.write_bytes(struct.pack('!H',256)+field(socket.gethostname().encode())+field(str(number).encode())+
                         field(b'MIT-MAGIC-COOKIE-1')+field(os.urandom(16)))
        auth.chmod(0o600)
        env=dict(os.environ, DISPLAY=display_name, XAUTHORITY=str(auth.resolve()), PYTHONDONTWRITEBYTECODE='1')
        os.environ.update(DISPLAY=display_name, XAUTHORITY=str(auth.resolve()))
        for k in ('WAYLAND_DISPLAY',): os.environ.pop(k,None); env.pop(k,None)
        xout=(a.out/'xvfb.stdout').open('x'); xerr=(a.out/'xvfb.stderr').open('x'); handles += [xout,xerr]
        argv=['Xvfb',display_name,'-screen','0','640x360x24','-nolisten','tcp','-auth',str(auth.resolve()),'-noreset']
        xv=subprocess.Popen(argv,stdout=xout,stderr=xerr,env=env)
        record['xvfb']={'pid':xv.pid,'argv':argv,'display':display_name}
        end=time.monotonic()+8
        while not Path(f'/tmp/.X11-unix/X{number}').exists():
            if xv.poll() is not None or time.monotonic()>end: raise RuntimeError('Xvfb startup failed')
            time.sleep(.01)
        witness=display.Display(display_name); wr=witness.screen().root
        def snapshot():
            start=time.monotonic_ns(); keys=list(witness.query_keymap()); pointer=wr.query_pointer()
            return {'started_ns':start,'ended_ns':time.monotonic_ns(),'keymap':keys,
                    'mask':pointer.mask,'lock':bool(pointer.mask & X.LockMask),
                    'focus':getattr(witness.get_input_focus().focus,'id',witness.get_input_focus().focus)}
        record['server_initial']=snapshot()
        if record['server_initial']['lock']: raise RuntimeError('fresh server unexpectedly locked')
        initial_on=a.condition in ('INITIAL_ON','PROGRAM_OFF','ON_DIGITS')
        if initial_on:
            code=witness.keysym_to_keycode(XK.string_to_keysym('Caps_Lock'))
            xtest.fake_input(witness,X.KeyPress,code); xtest.fake_input(witness,X.KeyRelease,code); witness.sync()
        record['fixture_setup_emissions']=2 if initial_on else 0
        record['before_app']=snapshot()
        if record['before_app']['lock'] != initial_on: raise RuntimeError('initial lock setup mismatch')
        app_err=(a.out/'app.stderr').open('x'); handles.append(app_err)
        app_argv=[sys.executable,'-B',str(Path(__file__).with_name('app.py')),str(a.out/'app.jsonl')]
        app=subprocess.Popen(app_argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=app_err,env=env,text=True,bufsize=1)
        ready_raw=line(app); record['ipc'].append({'direction':'from_app','raw':ready_raw})
        ready=json.loads(ready_raw);record['app']={'pid':app.pid,'argv':app_argv,'ready':ready}
        def request(cmd):
            raw=json.dumps({'command':cmd})+'\n'; record['ipc'].append({'direction':'to_app','raw':raw})
            app.stdin.write(raw);app.stdin.flush(); response=line(app)
            record['ipc'].append({'direction':'from_app','raw':response});return json.loads(response)
        record['before']=snapshot();record['app_before']=request('snapshot')
        ops=[{'op':'focus','target':'entry'}]
        caps={'op':'key_chord','keys':['Caps_Lock']}
        if a.condition=='PROGRAM_ON': ops += [{'op':'text','text':'1'},caps]
        elif a.condition=='PROGRAM_OFF': ops += [caps]
        elif a.condition=='PROGRAM_ROUNDTRIP': ops += [caps,caps]
        ops += [{'op':'text','text':'12' if a.condition=='ON_DIGITS' else 'aB2'}, {'op':'release_all'}]
        program={'schema':'agent-interface/program-v1','program_id':a.session,
                 'source':{'observation_seq':1,'binding_revision':1},
                 'authority':{'lease_id':'fixture-only','expires_at_ns':time.monotonic_ns()+30_000_000_000},
                 'terminal':{'release_all_required':True},'ops':ops}
        dump(a.out/'program.json',program)
        record['dispatch_started_ns']=time.monotonic_ns()
        result=dispatch(program,{'entry':ready['window']},current_observation_seq=1,
                        current_binding_revision=1,display_name=display_name)
        record['dispatch_ended_ns']=time.monotonic_ns();record['response']=result
        dump(a.out/'response.json',result)
        witness.sync(); record['after']=snapshot(); record['app_after']=request('snapshot')
        record['app_close']=request('close');app.wait(timeout=8);record['app']['exit']=app.returncode
        record['terminal']=snapshot()
    except Exception:
        record['errors'].append(traceback.format_exc())
    finally:
        if app is not None:
            if app.poll() is None:
                app.terminate()
                try: app.wait(timeout=4)
                except subprocess.TimeoutExpired: app.kill();app.wait()
                record.setdefault('app',{})['forced_cleanup']=True
            record.setdefault('app',{})['exit']=app.returncode
        if witness is not None: witness.close()
        if xv is not None:
            if xv.poll() is None: xv.terminate()
            try: xv.wait(timeout=4)
            except subprocess.TimeoutExpired: xv.kill();xv.wait()
            record['xvfb'].update(exit=xv.returncode,termination_requested=True)
            record['display_socket_removed']=not Path(f'/tmp/.X11-unix/X{number}').exists()
        for f in handles: f.close()
        if auth.exists(): auth.unlink() # Never publish even an expired fixture credential.
        record['runtime_imports']={}
        for name,module in list(sys.modules.items()):
            f=getattr(module,'__file__',None)
            if name.startswith('runtime') and f and Path(f).is_file():
                record['runtime_imports'][name]={'path':str(Path(f).relative_to(source)),
                    'sha256':hashlib.sha256(Path(f).read_bytes()).hexdigest()}
        record['ended_ns']=time.monotonic_ns();dump(a.out/'record.json',record)
    print(json.dumps({'session':a.session,'errors':record['errors'],
                     'value':record.get('app_after',{}).get('value'),
                     'status':record.get('response',{}).get('result',{}).get('status')}))
    return 1 if record['errors'] else 0
if __name__=='__main__': raise SystemExit(main())
