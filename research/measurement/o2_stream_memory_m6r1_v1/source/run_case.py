"""One consumed condition; all warmup, timing and traced-memory outputs retained."""
from pathlib import Path
import gc
import hashlib
import json
import os
import resource
import sys
import time
import tracemalloc
import zlib
from stream_encoder import Encoder, StreamingEncoder, Frame

ROOT=Path(__file__).resolve().parents[1]
def sha(data):return hashlib.sha256(data).hexdigest()
def save(path,obj):path.write_text(json.dumps(obj,sort_keys=True,indent=2)+'\n')

def main(index):
    freeze=json.loads((ROOT/'FREEZE.json').read_text())
    for p,digest in freeze['files'].items():
        if sha((ROOT/p).read_bytes())!=digest:raise RuntimeError('source/input mismatch: '+p)
    env=json.loads((ROOT/'ENVIRONMENT.json').read_text())
    os.sched_setaffinity(0,{env['chosen_cpu']})
    spec=json.loads((ROOT/'SCHEDULE.json').read_text())[index]
    out=ROOT/'formal'/f'{index:02d}'
    out.mkdir(parents=True,exist_ok=False)
    raw=dict(index=index,spec=spec,pid=os.getpid(),argv=sys.argv,affinity=sorted(os.sched_getaffinity(0)),
             freeze_sha256=sha((ROOT/'FREEZE.json').read_bytes()),samples=[],status='STARTED',
             perf_clock=time.get_clock_info('perf_counter')._asdict() if hasattr(time.get_clock_info('perf_counter'),'_asdict') else str(time.get_clock_info('perf_counter')))
    save(out/'record.json',raw)
    images=[]
    for key in ('before','after'):
        b=zlib.decompress((ROOT/spec[key]['path']).read_bytes())
        if sha(b)!=spec[key]['sha256'] or len(b)!=spec[key]['bytes']:raise RuntimeError('bad input')
        images.append(Frame(spec['width'],spec['height'],spec['mode'],b))
    kw=spec['metadata'].copy();stream=kw.pop('stream')
    arms={'canonical':Encoder,'streaming':StreamingEncoder}
    reference={}
    for phase,count in [('warmup',2),('timing',11),('memory',3)]:
        for pair in range(count):
            order=['canonical','streaming'] if (index+pair)%2==0 else ['streaming','canonical']
            for arm in order:
                enc=arms[arm](stream,'O2',64)
                initial=enc.encode(images[0],action_id='initial',observed_ns=1,context=kw['context'])
                if arm not in reference:
                    (out/(arm+'-initial.ait')).write_bytes(initial)
                    reference[arm]={'initial':sha(initial)}
                if sha(initial)!=reference[arm]['initial']:raise RuntimeError('initial nonrepeatable')
                gc.collect()
                highwater_before=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                traced_before=0
                if phase=='memory':
                    tracemalloc.start(1)
                    traced_before=tracemalloc.get_traced_memory()[0]
                    tracemalloc.reset_peak()
                if phase=='timing' and tracemalloc.is_tracing():raise RuntimeError('traced timing')
                wall_start=time.perf_counter_ns();cpu_start=time.process_time_ns()
                wire=enc.encode(images[1],**kw)
                cpu_end=time.process_time_ns();wall_end=time.perf_counter_ns()
                memory=None
                if phase=='memory':
                    current,peak=tracemalloc.get_traced_memory()
                    memory=dict(before=traced_before,current=current,peak=peak,increment=peak-traced_before)
                    tracemalloc.stop()
                highwater_after=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                digest=sha(wire)
                if 'update' not in reference[arm]:
                    (out/(arm+'-update.ait')).write_bytes(wire);reference[arm]['update']=digest
                if digest!=reference[arm]['update']:raise RuntimeError('update nonrepeatable')
                raw['samples'].append(dict(phase=phase,pair=pair,arm=arm,order=order,
                    wall_start_ns=wall_start,wall_end_ns=wall_end,cpu_start_ns=cpu_start,cpu_end_ns=cpu_end,
                    wall_ns=wall_end-wall_start,cpu_ns=cpu_end-cpu_start,memory=memory,
                    rss_highwater_before_kib=highwater_before,rss_highwater_after_kib=highwater_after,
                    wire_sha256=digest,wire_bytes=len(wire),initial_sha256=sha(initial),
                    state=dict(sequence=enc.sequence,previous_sha256=sha(enc.previous.pixels),
                               kind=enc.last['kind'],changed_tiles=enc.last['changed_tiles'])))
                del wire,enc,initial
            save(out/'record.json',raw)
    raw.update(status='COMPLETE',wire=reference)
    save(out/'record.json',raw)
    print(json.dumps({'index':index,'status':raw['status'],'samples':len(raw['samples'])}))

if __name__=='__main__':main(int(sys.argv[1]))
