"""Measure retained preparation allocations at fixed input-byte budget.

Input creation, imports, raw serialization and query allocations are outside the
trace window. This does not measure RSS, total memory or live producer behavior.
"""
import argparse,gc,hashlib,json,os,sys,tracemalloc
from pathlib import Path
from eager_snapshot import FrozenSnapshot


def enc(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()+b'\n'
def corpus(count,total):
    width=total//count
    if total%count:raise ValueError('nonintegral record width')
    out=[]
    for i in range(1,count+1):
        b=enc({'event':'notification','delivery_id':f'delivery:{i}','value':f'item-{i:06d}'})
        if len(b)>width:raise ValueError('record cannot fit')
        out.append(b[:-1]+b' '*(width-len(b))+b'\n')
    return b''.join(out)

def run(count,total,rep,folder):
    folder.mkdir(parents=True,exist_ok=False)
    data=corpus(count,total);(folder/'input.jsonl').write_bytes(data)
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
    if tracemalloc.is_tracing():raise RuntimeError('PREEXISTING_TRACER')
    gc.collect()
    tracemalloc.start(1)
    snapshot=FrozenSnapshot.prepare(data,stream_id='density-c5d2',max_bytes=total)
    gc.collect()
    allocation_snapshot=tracemalloc.take_snapshot()
    tracemalloc.stop()
    # Each trace is retained, not merely the worker's sum. CPython tracer's
    # internal storage and preexisting data bytes are outside this measurement.
    traces=[]
    for t in allocation_snapshot.traces:
        frame=t.traceback[0]
        path=Path(frame.filename)
        filename=path.name if path.parent==Path(__file__).resolve().parent else frame.filename
        traces.append({'size':t.size,'domain':t.domain,'filename':filename,'line':frame.lineno})
    traces.sort(key=lambda x:(x['filename'],x['line'],x['domain'],x['size']))
    response=snapshot.read(max_records=32)
    rows=[{'offset':o,'sequence':v[0],'sha256':v[1]} for o,v in snapshot.prefixes.items()]
    trace_bytes=sum(t['size'] for t in traces)
    candidate_bytes=sum(t['size'] for t in traces if t['filename']=='eager_snapshot.py')
    obj={'schema':'snapshot-index-density-c5d2-v1','n':count,'total_bytes':total,'rep':rep,'pid':os.getpid(),
         'affinity':sorted(os.sched_getaffinity(0)),'input_sha256':hashlib.sha256(data).hexdigest(),
         'input_is_reused_object':snapshot.data is data,'input_unchanged':(folder/'input.jsonl').read_bytes()==data,
         'traceback_limit':1,'traces':traces,'trace_bytes':trace_bytes,'eager_source_trace_bytes':candidate_bytes,
         'prefix_entries':rows,'response':response,'metadata':snapshot.metadata(),
         'trace_scope':'live Python blocks allocated after start through post-prepare GC; excludes preexisting input/query/RSS/tracer storage'}
    sys.stdout.buffer.write(enc(obj))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('n',type=int);a.add_argument('total',type=int);a.add_argument('rep',type=int);a.add_argument('out',type=Path);o=a.parse_args();run(o.n,o.total,o.rep,o.out)
