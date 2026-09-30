"""Generic preformal clock capability; no candidate or retained corpus imports."""
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import sys
import threading
import time

resource.setrlimit(resource.RLIMIT_AS,(256*1024*1024,256*1024*1024))
resource.setrlimit(resource.RLIMIT_CPU,(1,1))
cpu=min(os.sched_getaffinity(0));os.sched_setaffinity(0,{cpu})
rows=[];accumulator=1
for block in range(32):
    wall=time.monotonic_ns();process=time.process_time_ns();thread=time.thread_time_ns()
    for index in range(10000):
        accumulator=(accumulator*1664525+1013904223+index)%4294967296
    thread_end=time.thread_time_ns();process_end=time.process_time_ns();wall_end=time.monotonic_ns()
    rows.append({'block':block,'iterations':10000,'wall_ns':wall_end-wall,'process_cpu_ns':process_end-process,'thread_cpu_ns':thread_end-thread})
result={'kind':'generic_clock_capability_construction_only','source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'clocks':{name:vars(time.get_clock_info(name)) for name in ('monotonic','perf_counter','process_time','thread_time')},
        'cpu_affinity':sorted(os.sched_getaffinity(0)),'rlimit_as':list(resource.getrlimit(resource.RLIMIT_AS)),
        'rlimit_cpu':list(resource.getrlimit(resource.RLIMIT_CPU)),'active_thread_count':threading.active_count(),
        'rows':rows,'accumulator':accumulator,'candidate_calls':0,'corpus_reads':0}
with Path(sys.argv[1]).open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps({'blocks':len(rows),'wall_ns_total':sum(r['wall_ns'] for r in rows),
                 'process_nonzero':[r['process_cpu_ns'] for r in rows if r['process_cpu_ns']],
                 'thread_nonzero':[r['thread_cpu_ns'] for r in rows if r['thread_cpu_ns']]}))
