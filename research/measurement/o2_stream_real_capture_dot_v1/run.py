"""Offline retained-image codec transfer. No GUI, network or input actions."""
import argparse, gc, hashlib, json, os, resource, sys, time, tracemalloc
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'source'))
from stream_encoder import Encoder, StreamingEncoder, Frame
from PIL import Image

APPS=['dogfood-calc-01','dogfood-inkscape-02','dogfood-xterm-03']
sha=lambda b:hashlib.sha256(b).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--construction',action='store_true');args=ap.parse_args()
    out=ROOT/args.out;out.mkdir(exist_ok=False);(out/'wire').mkdir()
    resource.setrlimit(resource.RLIMIT_AS,(256*1024*1024,256*1024*1024))
    resource.setrlimit(resource.RLIMIT_CPU,(30,30))
    allowed=sorted(os.sched_getaffinity(0));os.sched_setaffinity(0,{allowed[0]})
    start=time.perf_counter_ns();counts=0
    manifest=json.loads((ROOT/'PROVENANCE.json').read_text())
    for r in manifest['records']:
        b=(ROOT/r['local']).read_bytes()
        assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==r['sha'],r['local']
    env={'python':sys.version,'pid':os.getpid(),'argv':sys.argv,'affinity':sorted(os.sched_getaffinity(0)),'as_limit':resource.getrlimit(resource.RLIMIT_AS),'cpu_limit':resource.getrlimit(resource.RLIMIT_CPU),'construction':args.construction,'passes':4,'timing_passes':3,'warmup_passes':0,'no_gui_no_model':True,'thread_limits':{k:os.environ.get(k) for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS']}}
    (out/'environment.json').write_text(json.dumps(env,indent=2)+'\n')
    with (out/'samples.jsonl').open('x') as log:
        for app in APPS:
            observations=json.loads((ROOT/'inputs'/app/'observations.json').read_text());frames=[]
            for obs in observations:
                p=ROOT/'inputs'/app/Path(obs['image']).name
                with Image.open(p) as im:
                    assert im.size==(1280,800) and im.mode=='RGB'
                    if args.construction:im=im.crop((0,0,67,65))
                    frames.append(Frame(im.width,im.height,im.mode,im.tobytes()))
            first_hashes={}
            for rep in range(4):
                encs={'canonical':Encoder('dogfood'),'streaming':StreamingEncoder('dogfood')}
                for idx,(obs,frame) in enumerate(zip(observations,frames)):
                    order=['canonical','streaming'] if (rep+idx)%2==0 else ['streaming','canonical']
                    wires={};pending=[]
                    for pos,arm in enumerate(order):
                        gc.collect();enc=encs[arm]
                        prior_sequence=enc.sequence;prior_hash=sha(enc.previous.pixels) if enc.previous is not None else None
                        if rep==3:tracemalloc.start()
                        w0=time.perf_counter_ns();c0=time.process_time_ns()
                        wire=enc.encode(frame,action_id=obs['action_id'],observed_ns=obs['capture_ns'],context=obs['context'])
                        cpu=time.process_time_ns()-c0;wall=time.perf_counter_ns()-w0
                        memory=tracemalloc.get_traced_memory() if rep==3 else None
                        if rep==3:tracemalloc.stop()
                        digest=sha(wire);wires[arm]=wire
                        if rep==0:
                            (out/'wire'/f'{app}-{idx+1:03}-{arm}.ait').write_bytes(wire);first_hashes[(idx,arm)]=digest
                        row={'app':app,'pass':rep,'sequence':idx+1,'arm':arm,'order':pos,'input':str(Path('inputs')/app/Path(obs['image']).name),'input_pixels_sha256':sha(frame.pixels),'wire_sha256':digest,'wire_bytes':len(wire),'first_pass_hash_matches':digest==first_hashes[(idx,arm)],'width':frame.width,'height':frame.height,'mode':frame.mode,'prior_sequence':prior_sequence,'prior_pixels_sha256':prior_hash,'state_sequence':enc.sequence,'state_pixels_sha256':sha(enc.previous.pixels),'kind':enc.last['kind'],'changed_tiles':enc.last['changed_tiles'],'wall_ns':wall,'cpu_ns':cpu,'tracemalloc_current':memory[0] if memory else None,'tracemalloc_peak':memory[1] if memory else None}
                        pending.append(row)
                    for row in pending:log.write(json.dumps(row,sort_keys=True)+'\n');counts+=1
                    log.flush()
                    assert wires['canonical']==wires['streaming'],'wire mismatch'
                    assert all(x['first_pass_hash_matches'] for x in pending),'pass mismatch'
            del frames
    (out/'execution.json').write_text(json.dumps({'records':counts,'wall_ns':time.perf_counter_ns()-start,'completed':True},indent=2)+'\n')
    print(json.dumps({'completed':True,'records':counts,'output':args.out}))

if __name__=='__main__':main()
