"""Actual private process-lifetime probes. No Xlib/native input/runtime dispatch."""
import json,os,subprocess,sys,time
from pathlib import Path
from death_gate import observe_dead
def state(pid):
    try:
        t=Path("/proc",str(pid),"stat").read_text().rsplit(") ",1)[1].split()
        return t[0],int(t[19])
    except FileNotFoundError:return "missing",None
rows=[]
for mode in ("early_close","normal_exit","sigkill"):
    r,w=os.pipe()
    code="import os,sys,time; f=int(sys.argv[1]); print('READY',flush=True); "
    code+=("os.close(f); time.sleep(.04)"if mode=="early_close"else"time.sleep(.02)"if mode=="normal_exit"else"time.sleep(3)")
    p=subprocess.Popen([sys.executable,"-B","-c",code,str(w)],stdout=subprocess.PIPE,pass_fds=(w,))
    os.close(w);assert p.stdout.readline()==b"READY\n";ticks=state(p.pid)[1]
    if mode=="sigkill":p.kill()
    assert os.read(r,1)==b"";eof=time.monotonic_ns();initial=state(p.pid)
    result=observe_dead(ticks,lambda:state(p.pid),time.monotonic_ns,lambda ns:time.sleep(ns/1e9),250000000,2000000)
    rc=p.wait(timeout=1);os.close(r)
    assert rc==(-9 if mode=="sigkill"else 0)
    if mode=="early_close":assert initial[0]not in("Z","missing") and result["at_ns"]-eof>=10000000
    rows.append({"mode":mode,"pid":p.pid,"ticks":ticks,"eof_ns":eof,"initial":initial,"death":result,"returncode":rc,"task_input_emissions":0})
print(json.dumps({"process_probes":rows,"scientific_cells_started":0}))
