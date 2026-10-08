import hashlib,json,os,socket,subprocess,sys,time
from pathlib import Path
archive_arg,bundle_arg,case_arg,mode=sys.argv[1:]
archive=Path(archive_arg).resolve();bundle=Path(bundle_arg).resolve();case=Path(case_arg).resolve();case.mkdir(exist_ok=False);(case/'commands').mkdir();(case/'replies').mkdir()
def write(path,row):path.write_text(json.dumps(row,indent=2)+'\n')
write(case/'allocation.json',{'seed':1001074,'mode':mode,'pid':os.getpid(),'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'host_manifest_sha256':hashlib.sha256((bundle/'HOST_MANIFEST.json').read_bytes()).hexdigest(),'retry_budget':0})
for number in range(26800,26900):
    if Path(f'/tmp/.X11-unix/X{number}').exists() or Path(f'/tmp/.X{number}-lock').exists():continue
    sock=socket.socket(socket.AF_UNIX)
    try:sock.connect('\0'+f'/tmp/.X11-unix/X{number}')
    except OSError:break
    finally:sock.close()
else:raise RuntimeError('no unused X11 display')
children=[];terminal=None
try:
    from Xlib import display
    xvfb=subprocess.Popen(['Xvfb',f':{number}','-screen','0','640x480x24','-nolisten','tcp'],stdin=subprocess.DEVNULL,stdout=(case/'xvfb.stdout').open('wb'),stderr=(case/'xvfb.stderr').open('wb'));children.append(xvfb)
    for _ in range(100):
        if xvfb.poll() is not None:raise RuntimeError('Xvfb exited')
        try:d=display.Display(f':{number}');d.close();break
        except Exception:time.sleep(.02)
    else:raise RuntimeError('X11 not ready')
    app=subprocess.Popen([sys.executable,str(Path(__file__).parent/'fixture.py'),str(case),mode],env=dict(os.environ,DISPLAY=f':{number}'),stdin=subprocess.DEVNULL,stdout=(case/'app.stdout').open('wb'),stderr=(case/'app.stderr').open('wb'));children.append(app)
    for _ in range(100):
        if app.poll() is not None:raise RuntimeError('app exited')
        if (case/'ready.json').exists():break
        time.sleep(.02)
    else:raise RuntimeError('app not ready')
    window=json.loads((case/'ready.json').read_text())['window'];write(case/'targets.json',{'app':window})
    node=subprocess.Popen(['/home/taka/.volta/bin/node',str(Path(__file__).parent/'host-keeper.mjs'),str(case),str(archive),str(bundle),f':{number}',str(case/'targets.json')]);children.append(node)
    write(case/'owner.json',{'pid':os.getpid(),'children':[p.pid for p in children],'display':f':{number}','window':window})
    terminal=node.wait()
    if terminal!=0:raise RuntimeError('host keeper failed '+str(terminal))
except Exception as e:write(case/'exception.json',{'error':repr(e),'replay_allowed':False});raise
finally:
    codes=[]
    for p in reversed(children):
        if p.poll() is None:p.terminate()
        try:codes.append(p.wait(timeout=5))
        except subprocess.TimeoutExpired:p.kill();codes.append(p.wait(timeout=5))
    write(case/'cleanup.json',{'host_exit':terminal,'child_exit_codes':codes,'ended_ns':time.monotonic_ns()});print('TERMINAL OWNER',flush=True)
