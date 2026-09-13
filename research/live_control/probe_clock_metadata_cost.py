"""Paired local serialization cost of clock ID fields on the same recorded events."""
import gc,hashlib,json,platform,statistics,sys,time
from pathlib import Path
from timing_clock import describe
HERE=Path(__file__).resolve().parent;out=HERE/'results/clock-metadata-cost-01';out.mkdir(exist_ok=False)
source=HERE/'results/timing-clock-live-01/runtime/events.jsonl'
records=[json.loads(line) for line in source.read_text().splitlines()]
assert records and all(isinstance(r.get('clock_domain_id'),str) for r in records)
plain=[{k:v for k,v in r.items() if k!='clock_domain_id'} for r in records]
assert all(dict(a,clock_domain_id=b['clock_domain_id'])==b for a,b in zip(plain,records))
variants={'without_clock_id':plain,'with_clock_id':records}
def encode(rows):return [(json.dumps(r)+'\n').encode() for r in rows]
payloads={name:encode(rows) for name,rows in variants.items()}
byte_counts={name:sum(map(len,payload)) for name,payload in payloads.items()}
rounds=[];repeats=300
# Warm both paths; use alternating order and keep one sample per paired round.
for rows in variants.values():
    for i in range(10):encode(rows)
for round_id in range(16):
    names=list(variants)
    if round_id%2:names.reverse()
    sample=dict(round=round_id,order=names,encode={},decode={})
    for name in names:
        gc.collect();cpu=time.process_time_ns();wall=time.perf_counter_ns()
        for i in range(repeats):encode(variants[name])
        sample['encode'][name]=dict(cpu_ns_per_record=(time.process_time_ns()-cpu)/(repeats*len(records)),wall_ns_per_record=(time.perf_counter_ns()-wall)/(repeats*len(records)))
        cpu=time.process_time_ns();wall=time.perf_counter_ns()
        for i in range(repeats):
            for line in payloads[name]:json.loads(line)
        sample['decode'][name]=dict(cpu_ns_per_record=(time.process_time_ns()-cpu)/(repeats*len(records)),wall_ns_per_record=(time.perf_counter_ns()-wall)/(repeats*len(records)))
    rounds.append(sample)
description=[]
for i in range(100):
    started=time.perf_counter_ns();clock=describe();description.append(time.perf_counter_ns()-started)
    assert clock['status']=='identified'
summary=dict(events=len(records),repeats_per_round=repeats,paired_rounds=len(rounds),bytes=byte_counts,
    added_bytes=byte_counts['with_clock_id']-byte_counts['without_clock_id'],
    added_percent=100*(byte_counts['with_clock_id']/byte_counts['without_clock_id']-1),
    median_cpu_ns_per_record={phase:{name:statistics.median(r[phase][name]['cpu_ns_per_record'] for r in rounds) for name in variants} for phase in ('encode','decode')},
    median_paired_cpu_delta_ns_per_record={phase:statistics.median(r[phase]['with_clock_id']['cpu_ns_per_record']-r[phase]['without_clock_id']['cpu_ns_per_record'] for r in rounds) for phase in ('encode','decode')},
    describe_median_wall_ns=statistics.median(description),describe_max_wall_ns=max(description),
    python=sys.version,platform=platform.platform(),
    scope='same recorded raw events; local JSON encode/decode and warm proc metadata reads only; no live capture, delivery projection, disk flush, model token or end-to-end measurement')
(out/'results.json').write_text(json.dumps(summary,indent=2)+'\n')
(out/'samples.json').write_text(json.dumps(dict(rounds=rounds,describe_ns=description),indent=2)+'\n')
(out/'sources.json').write_text(json.dumps({str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),HERE/'timing_clock.py',source)},indent=2)+'\n')
print(json.dumps(summary,indent=2))
