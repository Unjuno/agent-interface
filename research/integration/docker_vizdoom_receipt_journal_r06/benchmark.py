import json,time
from pathlib import Path
from receipt_journal import ReceiptJournal
PAYLOADS=Path('/payloads')
OUT=Path('/output')
FILES=sorted(PAYLOADS.glob('compiled-*.json'))
VALUES=[(p.name,json.loads(p.read_text(encoding='utf-8'))) for p in FILES]
if len(VALUES)!=19: raise SystemExit(f'expected 19 receipts, got {len(VALUES)}')
methods=['pretty_files','hash_linked_jsonl']
rows=[]
for rep in range(10):
    order=methods if rep%2==0 else list(reversed(methods))
    for method in order:
        root=OUT/f'{method}-rep{rep:02d}'
        root.mkdir(parents=True,exist_ok=False)
        serialize_ns=0;write_ns=0;started=time.perf_counter_ns()
        if method=='pretty_files':
            refs=[]
            for name,value in VALUES:
                t=time.perf_counter_ns();text=json.dumps(value,indent=2,ensure_ascii=False)+'\n';serialize_ns+=time.perf_counter_ns()-t
                path=root/name
                t=time.perf_counter_ns();path.write_text(text,encoding='utf-8',newline='\n');write_ns+=time.perf_counter_ns()-t;refs.append(name[:-5])
            append_ns=time.perf_counter_ns()-started
            t=time.perf_counter_ns();restored={p.name[:-5]:json.loads(p.read_text(encoding='utf-8')) for p in sorted(root.glob('*.json'))};readback_ns=time.perf_counter_ns()-t
        else:
            journal_path=root/'receipts.jsonl';journal=ReceiptJournal(journal_path);refs=[]
            t=time.perf_counter_ns()
            for name,value in VALUES:
                ref=name[:-5];kind=name[:-5].rsplit('-',1)[-1]
                journal.append(ref,kind,value);refs.append(ref)
            append_ns=time.perf_counter_ns()-t
            serialize_ns=None;write_ns=None
            t=time.perf_counter_ns();reopened=ReceiptJournal(journal_path);restored={ref:reopened.lookup(ref) for ref in refs};readback_ns=time.perf_counter_ns()-t
        if len(restored)!=len(VALUES) or any(restored[name[:-5]]!=value for name,value in VALUES):
            raise RuntimeError(f'payload lookup mismatch: {method} repetition {rep}')
        total_ns=append_ns+readback_ns
        bytes_out=sum(p.stat().st_size for p in root.iterdir() if p.is_file())
        rows.append({'rep':rep,'method':method,'order_index':order.index(method),'records':19,'append_ns':append_ns,'readback_ns':readback_ns,'total_ns':total_ns,'serialize_ns':serialize_ns,'write_ns':write_ns,'bytes':bytes_out,'all_payloads_equal':True})
result={'schema':'agent-interface/receipt-journal-live-payload-benchmark-r06','payload_count':19,'repetitions_per_method':10,'rows':rows,'scope':'receipt persistence and verified reference lookup only; no GUI/input/task effect; no fsync; single writer'}
(OUT/'benchmark-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(result,sort_keys=True))