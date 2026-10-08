"""Fixed same-receipt local cost check; no model, image rendering or GUI input."""
import importlib.util,json,statistics,time
from pathlib import Path
p=Path(__file__).resolve().parent
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,p/'source'/file)
    result=importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result
functions={'previous':module('previous','baseline_receipt_references.py').compact_native_receipt,
           'new':module('new','receipt_references.py').compact_native_receipt}
view=json.loads((p/'full-receipt.json').read_text())
for _ in range(10):
    for function in functions.values(): function(view)
samples=[]
for pair in range(100):
    order=('previous','new') if pair%2==0 else ('new','previous')
    for name in order:
        started=time.perf_counter_ns()
        result=functions[name](view)
        elapsed=time.perf_counter_ns()-started
        samples.append({'pair':pair,'arm':name,'elapsed_ns':elapsed})
summary={}
for name in functions:
    values=sorted(s['elapsed_ns']/1e6 for s in samples if s['arm']==name)
    summary[name]={'median_ms':statistics.median(values),'p95_ms':values[94], 'n':len(values)}
print(json.dumps({'scope':'warm same-receipt WSL process; projection only, not end-to-end',
                  'warmups_per_arm':10,'order':'alternating within 100 pairs',
                  'summary':summary,'samples':samples},indent=2))
