"""Frozen offline cost/byte/identity comparison; never launches a GUI/model.

python benchmark.py --artifact-dir /mnt/data --out /tmp/tile-revisit-01
An existing output directory is refused. The two historical ZIPs are separate
replay fixtures, never treated as valid independent live allocations or pooled.
"""
import argparse
import base64
from collections import Counter
import hashlib
import io
import itertools
import json
import os
from pathlib import Path
import platform
import random
import statistics
import sys
import time
import traceback
import zipfile
import zlib

import numpy as np
import PIL
from PIL import Image

from candidate import CoverageEncoder, ROOT
from tile_transport import Decoder, Encoder, Frame

HERE = Path(__file__).resolve().parent
BASE = '48a9de4d863404e21d7d347b0cfe6a16ac7f871d'
EXPECTED = {
    'research/observation_gating/exact_gate.py': 'd2629bc94d40cc0a8e1bf9e053585549218629ed',
    'research/observation_tiles/tile_transport.py': '0fd2b65edaeb8748ccca02fa502051c3bb17f48a',
}
ARTIFACTS = {
    'run-34968759795.zip': 'dabbc5630b99bde994c3595d09e3a414a3571960b755bc26cedcfd638829f375',
    'run-34968781910.zip': '274623504341e6e3419c07b1f07368ca4e0e87078d72ebe507ce925ee670813f',
}


def digest(data): return hashlib.sha256(data).hexdigest()


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def read_optional(path):
    try: return Path(path).read_text().strip()
    except OSError: return None


def environment():
    cpu = read_optional('/proc/cpuinfo') or ''
    fields = dict(line.split(':',1) for line in cpu.splitlines() if ':' in line)
    fields = {k.strip():v.strip() for k,v in fields.items()}
    clock = time.get_clock_info('perf_counter')
    return dict(python=sys.version, platform=platform.platform(), machine=platform.machine(),
                numpy=np.__version__, pillow=PIL.__version__, zlib_build=zlib.ZLIB_VERSION,
                zlib_runtime=zlib.ZLIB_RUNTIME_VERSION, cpu=fields.get('model name'),
                sampled_cpu_mhz=fields.get('cpu MHz'), frequency_fixed=False,
                available_cpus=os.cpu_count(), affinity=sorted(os.sched_getaffinity(0)),
                cgroup_cpu_max=read_optional('/sys/fs/cgroup/cpu.max'),
                clock=dict(implementation=clock.implementation,resolution_s=clock.resolution,
                           monotonic=clock.monotonic,adjustable=clock.adjustable),
                concurrency='one sequential benchmark process; shared-host scheduling uncontrolled',
                batch_size=1, network='not used; container direct GitHub DNS failed before work',
                frame_generation_and_png_decode='excluded; identical immutable bytes preloaded for all arms',
                combined_uncertainty='not estimated; no calibrated scheduler/frequency/scorer error model')


def verify_sources():
    hashes = {}
    for name, expected in EXPECTED.items():
        data=(ROOT/name).read_bytes()
        blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        if blob != expected: raise ValueError('baseline source differs: '+name)
        hashes[name]=dict(git_blob_sha1=blob,sha256=digest(data))
    for name,expected in json.loads((HERE/'prereg.json').read_text())['source_sha256'].items():
        actual=digest((HERE/name).read_bytes())
        if actual != expected: raise ValueError('candidate source differs: '+name)
        hashes[name]=dict(sha256=actual)
    return hashes


def workloads(artifact_dir):
    rng=random.Random(990701)
    width,height=640,480
    textured=rng.randbytes(width*height*3)
    rows=[]
    for name in ('quiet','sparse_textured','sparse_flat','dense_textured','dense_flat'):
        data=bytearray(textured if 'textured' in name or name=='quiet' else bytes(width*height*3))
        frames=[]
        for index in range(16):
            if index and name.startswith('sparse'):
                # One fixed-seed pixel/channel mutation; entire 64px tile is retained.
                position=rng.randrange(len(data)); data[position] ^= 1 + index
            elif index and name=='dense_textured': data=bytearray(rng.randbytes(len(data)))
            elif index and name=='dense_flat': data=bytearray(bytes([index])*len(data))
            frames.append(Frame(width,height,'RGB',bytes(data)))
        rows.append((name,frames,dict(kind='synthetic',seed=990701,frames=16)))
    for filename,expected in ARTIFACTS.items():
        path=artifact_dir/filename
        data=path.read_bytes()
        if digest(data)!=expected: raise ValueError('artifact digest mismatch: '+filename)
        frames=[]; refs=[]
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            names=sorted(n for n in archive.namelist() if n.endswith('.png') and '/runtime/' in n)
            if len(names)!=7: raise ValueError('expected seven retained PNGs')
            for name in names:
                raw=archive.read(name)
                with Image.open(io.BytesIO(raw)) as im:
                    rgb=im.convert('RGB'); pixels=rgb.tobytes()
                    frames.append(Frame(rgb.width,rgb.height,'RGB',pixels))
                refs.append(dict(member=name,png_sha256=digest(raw),rgb_sha256=digest(pixels)))
        rows.append((filename.removesuffix('.zip'),frames,
                     dict(kind='historical invalidated-allocation artifact replay',
                          zip_sha256=expected,frame_members=refs)))
    return rows


def evaluate(arm, name, frames, round_index, order):
    enc=CoverageEncoder('fixed-stream') if arm=='coverage25' else Encoder('fixed-stream',arm)
    dec=Decoder('fixed-stream')
    total_encode=total_decode=warm_encode=warm_decode=0
    wire_bytes=warm_bytes=0
    routes=Counter(); fingerprint=hashlib.sha256()
    for index, frame in enumerate(frames):
        # Same metadata across all arms; these are logical replay clocks, not live timestamps.
        meta=dict(action_id=f'action-{index:03d}', observed_ns=index*1000000,
                  context=('offline-fixture',name,index))
        start=time.perf_counter_ns(); wire=enc.encode(frame,**meta); encoded=time.perf_counter_ns()
        got=dec.accept(wire); decoded=time.perf_counter_ns()
        en,de=encoded-start,decoded-encoded
        total_encode+=en; total_decode+=de; wire_bytes+=len(wire)
        if index: warm_encode+=en; warm_decode+=de; warm_bytes+=len(wire)
        if got!=frame: raise AssertionError('pixel/geometry failure')
        if (dec.metadata['action_id']!=meta['action_id'] or
            dec.metadata['observed_ns']!=meta['observed_ns'] or
            dec.metadata['context']!=list(meta['context']) or dec.sequence!=index+1):
            raise AssertionError('metadata failure')
        fingerprint.update(len(wire).to_bytes(8,'big')); fingerprint.update(wire)
        routes[enc.last['kind']]+=1
    return dict(workload=name,arm=arm,round=round_index,order=order,frames=len(frames),
                encode_ns=total_encode,decode_ns=total_decode,total_ns=total_encode+total_decode,
                warm_ns=warm_encode+warm_decode,bytes=wire_bytes,warm_bytes=warm_bytes,
                routes=dict(routes),packet_stream_sha256=fingerprint.hexdigest(),exact=True)


def summarize(raw):
    result={}
    for name in dict.fromkeys(row['workload'] for row in raw):
        arms={}
        for arm in ('O1','O2','coverage25'):
            rows=[r for r in raw if r['workload']==name and r['arm']==arm]
            if len(rows)!=12 or len({r['packet_stream_sha256'] for r in rows})!=1:
                raise AssertionError('round count/non-deterministic serialization')
            times=[r['total_ns']/1e6 for r in rows]
            arms[arm]=dict(frames=rows[0]['frames'],rounds=len(rows),bytes=rows[0]['bytes'],
                          warm_bytes=rows[0]['warm_bytes'],routes=rows[0]['routes'],
                          median_sequence_ms=statistics.median(times),min_sequence_ms=min(times),
                          max_sequence_ms=max(times),p95_sequence_ms=float(np.percentile(times,95)),
                          median_warm_ms=statistics.median(r['warm_ns']/1e6 for r in rows),
                          median_encode_ms=statistics.median(r['encode_ns']/1e6 for r in rows),
                          median_decode_ms=statistics.median(r['decode_ns']/1e6 for r in rows))
        b,c=arms['O2'],arms['coverage25']
        cost_ratio=c['bytes']/b['bytes']; time_ratio=c['median_sequence_ms']/b['median_sequence_ms']
        p95_ratio=c['p95_sequence_ms']/b['p95_sequence_ms']
        byte_ok=cost_ratio<=1.05
        # Quiet control is identity/bytes only, not a tiny-timer speed gate.
        faster=name=='quiet' or (time_ratio<=0.90 and p95_ratio<=1.10)
        decision='PASS_SCOPED_OFFLINE' if byte_ok and faster else ('REJECT_BYTE_REGRESSION' if not byte_ok else 'HOLD_NO_FROZEN_SPEED_BENEFIT')
        result[name]=dict(arms=arms,bytes_ratio_vs_O2=cost_ratio,median_ratio_vs_O2=time_ratio,
                          p95_ratio_vs_O2=p95_ratio,decision=decision)
    return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--artifact-dir',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True); args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    raw=[]
    try:
        save(args.out/'environment.json',environment());save(args.out/'sources.json',verify_sources())
        sets=workloads(args.artifact_dir)
        save(args.out/'inputs.json',{n:dict(provenance=p,frame_sha256=[digest(f.pixels) for f in fs]) for n,fs,p in sets})
        permutations=list(itertools.permutations(('O1','O2','coverage25')))
        with (args.out/'rounds.jsonl').open('x',encoding='utf-8') as log:
            for name,frames,_ in sets:
                # Exactly one full-stream unmeasured warmup per arm; correctness checked.
                for arm in permutations[0]: evaluate(arm,name,frames,-1,-1)
                for round_index in range(12):
                    for order,arm in enumerate(permutations[round_index%6]):
                        row=evaluate(arm,name,frames,round_index,order);raw.append(row)
                        log.write(json.dumps(row,sort_keys=True,separators=(',',':'))+'\n');log.flush()
                print(name,'finished',flush=True)
        summary=summarize(raw)
        overall='RETAIN_SCOPED_CANDIDATE' if all(x['decision']=='PASS_SCOPED_OFFLINE' for x in summary.values()) else 'HOLD_GLOBAL_PROMOTION_RETAIN_ALL_REGIMES'
        save(args.out/'summary.json',dict(base_commit=BASE,allocation='OPT-REVISIT-TILE-001',
            result_class=overall,exact_decodes=sum(r['frames'] for r in raw),
            timing_rounds=len(raw),warmup_decodes=sum(len(fs)*3 for _,fs,_ in sets),
            model_calls=0,gui_actions=0,live_allocations=0,workloads=summary))
        save(args.out/'completion.json',dict(status='COMPLETED',retained_rows=len(raw)))
    except Exception:
        save(args.out/'failure.json',dict(error=traceback.format_exc(),retained_rows=len(raw)))
        raise


if __name__=='__main__': main()
