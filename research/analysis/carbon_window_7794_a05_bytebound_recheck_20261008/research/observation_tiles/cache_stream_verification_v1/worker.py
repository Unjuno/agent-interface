"""One bounded image-publication case. No GUI, network, or model use."""
from __future__ import annotations
import io,json,os,sys,time,tracemalloc
from pathlib import Path
from PIL import Image
from common import ROOT,load,dump,sha,store_blob,verify_freeze
from vendor.exact_gate import Frame
from legacy_candidate import Candidate
from stream_guard import GuardedSink


def main(case_id: str, out_dir: str) -> None:
    freeze_sha=verify_freeze()
    case=next(c for c in load(ROOT/'SCHEDULE.json') if c['id']==case_id)
    out=Path(out_dir);out.mkdir(parents=True,exist_ok=False)
    plan=load(ROOT/'ENVIRONMENT.json');os.sched_setaffinity(0,{plan['worker_cpu']})
    fixture=next(x for x in load(ROOT/'FIXTURES.json') if x['id']==case['image'])
    raw=(ROOT/fixture['path']).read_bytes()
    if sha(raw)!=fixture['sha256']:raise ValueError('input hash')
    Image.init()
    wrapper=(Candidate(out/'cache','BYTE_PIN_REPAIR') if case['policy']=='LEGACY_256K'
             else GuardedSink(out/'cache',case['policy']))
    record={'case':case,'freeze_sha256':freeze_sha,'pid':os.getpid(),
            'affinity':sorted(os.sched_getaffinity(0)), 'started_ns':time.monotonic_ns(),
            'publications':[], 'maintenance':None, 'probe':None}
    dump(out/'START.json',record)

    def snapshot():
        return {p.name: {'sha256':store_blob(p.read_bytes()),'bytes':p.stat().st_size}
                for p in sorted((out/'cache').iterdir()) if p.is_file()}

    def publish(pixels, label):
        # Fresh equal bytes+Frame; copying, snapshotting and journal I/O are untimed.
        frame=Frame(fixture['width'],fixture['height'],'RGB',bytes(bytearray(pixels)))
        start_cpu=time.process_time_ns();start=time.perf_counter_ns()
        result=None;error=None
        try: result=wrapper.publish(frame)
        except FileExistsError as exc: error=type(exc).__name__
        end=time.perf_counter_ns();end_cpu=time.process_time_ns()
        row={'label':label,'input_sha256':sha(pixels),'start_ns':start,'end_ns':end,
             'cpu_start_ns':start_cpu,'cpu_end_ns':end_cpu,'response':result,'error':error,
             'files':snapshot()}
        if result is not None:
            image=Path(result['receipt']['image'])
            if image.parent.resolve() != (out/'cache').resolve():raise ValueError('image escaped case')
            row['output_name']=image.name
            row['output_sha256']=store_blob(image.read_bytes())
        record['publications'].append(row)
        dump(out/'PARTIAL.json',record)
        return row

    initial=publish(raw,'initial');base=Path(initial['response']['receipt']['image'])
    initial_bytes=base.read_bytes();store_blob(initial_bytes)
    if case['kind']=='performance':
        for i in range(8): publish(raw,'warm-'+str(i))
        if case['policy']!='LEGACY_256K':
            before=snapshot()
            accounting=wrapper.inspect_cache(trace=True)
            # Separate, prescribed memory pass; not included in performance timings.
            tracemalloc.start(1);tracemalloc.reset_peak()
            memory_result=wrapper.inspect_cache()
            current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
            record['probe']={'accounting':accounting,'memory_result':memory_result,
                             'traced_current_bytes':current,'traced_peak_bytes':peak,
                             'before_files':before,'after_files':snapshot()}
    else:
        scenario=case['scenario'];next_raw=raw
        if scenario=='MISSING':base.unlink()
        elif scenario=='TRUNCATED':base.write_bytes(initial_bytes[:len(initial_bytes)//2])
        elif scenario=='TAIL_CHANGED':
            altered=bytearray(initial_bytes);at=len(altered)-32;altered[at]^=1;base.write_bytes(altered)
        elif scenario=='LOSSLESS_REENCODE':
            buf=io.BytesIO();Image.frombytes('RGB',(fixture['width'],fixture['height']),raw).save(buf,format='PNG',compress_level=0)
            if buf.getvalue()==initial_bytes:raise ValueError('reencode was identical')
            base.write_bytes(buf.getvalue())
        elif scenario in ('FRAME_CHANGED','NEXT_NAME_OCCUPIED'):
            altered=bytearray(raw);altered[0]^=1;next_raw=bytes(altered);store_blob(next_raw)
            if scenario=='NEXT_NAME_OCCUPIED':(out/'cache'/'002.png').write_bytes(b'owned collision sentinel\n')
        elif scenario=='APPENDED':base.write_bytes(initial_bytes+b'bounded-appended-data\n')
        else:raise ValueError('unknown condition')
        record['maintenance']={'scenario':scenario,'before_sha256':sha(initial_bytes),
                              'after_files':snapshot(),'completed_ns':time.monotonic_ns()}
        publish(next_raw,'post-maintenance')
        if scenario!='NEXT_NAME_OCCUPIED':publish(next_raw,'steady-after')
    record['ended_ns']=time.monotonic_ns();record['final_files']=snapshot()
    dump(out/'RESULT.json',record)
    print(json.dumps({'id':case_id,'result_sha256':sha((out/'RESULT.json').read_bytes()),
                      'publications':len(record['publications']),'pid':os.getpid()}),flush=True)

if __name__=='__main__':main(sys.argv[1],sys.argv[2])
