"""Frozen, opt-in encoder -> unchanged decoder -> real PNG sink comparison.

No GUI, model, network or formal DOOM allocation. Times exclude source creation,
post-publication verification and log serialization. Output is never overwritten.
"""
import argparse
import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import statistics
import sys
import tempfile
import time
import traceback
import zlib
import numpy as np
import PIL
from PIL import Image
from candidate import ConditionalEncoder, Encoder, Decoder, Frame, ROOT
from image_artifact import ImageArtifactSink

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('prior_candidate',
    ROOT/'research/conditional_optimization/transport-revisit-v1/candidate.py')
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
ARMS = ['O1', 'O2', 'V1', 'V2']
ORDER = [[0,1,3,2], [1,2,0,3], [2,3,1,0], [3,0,2,1]]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fixtures():
    rng = np.random.default_rng(20260915)
    h, w = 256, 384
    yy, xx = np.indices((h, w))
    pattern = np.stack([(xx*7+yy*3)%256, (xx//12*17)%256, (yy//8*31)%256], axis=2).astype(np.uint8)
    frame = Frame(w, h, 'RGB', pattern.tobytes())
    groups = {'repeat_shared': ([frame]*8,64),
              'repeat_copied': ([Frame(w,h,'RGB',bytes(bytearray(frame.pixels))) for _ in range(8)],64)}
    a = rng.integers(0,256,(h,w,3),dtype=np.uint8)
    frames = []
    for i in range(8):
        if i:
            a[10:22,10:22] ^= 255
        frames.append(Frame(w,h,'RGB',a.tobytes()))
    groups['sparse_random'] = (frames,64)
    groups['dense_scroll'] = ([Frame(w,h,'RGB',np.roll(pattern,17*i,axis=1).tobytes()) for i in range(8)],64)
    groups['dense_random'] = ([Frame(w,h,'RGB',rng.integers(0,256,(h,w,3),dtype=np.uint8).tobytes()) for _ in range(8)],64)
    groups['sparse_header_counterexample'] = ([Frame(8,8,'L',bytes([i%2])*16+bytes(48)) for i in range(8)],1)
    return groups


def fixture_manifest(groups):
    return {name:{'tile_size':size,'frames':[
        {'width':f.width,'height':f.height,'mode':f.mode,'sha256':digest(f.pixels)} for f in frames]}
        for name,(frames,size) in groups.items()}


def environment():
    cpu = Path('/proc/cpuinfo').read_text() if Path('/proc/cpuinfo').exists() else ''
    allowed = sorted(os.sched_getaffinity(0)) if hasattr(os,'sched_getaffinity') else None
    return {'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        'python':sys.version,'platform':platform.platform(),'numpy':np.__version__,
        'pillow':PIL.__version__,'zlib':zlib.ZLIB_RUNTIME_VERSION,
        'cpu_info_sample':[l for l in cpu.splitlines() if l.startswith(('model name','cpu MHz'))][:2],
        'cpu_count':os.cpu_count(),'affinity':allowed,'clock':vars(time.get_clock_info('perf_counter')),
        'clock_fixed':False,'single_benchmark_process':True,'host_contention':'unknown',
        'memory_max':Path('/sys/fs/cgroup/memory.max').read_text().strip() if Path('/sys/fs/cgroup/memory.max').exists() else None}


def run(plan_path, out):
    out.mkdir(parents=True, exist_ok=False)
    plan_bytes = plan_path.read_bytes()
    plan = json.loads(plan_bytes)
    rows, receipts, error = [], {}, None
    (out/'environment.json').write_text(json.dumps(environment(),indent=2)+'\n')
    (out/'plan.json').write_bytes(plan_bytes)
    fields = ['dataset','block','position','arm','frames','exact','wire_bytes',
              'reused','codec_ns','publish_ns','pipeline_ns','steady_codec_ns','steady_pipeline_ns']
    raw = out/'raw.csv'
    try:
        for path, expected in plan['sources'].items():
            if digest((ROOT/path).read_bytes()) != expected:
                raise ValueError('source hash mismatch: '+path)
        groups = fixtures()
        if fixture_manifest(groups) != plan['inputs']:
            raise ValueError('fixture mismatch')
        with raw.open('x',newline='') as fh:
            writer = csv.DictWriter(fh,fieldnames=fields); writer.writeheader()
            names = list(groups)
            for block in range(plan['blocks']):
                for name in names[block%len(names):]+names[:block%len(names)]:
                    frames, size = groups[name]
                    for position, ai in enumerate(ORDER[block%4]):
                        arm = ARMS[ai]
                        enc = (Encoder('bench',arm,size) if ai < 2 else
                               prior.ConditionalEncoder('bench',size) if ai == 2 else
                               ConditionalEncoder('bench',size))
                        dec = Decoder('bench')
                        row = dict(dataset=name,block=block,position=position,arm=arm,
                            frames=0,exact=True,wire_bytes=0,reused=0,codec_ns=0,publish_ns=0,
                            pipeline_ns=0,steady_codec_ns=0,steady_pipeline_ns=0)
                        frame_receipts = []
                        with tempfile.TemporaryDirectory(prefix='co-png-') as td:
                            sink = ImageArtifactSink(td,compress_level=6,reuse=True)
                            for i, frame in enumerate(frames):
                                kw = dict(action_id=f'a{i}',observed_ns=1000+i,context=('surface',i))
                                t0=time.perf_counter_ns(); wire=enc.encode(frame,**kw)
                                rebuilt=dec.accept(wire); t1=time.perf_counter_ns()
                                artifact=sink.publish(rebuilt); t2=time.perf_counter_ns()
                                # Check all decoded bytes and metadata after the measured boundary.
                                if rebuilt != frame or any(dec.metadata[k] != v for k,v in
                                    {'action_id':kw['action_id'],'observed_ns':kw['observed_ns'],
                                     'context':['surface',i],'sequence':i+1,'base':i}.items()):
                                    raise AssertionError('frame/metadata mismatch')
                                with Image.open(artifact['image']) as image:
                                    if (image.size,image.mode,image.tobytes()) != ((frame.width,frame.height),frame.mode,frame.pixels):
                                        raise AssertionError('PNG mismatch')
                                frame_receipts.append({'wire_sha256':digest(wire),'png_sha256':digest(Path(artifact['image']).read_bytes()),
                                    'kind':dec.metadata['kind'],'wire_bytes':len(wire),'reused':artifact['image_reused']})
                                row['frames']+=1; row['wire_bytes']+=len(wire); row['reused']+=int(artifact['image_reused'])
                                row['codec_ns']+=t1-t0; row['publish_ns']+=t2-t1; row['pipeline_ns']+=t2-t0
                                if i: row['steady_codec_ns']+=t1-t0; row['steady_pipeline_ns']+=t2-t0
                        key=name+'/'+arm
                        if key in receipts and receipts[key] != frame_receipts:
                            raise AssertionError('non-deterministic packets or PNGs')
                        receipts[key]=frame_receipts
                        writer.writerow(row);fh.flush();rows.append(row)
                print('completed block',block+1,flush=True)
        for name in groups:
            if receipts[name+'/V1'] != receipts[name+'/V2']:
                raise AssertionError('v1/v2 wire or PNG incompatibility')
    except Exception:
        error=traceback.format_exc()
        (out/'failure.txt').write_text(error)
    summaries={}
    for name in plan['inputs']:
        summaries[name]={}
        for arm in ARMS:
            selected=[r for r in rows if r['dataset']==name and r['arm']==arm]
            summaries[name][arm]={'sequences':len(selected)}
            if selected:
                for metric in ['codec_ns','publish_ns','pipeline_ns','steady_codec_ns','steady_pipeline_ns']:
                    values=[r[metric]/1e6 for r in selected]
                    summaries[name][arm][metric.replace('_ns','_ms')]={
                        'median':statistics.median(values),'min':min(values),'max':max(values)}
                summaries[name][arm]['wire_bytes']=selected[0]['wire_bytes']
    complete=error is None and len(rows)==len(plan['inputs'])*len(ARMS)*plan['blocks']
    repeat_gate=complete and all(summaries[n]['V2']['steady_codec_ms']['median']<=
        .9*summaries[n]['V1']['steady_codec_ms']['median'] for n in ['repeat_shared','repeat_copied'])
    result={'allocation_id':plan['allocation_id'],'base_commit':plan['base_commit'],
        'plan_sha256':digest(plan_bytes),'raw_sha256':digest(raw.read_bytes()) if raw.exists() else None,
        'sequences':len(rows),'frames':sum(r['frames'] for r in rows),'mechanics_pass':complete,
        'repeat_10_percent_gate':repeat_gate,'failure':error,'summaries':summaries,
        'default_promotion':False,'scope':'Offline transport/PNG integration, not GUI/model efficacy.'}
    (out/'receipts.json').write_text(json.dumps(receipts,indent=2)+'\n')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return complete


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--plan',type=Path,default=HERE/'plan.json')
    args=parser.parse_args()
    raise SystemExit(0 if run(args.plan,args.out) else 1)
