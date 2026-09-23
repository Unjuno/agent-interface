import argparse,hashlib,json,statistics,time
from pathlib import Path
from contract import current_only_select,temporal_select,virtual_effect_latency_ns
from oracle import select_current,select_temporal,expected
from corpus import build,SEED
from live import construction,formal as live_formal

def run_large(cases):
    acc={a:{'hits':0,'latencies':[],'wrong':0,'authority':0,'mismatch':0} for a in ('wait','current','temporal')}
    h=hashlib.sha256()
    for c in cases:
        cs=current_only_select(c);ts=temporal_select(c)
        oc=select_current(c.history);ot=select_temporal(c.history)
        if set(cs)!=oc: acc['current']['mismatch']+=1
        if set(ts)!=ot: acc['temporal']['mismatch']+=1
        for arm,sel in [('current',cs),('temporal',ts)]:
            hit,olat=expected(set(sel),c.realized)
            lat=virtual_effect_latency_ns(sel,c.realized)
            if lat!=olat:acc[arm]['mismatch']+=1
            acc[arm]['hits']+=int(hit);acc[arm]['latencies'].append(lat)
        acc['wait']['latencies'].append(31_000_000)
        h.update(f'{c.case_id}:{c.category}:{c.realized}:{cs}:{ts}'.encode())
    out={}
    for arm,d in acc.items():
        xs=d.pop('latencies');out[arm]={**d,'mean_latency_ns':sum(xs)/len(xs),'p50_latency_ns':statistics.median(xs),'cases':len(xs)}
    out['digest']=h.hexdigest();return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--construction',action='store_true');ap.add_argument('--out');a=ap.parse_args()
    if a.construction:
        rows=construction();print(json.dumps({'construction':True,'live':rows},indent=2));return
    if not a.out:raise SystemExit('--out required')
    p=Path(a.out)
    if p.exists():raise SystemExit('result exists')
    cases=build();t0=time.perf_counter_ns();large=run_large(cases);large_wall=time.perf_counter_ns()-t0
    live=live_formal(cases)
    by={arm:[r['latency_ns'] for r in live if r['arm']==arm] for arm in ('wait','current','temporal')}
    live_summary={arm:{'n':len(xs),'median_latency_ns':statistics.median(xs),'p95_latency_ns':sorted(xs)[int(.95*(len(xs)-1))]} for arm,xs in by.items()}
    result={'task':'TEMPORAL-SPECULATION-PLANNER-GAP-RUNG1-20260918-001','seed':SEED,'formal_invocations':1,'reruns':0,'cases':len(cases),'large':large,'large_wall_ns':large_wall,'live_rows':live,'live_summary':live_summary,'authority_grants':0,'model_calls':0,'gui_actions':0,'task_input_actions':0}
    p.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True))
if __name__=='__main__':main()
