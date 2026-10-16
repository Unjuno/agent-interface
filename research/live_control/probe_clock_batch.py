"""Exact roundtrip and comparable JSON byte accounting, not token measurement."""
import copy,hashlib,json
from pathlib import Path
from clock_batch import pack,unpack
HERE=Path(__file__).resolve().parent;out=HERE/'results/clock-batch-01';out.mkdir(exist_ok=False)
source=HERE/'results/timing-clock-live-01/runtime/events.jsonl'
records=[json.loads(line) for line in source.read_text().splitlines()]
batch=pack(records);assert unpack(batch)==records
before=json.dumps(records).encode();after=json.dumps(batch).encode()
unknown=[dict(event='test',clock_domain_id=None)];assert unpack(pack(unknown))==unknown
assert unpack(pack([]))==[]
for case in ('mixed','missing','duplicate_field','bad_schema'):
    try:
        if case=='mixed':
            changed=copy.deepcopy(records);changed[-1]['clock_domain_id']='different';pack(changed)
        elif case=='missing':pack([dict(event='test')])
        elif case=='duplicate_field':
            changed=copy.deepcopy(batch);changed['records'][0]['clock_domain_id']='different';unpack(changed)
        else:unpack(dict(batch,unexpected=True))
    except ValueError:pass
    else:raise AssertionError(case)
copy_batch=pack(records);copy_batch['records'][0]['event']='changed';assert records[0]['event']!='changed'
restored=unpack(batch);restored[0]['event']='changed';assert batch['records'][0]['event']!='changed'
summary=dict(exact_records=len(records),original_json_array_bytes=len(before),packed_json_bytes=len(after),saved_bytes=len(before)-len(after),
    saved_percent=100*(1-len(after)/len(before)),unknown_and_empty_preserved=True,negative_controls=4,mutation_isolated=True,
    scope='offline raw-record JSON batch prototype; no live transport, JSON CPU, model tokens or total latency measured')
(out/'results.json').write_text(json.dumps(summary,indent=2)+'\n')
(out/'sources.json').write_text(json.dumps({str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),HERE/'clock_batch.py',source)},indent=2)+'\n')
print(json.dumps(summary,indent=2))
