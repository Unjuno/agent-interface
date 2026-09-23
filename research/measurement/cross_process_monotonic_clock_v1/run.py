from __future__ import annotations
import subprocess, sys, json, time, gzip, hashlib, platform, os, statistics, pathlib
ROOT=pathlib.Path(__file__).resolve().parent
NPROC=32
NEX=4096
RAW=ROOT/'raw.jsonl.gz'

def percentile(vals, q):
    xs=sorted(vals)
    if not xs: return None
    i=min(len(xs)-1, max(0, int(round((len(xs)-1)*q))))
    return xs[i]

def main():
    if RAW.exists() or (ROOT/'result.json').exists():
        raise SystemExit('exclusive first outcome already exists')
    h=hashlib.sha256(); rows=0; perf_fail=0; mono_fail=0; clock_fail=0; missing=0; dup=0
    rtts=[]; child_proc_ns=[]; perf_minus_clock=[]; mono_minus_clock=[]
    child_metas=[]; seen=set()
    start=time.perf_counter_ns()
    with gzip.open(RAW,'wt',encoding='utf-8',compresslevel=6) as out:
        for pi in range(NPROC):
            p=subprocess.Popen([sys.executable, str(ROOT/'child.py')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
            assert p.stdin and p.stdout and p.stderr
            meta=json.loads(p.stdout.readline())
            child_metas.append(meta['meta'])
            for j in range(NEX):
                seq=pi*NEX+j
                nonce=hashlib.sha256(f'{pi}:{j}:CROSS-PROCESS-MONOTONIC-CLOCK-COMPARABILITY-20260917-001'.encode()).hexdigest()[:24]
                p_perf_send=time.perf_counter_ns(); p_mono_send=time.monotonic_ns(); p_clock_send=time.clock_gettime_ns(time.CLOCK_MONOTONIC)
                p.stdin.write(json.dumps({'seq':seq,'nonce':nonce},separators=(',',':'))+'\n'); p.stdin.flush()
                resp=json.loads(p.stdout.readline())
                p_perf_recv=time.perf_counter_ns(); p_mono_recv=time.monotonic_ns(); p_clock_recv=time.clock_gettime_ns(time.CLOCK_MONOTONIC)
                row={
                    'process_index':pi,'seq':seq,'nonce':nonce,
                    'p_perf_send':p_perf_send,'p_mono_send':p_mono_send,'p_clock_send':p_clock_send,
                    **resp,
                    'p_perf_recv':p_perf_recv,'p_mono_recv':p_mono_recv,'p_clock_recv':p_clock_recv,
                }
                line=json.dumps(row,separators=(',',':'),sort_keys=True)
                out.write(line+'\n'); h.update((line+'\n').encode())
                rows += 1
                key=(row['seq'],row['nonce'])
                if key in seen: dup += 1
                seen.add(key)
                if not (p_perf_send <= row['c_perf_recv'] <= row['c_perf_send'] <= p_perf_recv): perf_fail += 1
                if not (p_mono_send <= row['c_mono_recv'] <= row['c_mono_send'] <= p_mono_recv): mono_fail += 1
                if not (p_clock_send <= row['c_clock_recv'] <= row['c_clock_send'] <= p_clock_recv): clock_fail += 1
                rtts.append(p_perf_recv-p_perf_send)
                child_proc_ns.append(row['c_perf_send']-row['c_perf_recv'])
                perf_minus_clock.extend([row['c_perf_recv']-row['c_clock_recv'], row['c_perf_send']-row['c_clock_send']])
                mono_minus_clock.extend([row['c_mono_recv']-row['c_clock_recv'], row['c_mono_send']-row['c_clock_send']])
            p.stdin.close(); rc=p.wait(timeout=5); err=p.stderr.read()
            if rc != 0: raise RuntimeError(f'child {pi} rc={rc} stderr={err!r}')
    elapsed=time.perf_counter_ns()-start
    expected=NPROC*NEX
    missing=expected-len(seen)
    parent_meta={
        'pid':os.getpid(),'python':sys.version,'platform':platform.platform(),
        'perf':vars(time.get_clock_info('perf_counter')),
        'mono':vars(time.get_clock_info('monotonic')),
        'clock_monotonic_available':hasattr(time,'CLOCK_MONOTONIC'),
    }
    res={
        'task':'CROSS-PROCESS-MONOTONIC-CLOCK-COMPARABILITY-20260917-001',
        'base':'159dd3684ffcd0ee78b9ff5939e0173cd77c7b4f',
        'processes':NPROC,'exchanges_per_process':NEX,'expected_rows':expected,'rows':rows,
        'unique_rows':len(seen),'missing_rows':missing,'duplicate_rows':dup,
        'perf_containment_failures':perf_fail,'mono_containment_failures':mono_fail,'clock_containment_failures':clock_fail,
        'raw_uncompressed_sha256':h.hexdigest(),'raw_gzip_bytes':RAW.stat().st_size,'elapsed_ns':elapsed,
        'rtt_ns':{'p50':int(statistics.median(rtts)),'p95':percentile(rtts,.95),'p99':percentile(rtts,.99),'max':max(rtts)},
        'child_processing_ns':{'p50':int(statistics.median(child_proc_ns)),'p95':percentile(child_proc_ns,.95),'p99':percentile(child_proc_ns,.99),'max':max(child_proc_ns)},
        'perf_minus_clock_ns':{'min':min(perf_minus_clock),'max':max(perf_minus_clock),'p50':int(statistics.median(perf_minus_clock))},
        'mono_minus_clock_ns':{'min':min(mono_minus_clock),'max':max(mono_minus_clock),'p50':int(statistics.median(mono_minus_clock))},
        'parent_meta':parent_meta,
        'child_meta_unique':list({json.dumps(m,sort_keys=True) for m in child_metas}),
        'formal_live_allocation':False,'x11_actions':0,'task_input_actions':0,
    }
    (ROOT/'result.json').write_text(json.dumps(res,indent=2,sort_keys=True))
    print(json.dumps(res,sort_keys=True))
if __name__=='__main__': main()
