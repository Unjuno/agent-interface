"""One finite diagnostic block, no science replay or timing censoring."""
import argparse
import hashlib
import json
import os
import platform
import select
import subprocess
import sys
import time
import traceback
from pathlib import Path
from common import await_file,write
from validation import validate_cell
from decision import contrast

HERE=Path(__file__).resolve().parent

def read_display(p,fd,seconds=3):
    deadline=time.monotonic()+seconds; raw=b''
    while time.monotonic()<deadline:
        if p.poll() is not None: raise RuntimeError('display owner exited before readiness')
        if select.select([fd],[],[],min(.02,max(0,deadline-time.monotonic())))[0]:
            chunk=os.read(fd,128)
            if not chunk: raise RuntimeError('display descriptor closed before readiness')
            raw+=chunk
            if len(raw)>128: raise RuntimeError('oversize display descriptor')
            if raw.endswith(b'\n'):
                value=raw[:-1]
                if not value.isdigit() or int(value)>65535: raise RuntimeError('invalid display descriptor')
                if p.poll() is not None: raise RuntimeError('display owner not live')
                return ':'+str(int(value))
    raise RuntimeError('bounded display descriptor timeout')

def load(path): return json.loads(Path(path).read_text())
def terminal(p):
    if p.poll() is None: p.terminate()
    try: return p.wait(timeout=3)
    except subprocess.TimeoutExpired:
        p.kill(); return p.wait(timeout=3)

def cell_data(root):
    data={n:load(root/(n+'.json')) for n in ('source','capture')}
    data['lifecycle']=load(root/'cell.json')['lifecycle']
    for key,name in [('epoch','epoch.json'),('fixture_ready','fixture-ready.json'),
                     ('observer_ready','observer-ready.json'),('display_ready','display-ready.json')]:
        data[key]=load(root/name)
    for key,name in [('source_journal','source.jsonl'),('source_waits','source-waits.jsonl'),
                     ('frames','frames.jsonl'),('observer_waits','waits.jsonl')]:
        data[key]=[json.loads(line) for line in (root/name).read_text().splitlines()]
    return data

def run_cell(spec,root):
    root.mkdir(); write(root/'spec.json',spec)
    children={}; handles=[]; commands={}; error=None; server_live=False; shutdown=None
    def spawn(name,args,**kwargs):
        out=(root/(name+'.stdout.log')).open('xb'); err=(root/(name+'.stderr.log')).open('xb')
        handles.extend([out,err]); commands[name]=args
        p=subprocess.Popen(args,stdout=out,stderr=err,**kwargs); children[name]=p; return p
    try:
        read_fd,write_fd=os.pipe()
        try:
            xv=spawn('xvfb',['Xvfb','-displayfd',str(write_fd),'-screen','0','64x64x24','-nolisten','tcp','-noreset','-ac'],pass_fds=(write_fd,))
            os.close(write_fd); write_fd=None
            display=read_display(xv,read_fd)
        finally:
            os.close(read_fd)
            if write_fd is not None: os.close(write_fd)
        write(root/'display-ready.json',{'pid':xv.pid,'display':display,'transport':'child-owned-displayfd'})
        fx=spawn('fixture',[sys.executable,'-B',str(HERE/'fixture.py'),'--display',display,
                            '--cell',str(root/'spec.json'),'--out',str(root)])
        ready=await_file(root/'fixture-ready.json')
        ob=spawn('observer',[sys.executable,'-B',str(HERE/'observer.py'),'--display',display,
                            '--window',str(ready['window']),'--offsets',json.dumps(spec['offsets']),
                            '--out',str(root),'--epoch-file',str(root/'epoch.json')])
        await_file(root/'observer-ready.json')
        write(root/'epoch.json',{'epoch_ns':time.monotonic_ns()+200_000_000})
        if ob.wait(timeout=4)!=0 or fx.wait(timeout=4)!=0: raise RuntimeError('native child failure')
        if xv.poll() is not None: raise RuntimeError('private server ended before planned shutdown')
    except Exception: error=traceback.format_exc()
    finally:
        server_live='xvfb' in children and children['xvfb'].poll() is None
        shutdown='SIGTERM' if server_live else None
        exits={n:terminal(p) for n,p in children.items()}
        for h in handles: h.close()
    life={n+'_pid':p.pid for n,p in children.items()}; life.update({n+'_exit':v for n,v in exits.items()})
    life.update(xvfb_running_before_cleanup=server_live,xvfb_shutdown_requested=shutdown)
    hashes={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(root.iterdir()) if f.is_file()}
    write(root/'cell.json',{'spec':spec,'lifecycle':life,'commands':commands,'files_sha256':hashes,'error':error})
    if error is not None: raise RuntimeError(error)
    return validate_cell(spec,cell_data(root))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--freeze',type=Path,required=True); a=ap.parse_args(); freeze=load(a.freeze)
    hashes={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in freeze['source_sha256']}
    if hashes!=freeze['source_sha256']: raise ValueError('source freeze mismatch')
    cgroups={n:Path('/sys/fs/cgroup',n).read_text().strip()
             for n in ('cpu.max','memory.max','memory.swap.max','pids.max')}
    if cgroups!={'cpu.max':'100000 100000','memory.max':'536870912','memory.swap.max':'0','pids.max':'64'}:
        raise ValueError('actual cgroup limits differ')
    plan=load(HERE/'plan.json')
    if plan!=freeze['cases']: raise ValueError('published cases mismatch')
    a.out.mkdir(exist_ok=False); (a.out/'cells').mkdir()
    write(a.out/'consumed.json',{'allocation':freeze['allocation'],'pid':os.getpid(),'started_ns':time.monotonic_ns()})
    summary={'allocation':freeze['allocation'],'status':'STOP_COLLECTION','source_sha256':hashes,
             'cgroups':cgroups,'started_cells':[],'cells':[],'metrics':[],
             'python':sys.version,'platform':platform.platform(),'input_events':0,'model_calls':0}
    try:
        for spec in plan:
            summary['started_cells'].append(spec['id']); metric=run_cell(spec,a.out/'cells'/spec['id'])
            summary['cells'].append(spec['id']); summary['metrics'].append(metric)
            print(json.dumps({'completed':len(summary['cells']),'planned':len(plan),'cell':spec['id']}),flush=True)
        summary['decision']=contrast([m for m in summary['metrics'] if m['kind']=='pulse'])
        summary['status']='COMPLETE_DIAGNOSTIC'
    except Exception: summary['reason']=traceback.format_exc()
    summary['finished_ns']=time.monotonic_ns(); write(a.out/'raw.json',summary)
    if summary['status']!='COMPLETE_DIAGNOSTIC': raise SystemExit(2)

if __name__=='__main__': main()
