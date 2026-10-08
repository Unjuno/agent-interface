"""Finite staged GUI experiment. No LLM and no continuous-motion claim."""
import argparse
from dataclasses import asdict
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import time
import traceback
from backend import environment, click, capture
from guard import acquire, propose
HERE=Path(__file__).resolve().parent


def digest(b):return hashlib.sha256(b).hexdigest()
def dump(p,obj):
    with p.open('x',encoding='utf-8') as f:
        json.dump(obj,f,sort_keys=True,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())


def mutate(page,kind):
    start=time.perf_counter_ns()
    page.evaluate('(k)=>window.change(k)',kind)
    page.wait_for_timeout(20)
    return {'kind':kind,'start_ns':start,'end_ns':time.perf_counter_ns()}


def run(out,seed,smoke=False):
    out.mkdir(parents=True,exist_ok=False)
    plan=json.loads((HERE/'plan.json').read_text())
    if not smoke:
        for n,h in plan['source_sha256'].items():
            if digest((HERE/n).read_bytes())!=h:raise RuntimeError('source mismatch: '+n)
        if seed not in plan['seeds']:raise ValueError('unregistered seed')
    dump(out/'plan.json',plan)
    dump(out/'environment.json',{'python':platform.python_version(),'platform':platform.platform(),
         'cpuinfo':Path('/proc/cpuinfo').read_text(),'affinity':sorted(os.sched_getaffinity(0)),
         'clock':str(time.get_clock_info('perf_counter')),
         'chromium':subprocess.check_output(['chromium','--version'],text=True).strip(),
         'xlib_module_version':str(__import__('Xlib').__version__),
         'versions':{p:importlib.metadata.version(p) for p in ['numpy','Pillow','playwright']}})
    rows=[]
    try:
        with environment() as (page,cdp,d,name,origin):
            dump(out/'calibration.json',{'origin':list(origin),'viewport':[800,600],'dpr':1})
            cases=plan['cases'][:1] if smoke else plan['cases']
            methods=plan['methods']
            with (out/'raw.jsonl').open('x',encoding='utf-8') as log:
                for ci,case in enumerate(cases):
                    offset=(ci+seed)%len(methods)
                    order=methods[offset:]+methods[:offset]
                    for method in order:
                        page.evaluate('(s)=>window.setup(s)',seed);page.wait_for_timeout(25)
                        binding,source=acquire(cdp)
                        folder=out/(case['name']+'--'+method);folder.mkdir()
                        evidence={'source':source,'binding':asdict(binding),'transitions':[]}
                        evidence['transitions'].append(mutate(page,case['before']))
                        early=propose(cdp,None if method=='current_semantic' else binding)
                        evidence['early']=early
                        evidence['transitions'].append(mutate(page,case['between']))
                        # Only the nominated final-check arm pays for an extra observation.
                        late=propose(cdp,binding) if method=='bound_final' else None
                        evidence['late']=late
                        chosen=late if late is not None else early
                        evidence['transitions'].append(mutate(page,case['after']))
                        image_clock=capture(name,origin,folder/'pre-input.png')
                        # Capture is evidence-only and not read by the selector.
                        event=click(d,chosen['point'],origin) if chosen['point'] is not None else None
                        page.wait_for_timeout(25)
                        scores=page.evaluate('()=>window.readScores()')
                        if not event and scores:raise AssertionError('event after abstention')
                        if event and len(scores)>1:raise AssertionError('duplicate application effect')
                        if scores and (not scores[0]['trusted'] or scores[0]['x']!=event['point'][0]
                                       or scores[0]['y']!=event['point'][1]):
                            raise AssertionError('untrusted or miscalibrated effect')
                        outcome=scores[0]['hit'] if scores else ('no_event' if event else 'abstain')
                        selected_us=(early['end_ns']-early['start_ns']+
                            (late['end_ns']-late['start_ns'] if late else 0))/1000
                        row={'case':case['name'],'seed':seed,'method':method,'outcome':outcome,
                             'evidence':evidence,'event':event,'scores':scores,'image_clock':image_clock,
                             'selector_us':selected_us,'point':chosen['point'],'reason':chosen['reason'],
                             'boundary_negative':case['boundary_negative']}
                        dump(folder/'record.json',row)
                        rows.append(row);log.write(json.dumps(row,separators=(',',':'))+'\n')
                        log.flush();os.fsync(log.fileno())
                    print(json.dumps({'seed':seed,'case':case['name'],'records':len(rows)}),flush=True)
        summary={m:{k:sum(r['method']==m and r['outcome']==k for r in rows)
                     for k in ['target','wrong','background','no_event','abstain']} for m in methods}
        for m in methods:
            summary[m]['selector_median_us']=statistics.median(r['selector_us'] for r in rows if r['method']==m)
        dump(out/'summary.json',{'records':len(rows),'summary':summary,'smoke':smoke,
             'allocation':plan['allocation_id'],'scope':'staged GUI mechanics, no production runtime or LLM'})
    except Exception:
        dump(out/'failure.json',{'completed':len(rows),'traceback':traceback.format_exc()})
        raise
    finally:
        dump(out/'manifest.json',{str(p.relative_to(out)):{'bytes':p.stat().st_size,'sha256':digest(p.read_bytes())}
                                  for p in sorted(out.rglob('*')) if p.is_file()})


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--seed',type=int,required=True);ap.add_argument('--smoke',action='store_true')
    a=ap.parse_args();run(a.out,a.seed,a.smoke)
