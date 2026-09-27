"""Issue 2561: controlled browser-rendered change-gate cost, no OS input/model.
Formal output is exclusive-create. Never reuse a consumed allocation directory.
"""
from __future__ import annotations
import argparse, hashlib, io, json, os, platform, random, sys, time, traceback, tracemalloc
from pathlib import Path
import importlib.metadata
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
W, H, N = 320, 240, 320*240*3
POLICIES = ('GLOBAL_AHASH_ONLY', 'AHASH_EXACT_FALLBACK', 'EXACT_ONLY')
STRATA = ('unchanged','noise','text','selection','critical','large')

def dump(path: Path, value):
    path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def ahash(b: bytes) -> int:
    if type(b) is not bytes or len(b) != N:
        raise ValueError('expected exact 320x240 RGB bytes')
    a=np.frombuffer(b,dtype=np.uint8).reshape(8,30,8,40,3)
    sums=a.sum(axis=(1,3,4),dtype=np.uint64).reshape(64)
    bits=sums*64 >= sums.sum(dtype=np.uint64)
    return int.from_bytes(np.packbits(bits,bitorder='big').tobytes(),'big')

def gate(policy: str, a: bytes, b: bytes) -> tuple[bool,bool]:
    if type(a) is not bytes or type(b) is not bytes or len(a)!=N or len(b)!=N:
        raise ValueError('bad raster shape/type')
    if policy=='EXACT_ONLY': return (a!=b,False)
    different=ahash(a)!=ahash(b)
    if policy=='GLOBAL_AHASH_ONLY': return (different,False)
    if policy=='AHASH_EXACT_FALLBACK': return (different or a!=b,not different)
    raise ValueError('unknown policy')

def specs(construction: bool):
    rng=random.Random(256120260922)
    families=[0] if construction else range(10)
    variants=[99] if construction else range(5)
    for family in families:
        for variant in variants:
            for stratum in STRATA:
                order=list(POLICIES);rng.shuffle(order)
                yield {'id':f'f{family:02d}-v{variant:02d}-{stratum}',
                       'family':family,'variant':variant,'stratum':stratum,
                       'must_forward':stratum in ('text','selection','critical','large'),
                       'semantic_importance':'task' if stratum in ('text','selection','critical','large') else 'benign',
                       'policy_order':order}

def source_hashes():
    names=('experiment.py','audit.py','fixture.html','PLAN.json','predecessor.py')
    return {n:sha((ROOT/n).read_bytes()) for n in names}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--construction',action='store_true');args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    out=args.out;frames=out/'frames';frames.mkdir()
    dump(out/'invocation.json',{'argv':sys.argv,'pid':os.getpid(),'started_wall_ns':time.time_ns(),
                               'formal':not args.construction,'invocations':1,'retries':0})
    try:
        plan=json.loads((ROOT/'PLAN.json').read_text())
        hashes=source_hashes()
        if not args.construction:
            if hashes!=json.loads((ROOT/'SOURCE_MANIFEST.json').read_text()):
                raise RuntimeError('STOP_SOURCE_MISMATCH')
        dump(out/'source.json',hashes)
        dump(out/'schedule.json',list(specs(args.construction)))
        requests=[]
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,
                args=['--no-sandbox','--disable-background-networking','--disable-component-update',
                      '--disable-sync','--disable-default-apps','--no-first-run'])
            context=browser.new_context(viewport={'width':W,'height':H},device_scale_factor=1,
                                        locale='en-US',timezone_id='UTC',service_workers='block')
            def block(route):
                requests.append(route.request.url);route.abort()
            context.route('**/*',block)
            page=context.new_page();page.set_default_timeout(5000)
            page.set_content((ROOT/'fixture.html').read_text())
            env={'python':sys.version,'platform':platform.platform(),'browser_version':browser.version,
                 'packages':{n:importlib.metadata.version(n) for n in ('numpy','Pillow','playwright')},
                 'provided_execution_container':True,'docker_cli':False,'docker_image_identity':None,
                 'clock':vars(time.get_clock_info('perf_counter')),'network_policy':'browser requests aborted; no Docker network-none claim',
                 'model_calls':0,'os_task_input_calls':0,'rgb_bytes_per_frame':N,'timing_repeats':plan['timing_repeats']}
            dump(out/'environment.json',env)
            # Warmup is a generated uniform raster, not a formal pair.
            warm=bytes([130])*N;warm2=bytes(bytearray(warm))
            for policy in POLICIES:
                for _ in range(plan['warmup_calls']): gate(policy,warm,warm2)
            memory={}
            for policy in POLICIES:
                tracemalloc.start();tracemalloc.reset_peak()
                gate(policy,warm,warm2)
                current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
                memory[policy]={'traced_current_bytes':current,'traced_peak_bytes':peak}
            dump(out/'memory.json',{'scope':'one excluded uniform equal raster; Python-visible allocations, not total browser/native/RSS','policies':memory})
            with (out/'rows.jsonl').open('x',encoding='utf-8') as log:
                for spec in specs(args.construction):
                    images=[];receipts=[];rgb=[]
                    for after in (False,True):
                        receipt=page.evaluate('(x)=>window.renderCase(x)',{**spec,'after':after})
                        png=page.screenshot(type='png',animations='disabled',caret='hide',scale='css')
                        im=Image.open(io.BytesIO(png));im.load()
                        if im.size!=(W,H): raise RuntimeError('STOP_RASTER_SIZE')
                        b=im.convert('RGB').tobytes()
                        digest=sha(png);path=frames/(digest+'.png')
                        if not path.exists(): path.write_bytes(png)
                        images.append({'png_sha256':digest,'png_bytes':len(png),'rgb_sha256':sha(b)})
                        receipts.append(receipt);rgb.append(b)
                    a,b=rgb
                    if a is b: raise RuntimeError('STOP_IDENTITY_SHORTCUT')
                    decisions={}
                    for policy in spec['policy_order']:
                        first=gate(policy,a,b)
                        start=time.perf_counter_ns()
                        for _ in range(plan['timing_repeats']): last=gate(policy,a,b)
                        elapsed=time.perf_counter_ns()-start
                        if first!=last: raise RuntimeError('STOP_NONDETERMINISTIC')
                        decisions[policy]={'forward':first[0],'exact_fallback':first[1],
                                           'batch_elapsed_ns':elapsed,'repeats':plan['timing_repeats']}
                    arr1=np.frombuffer(a,np.uint8).reshape(H,W,3);arr2=np.frombuffer(b,np.uint8).reshape(H,W,3)
                    mask=np.any(arr1!=arr2,axis=2);yy,xx=np.where(mask)
                    region=None if not len(xx) else [int(xx.min()),int(yy.min()),int(xx.max()-xx.min()+1),int(yy.max()-yy.min()+1)]
                    row={**spec,'images':images,'receipts':receipts,'hashes':[f'{ahash(a):016x}',f'{ahash(b):016x}'],
                         'exact_same':a==b,'changed_pixels':int(mask.sum()),'changed_bbox':region,'decisions':decisions}
                    log.write(json.dumps(row,sort_keys=True,allow_nan=False)+'\n');log.flush()
            dump(out/'network.json',{'blocked_requests':requests,'count':len(requests)})
            context.close();browser.close()
        if source_hashes()!=hashes: raise RuntimeError('STOP_POSTRUN_SOURCE_DRIFT')
        dump(out/'exit.json',{'returncode':0,'status':'COMPLETE_UNSCORED','ended_wall_ns':time.time_ns()})
    except Exception as e:
        dump(out/'exit.json',{'returncode':1,'status':'STOP_INFRASTRUCTURE','error':repr(e),'traceback':traceback.format_exc()})
        raise

if __name__=='__main__': main()
