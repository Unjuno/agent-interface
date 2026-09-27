import json
from pathlib import Path
for label,path in [('zero_gap',str(Path(__file__).with_name('zero-gap.jsonl'))),('two_ms',str(Path(__file__).with_name('two-ms.jsonl')))]:
    rows=[json.loads(l) for l in Path(path).read_bytes().splitlines()]
    calls=[r for r in rows if r['tool']=='native_submit']
    spans=[r['sdk_return_ns']-r['sdk_entry_ns'] for r in calls]
    gaps=[b['sdk_entry_ns']-a['sdk_return_ns'] for a,b in zip(calls,calls[1:])]
    assert all(n>=0 for n in spans+gaps)
    total=calls[-1]['sdk_return_ns']-calls[0]['sdk_entry_ns']
    assert total==sum(spans)+sum(gaps)
    print(json.dumps({'case':label,'submit_calls':len(calls),'sdk_ms':[v/1e6 for v in spans],'between_calls_ms':[v/1e6 for v in gaps],'entry_to_final_return_ms':total/1e6,'sdk_total_ms':sum(spans)/1e6,'outside_sdk_ms':sum(gaps)/1e6}))
