import asyncio,hashlib,json,os,socket,subprocess,sys,time
from pathlib import Path
archive,case_arg,mode=sys.argv[1:];sys.path.insert(0,archive)
from runtime.cli_v1.mcp_server import create_server
assert create_server.__module__=='runtime.cli_v1.mcp_server'
import runtime.cli_v1.mcp_guarded as guarded
assert guarded.__file__.startswith(archive+'/')
case=Path(case_arg);case.mkdir(exist_ok=False);(case/'commands').mkdir();(case/'replies').mkdir()
def write(path,row):
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(row,indent=2)+'\n');temp.rename(path)
write(case/'allocation.json',{'seed':1001068,'mode':mode,'archive_sha256':hashlib.sha256(Path(archive).read_bytes()).hexdigest(),'pid':os.getpid(),'retry_budget':0})
for number in range(26100,26200):
    if Path(f'/tmp/.X11-unix/X{number}').exists() or Path(f'/tmp/.X{number}-lock').exists():continue
    sock=socket.socket(socket.AF_UNIX)
    try:sock.connect('\0'+f'/tmp/.X11-unix/X{number}')
    except OSError:break
    finally:sock.close()
else:raise RuntimeError('no unused display')
children=[];server=None;closed=False
async def run():
    global server,closed
    from Xlib import display
    xvfb=subprocess.Popen(['Xvfb',f':{number}','-screen','0','640x480x24','-nolisten','tcp'],stdin=subprocess.DEVNULL,stdout=(case/'xvfb.stdout').open('wb'),stderr=(case/'xvfb.stderr').open('wb'));children.append(xvfb)
    for _ in range(100):
        if xvfb.poll() is not None:raise RuntimeError('Xvfb exited')
        try:d=display.Display(f':{number}');d.close();break
        except Exception:await asyncio.sleep(.02)
    else:raise RuntimeError('X11 not ready')
    app=subprocess.Popen([sys.executable,str(Path(__file__).parent/'fixture.py'),str(case),mode],env=dict(os.environ,DISPLAY=f':{number}'),stdin=subprocess.DEVNULL,stdout=(case/'app.stdout').open('wb'),stderr=(case/'app.stderr').open('wb'));children.append(app)
    for _ in range(100):
        if app.poll() is not None:raise RuntimeError('app exited')
        if (case/'ready.json').exists():break
        await asyncio.sleep(.02)
    else:raise RuntimeError('app not ready')
    window=json.loads((case/'ready.json').read_text())['window']
    server=create_server({'app':window},case/'calls',display_name=f':{number}',session_mode='guarded-x11')
    write(case/'owner.json',{'pid':os.getpid(),'children':[p.pid for p in children],'window':window,'display':f':{number}'})
    print('READY '+mode,flush=True)
    for index in range(1,20):
        path=case/'commands'/f'{index:03d}.json'
        while not path.exists():
            if any(p.poll() is not None for p in children):raise RuntimeError('owned child exited')
            await asyncio.sleep(.02)
        request=json.loads(path.read_text());started=time.monotonic_ns()
        response=await server.call_tool(request['tool'],request.get('args',{}))
        meta=json.loads(response.content[0].text)
        image=None
        for part in response.content:
            if part.type=='image':
                import base64
                image=case/f'primary-{index:03d}.png';image.write_bytes(base64.b64decode(part.data))
        write(case/'replies'/path.name,{'request':request,'started_ns':started,'ended_ns':time.monotonic_ns(),'isError':response.isError,'metadata':meta,'image_path':str(image) if image else None,'image_sha256':hashlib.sha256(image.read_bytes()).hexdigest() if image else None})
        print('REPLY '+str(index),flush=True)
        if request['tool']=='interface_close':closed=True;return
    raise RuntimeError('case call limit')
try:asyncio.run(run())
except Exception as e:write(case/'exception.json',{'error':repr(e),'replay_allowed':False});raise
finally:
    codes=[]
    for p in reversed(children):
        if p.poll() is None:p.terminate()
        try:codes.append(p.wait(timeout=5))
        except subprocess.TimeoutExpired:p.kill();codes.append(p.wait(timeout=5))
    write(case/'cleanup.json',{'closed':closed,'child_exit_codes':codes,'ended_ns':time.monotonic_ns()})
    print('TERMINAL',flush=True)
