"""Matched offline output-path benchmark; regular-file sink is not model delivery."""
import hashlib,json,statistics,tempfile,time
from pathlib import Path
from delivery_ledger_v2 import DeliveryLedger as V2
from delivery_ledger_v3 import DeliveryLedger as V3
HERE=Path(__file__).resolve().parent
source=HERE/'results/servo-recovery-02/delivered.jsonl'
items=[json.loads(x) for x in source.read_text().splitlines()]
original=json.dumps(items,sort_keys=True)
out=HERE/'results/delivery-cost-01';out.mkdir(exist_ok=False)
rows=[]
for repetition in range(20):
    order=('off','v2','v3') if repetition%2==0 else ('v3','v2','off')
    for mode in order:
        ledger={'off':lambda:None,'v2':V2,'v3':V3}[mode]()
        with tempfile.TemporaryDirectory(prefix='delivery-cost-',dir=HERE/'results-local' if (HERE/'results-local').exists() else HERE) as temporary:
            root=Path(temporary)
            with (root/'sink').open('w') as sink:
                start=time.perf_counter_ns()
                for item in items:
                    visible=ledger.prepare(item) if ledger else item
                    rendered=json.dumps(visible)
                    with (root/'delivered').open('a') as stream:stream.write(rendered+'\n')
                    flush_start=time.perf_counter_ns()
                    print(rendered,file=sink,flush=True)
                    if ledger:
                        receipt=ledger.flushed(visible,len((rendered+'\n').encode()),flush_start)
                        with (root/'receipts').open('a') as stream:stream.write(json.dumps(receipt)+'\n')
                elapsed=(time.perf_counter_ns()-start)/1e6
            actual=[json.loads(x) for x in (root/'sink').read_text().splitlines()]
            if ledger:
                for x in actual:x.pop('delivery_id')
            assert actual==items
            rows.append(dict(repetition=repetition,mode=mode,elapsed_ms=elapsed,
                             output_bytes=(root/'sink').stat().st_size,
                             receipt_bytes=(root/'receipts').stat().st_size if ledger else 0,
                             retained_records=len(ledger.records) if ledger else 0))
assert json.dumps(items,sort_keys=True)==original
# Eviction must reject evidence while retaining a newer receipt with reused image.
ledger=V3(2)
for seq in (1,2,3):
    item=ledger.prepare(dict(event='observation',sequence=seq,image='same.png',capture_ns=seq,image_reused=seq>1))
    ledger.flushed(item,1,time.perf_counter_ns())
assert len(ledger.records)==2
try:ledger.validate(dict(delivery_id='delivery:1',observation_sequence=1,producer='scripted'))
except ValueError:pass
else:raise AssertionError('evicted evidence accepted')
assert ledger.validate(dict(delivery_id='delivery:3',observation_sequence=3,producer='scripted'))['image']=='same.png'
summary={mode:dict(median_ms=statistics.median(r['elapsed_ms'] for r in rows if r['mode']==mode),
                   receipt_bytes_range=[min(r['receipt_bytes'] for r in rows if r['mode']==mode),max(r['receipt_bytes'] for r in rows if r['mode']==mode)]) for mode in ('off','v2','v3')}
summary['paired_deltas_ms']={mode:statistics.median(next(r['elapsed_ms'] for r in rows if r['mode']==mode and r['repetition']==i)-next(r['elapsed_ms'] for r in rows if r['mode']=='off' and r['repetition']==i) for i in range(20)) for mode in ('v2','v3')}
(out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n')
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
paths=[Path(__file__),HERE/'delivery_ledger_v2.py',HERE/'delivery_ledger_v3.py',source]
(out/'sources.json').write_text(json.dumps({str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2)+'\n')
print(json.dumps(summary,indent=2))
