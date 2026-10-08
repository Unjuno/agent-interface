from __future__ import annotations
import argparse,json,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
def cmd(args): return subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=8)
def main():
    p=argparse.ArgumentParser(); p.add_argument('--container',required=True); p.add_argument('--out',type=Path,required=True); p.add_argument('--stop-file',type=Path,required=True); p.add_argument('--interval',type=float,default=.2); a=p.parse_args()
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open('a',encoding='utf-8',newline='\n') as f:
        while not a.stop_file.exists():
            ns=time.time_ns(); smi=cmd(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits']); ps=cmd(['docker','exec',a.container,'ollama','ps'])
            try: used,util=[int(x.strip()) for x in smi.stdout.strip().splitlines()[0].split(',')]
            except Exception: used=util=None
            f.write(json.dumps({'utc_ns':ns,'utc':datetime.fromtimestamp(ns/1e9,tz=timezone.utc).isoformat(),'memory_used_mib':used,'gpu_utilization_percent':util,
                'nvidia_smi_exit':smi.returncode,'nvidia_smi_stdout':smi.stdout,'ollama_ps_exit':ps.returncode,'ollama_ps_stdout':ps.stdout,'ollama_ps_stderr':ps.stderr},sort_keys=True)+'\n'); f.flush(); time.sleep(a.interval)
if __name__=='__main__': main()
