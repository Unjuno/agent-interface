"""Finite clock-domain check for the prospective capture-time adapter; no GUI input."""
import json,time,sys
rows=[]
for _ in range(128):
    before=time.perf_counter_ns();capture=time.monotonic_ns();after=time.perf_counter_ns()
    rows.append({'perf_before_ns':before,'monotonic_ns':capture,'perf_after_ns':after})
print(json.dumps({'python':sys.version,'clocks':{name:vars(time.get_clock_info(name)) for name in ('monotonic','perf_counter')},'rows':rows,'violations':[i for i,r in enumerate(rows) if not r['perf_before_ns']<=r['monotonic_ns']<=r['perf_after_ns']]}))
