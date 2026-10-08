"""One allocation per fixed case; command files and every reply remain retained."""
import argparse, copy, hashlib, json, os, socket, subprocess, sys, time
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument('--archive',required=True); p.add_argument('--case',required=True); p.add_argument('--variant',choices=['positive','changed'],required=True); p.add_argument('--route',choices=['form','compiled'],required=True); args=p.parse_args()
sys.path.insert(0,args.archive)
from runtime.guarded_x11_v1.bridge import NativeHandleBridge
from runtime.guarded_x11_v1 import compiled
if not compiled.__file__.startswith(args.archive+'/'): raise RuntimeError('must use frozen archive')
case=Path(args.case); case.mkdir(exist_ok=False); (case/'commands').mkdir(); (case/'replies').mkdir()
token='t1001067-'+args.variant
here=Path(__file__).resolve().parent
(case/'allocation.json').write_text(json.dumps({'variant':args.variant,'route':args.route,'token':token,'archive':args.archive,'archive_sha256':hashlib.sha256(Path(args.archive).read_bytes()).hexdigest(),'keeper_pid':os.getpid(),'model_grounding':'primary image review; no secondary model','retry_budget':0},indent=2)+'\n')
def write(path,row): path.write_text(json.dumps(row,indent=2)+'\n')
number=None
for candidate in range(170,220):
    if Path(f'/tmp/.X11-unix/X{candidate}').exists(): continue
    s=socket.socket(socket.AF_UNIX)
    try: s.connect('\0'+f'/tmp/.X11-unix/X{candidate}')
    except OSError: number=candidate; break
    finally: s.close()
if number is None: raise RuntimeError('no unallocated display')
processes=[]; bridge=None; exit_codes=[]; status='starting'
try:
    xvfb=subprocess.Popen(['Xvfb',f':{number}','-screen','0','640x480x24','-nolisten','tcp'],stdout=(case/'xvfb.stdout').open('wb'),stderr=(case/'xvfb.stderr').open('wb')); processes.append(xvfb)
    from Xlib import display
    for _ in range(100):
        if xvfb.poll() is not None: raise RuntimeError('Xvfb exited')
        try: d=display.Display(f':{number}'); d.close(); break
        except Exception: time.sleep(.02)
    else: raise RuntimeError('Xvfb readiness timeout')
    app=subprocess.Popen([sys.executable,str(here/'fixture.py'),str(case),token,args.variant],env=dict(os.environ,DISPLAY=f':{number}'),stdout=(case/'app.stdout').open('wb'),stderr=(case/'app.stderr').open('wb')); processes.append(app)
    for _ in range(100):
        if app.poll() is not None: raise RuntimeError('fixture exited')
        if (case/'ready.json').exists(): break
        time.sleep(.02)
    else: raise RuntimeError('fixture readiness timeout')
    window=json.loads((case/'ready.json').read_text())['window']
    bridge=NativeHandleBridge(f':{number}',{'app':window},'app',case/'bridge')
    write(case/'owner.json',{'pid':os.getpid(),'children':[p.pid for p in processes],'display':f':{number}','window':window})
    print('READY '+str(case),flush=True); status='ready'; refs={}; source=None; image=None; index=1
    while True:
        if any(child.poll() is not None for child in processes): raise RuntimeError('owned child exited')
        command_file=case/'commands'/f'{index:03d}.json'
        if not command_file.exists(): time.sleep(.02); continue
        request=json.loads(command_file.read_text()); started=time.monotonic_ns(); op=request['op']
        if op=='observe':
            source=bridge.observe(); image=bridge.history[source['sequence']][1].copy(); reply={'sequence':source['sequence'],'image_path':source['native']['artifact']['path'],'image_sha256':source['native']['artifact']['sha256'],'full_observation_ref':'observation-'+str(source['sequence'])}
        elif op=='mint':
            if source is None: raise RuntimeError('review source required')
            if request['alias'] not in ('field','save'): raise ValueError('only authored fixture aliases')
            point=request['point']; ref=bridge.mint_reference(request['alias'],source['sequence'],point,region_size=(24,24)); refs[request['alias']]={'offset':ref['offset'],'box':(point[0]-12,point[1]-12,point[0]+12,point[1]+12),'pixels':image.crop((point[0]-12,point[1]-12,point[0]+12,point[1]+12)).tobytes()}; reply=ref
        elif op=='run':
            if set(refs)!=set(('field','save')): raise RuntimeError('both primary-grounded references required')
            sys.path.insert(0,str(here))
            from methods import run
            reply=run(bridge,refs,token,args.route)
        elif op=='close':
            reply={'status':'closing','input_replayed':False}; write(case/'replies'/f'{index:03d}.json',{'request':request,'started_ns':started,'ended_ns':time.monotonic_ns(),'reply':reply}); status='closed'; break
        else: raise ValueError('unsupported command')
        write(case/'replies'/f'{index:03d}.json',{'request':request,'started_ns':started,'ended_ns':time.monotonic_ns(),'reply':reply}); print('REPLY '+str(index)+' '+op,flush=True); index+=1
except Exception as error:
    status='failed'; write(case/'exception.json',{'error':repr(error),'input_replayed':False}); raise
finally:
    if bridge is not None: bridge.close()
    for child in reversed(processes):
        if child.poll() is None: child.terminate()
        try: exit_codes.append(child.wait(timeout=5))
        except subprocess.TimeoutExpired: child.kill(); exit_codes.append(child.wait(timeout=5))
    write(case/'cleanup.json',{'status':status,'child_exit_codes':exit_codes,'ended_ns':time.monotonic_ns()}); print('TERMINAL '+status,flush=True)
