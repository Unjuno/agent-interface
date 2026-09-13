"""Two live Linux processes plus missing/mismatched interval controls."""
import copy,hashlib,json,subprocess,sys,time
from pathlib import Path
from timing_clock import describe,interval
HERE=Path(__file__).resolve().parent;out=HERE/'results/timing-clock-01';out.mkdir(exist_ok=False)
clock=describe();start=time.perf_counter_ns()
child=json.loads(subprocess.check_output([sys.executable,'-c',"import json,time;from timing_clock import describe;print(json.dumps(dict(clock=describe(),stamp=time.perf_counter_ns())))"],cwd=HERE,text=True))
end=time.perf_counter_ns();assert clock['status']=='identified' and child['clock']==clock
before=interval(start,clock,child['stamp'],child['clock']);after=interval(child['stamp'],child['clock'],end,clock)
assert before['status']==after['status']=='comparable'
changed=copy.deepcopy(clock);changed['domain']['boot_id']='different-boot'
cases=dict(missing_time=interval(None,clock,end,clock),missing_clock=interval(start,None,end,clock),
    different_domain=interval(start,clock,end,changed),bad_order=interval(end,clock,start,clock))
assert [v['status'] for v in cases.values()]==['missing_endpoint','missing_clock','different_clock_domain','ordering_error']
assert all(v['duration_ns'] is None for v in cases.values())
report=dict(parent_clock=clock,child=child,before=before,after=after,controls=cases)
(out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
(out/'sources.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),HERE/'timing_clock.py')},indent=2)+'\n')
print(json.dumps(dict(same_domain=True,ordered=True,controls=cases),indent=2))
