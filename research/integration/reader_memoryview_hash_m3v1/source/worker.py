import argparse, gc, importlib.util, json, os, sys, time, tracemalloc
from pathlib import Path
from common import cursor_for, sha256_path

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

p=argparse.ArgumentParser(); p.add_argument('--arm',choices=['BASELINE','MEMORYVIEW'],required=True); p.add_argument('--corpus',required=True); p.add_argument('--cursor-records',type=int,required=True); p.add_argument('--max-records',type=int,default=32); a=p.parse_args()
root=Path(__file__).resolve().parent
source=root/('baseline_reader.py' if a.arm=='BASELINE' else 'candidate_reader.py')
mod=load(source,f'reader_{a.arm.lower()}')
corpus=Path(a.corpus); data=corpus.read_bytes(); cur=cursor_for(data,a.cursor_records)
source_sha=sha256_path(source); before_sha=sha256_path(corpus)
gc.collect(); tracemalloc.start(); wall0=time.perf_counter_ns(); cpu0=time.process_time_ns()
try:
    result=mod.read_pending(corpus,stream_id='formal-stream',cursor=cur,max_records=a.max_records,max_bytes=1048576)
    error=None
except Exception as exc:
    result=None; error={'type':type(exc).__name__,'message':str(exc)}
cpu1=time.process_time_ns(); wall1=time.perf_counter_ns(); current,peak=tracemalloc.get_traced_memory(); tracemalloc.stop(); after_sha=sha256_path(corpus)
out={'schema':'reader-memoryview-resource-row-v1','arm':a.arm,'cursor_records':a.cursor_records,'max_records':a.max_records,
     'result':result,'error':error,'wall_ns':wall1-wall0,'cpu_ns':cpu1-cpu0,'traced_current_bytes':current,'traced_peak_bytes':peak,
     'source_sha256':source_sha,'input_sha256_before':before_sha,'input_sha256_after':after_sha,'pid':os.getpid(),'python':sys.version}
print(json.dumps(out,sort_keys=True,separators=(',',':')))
