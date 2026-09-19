"""Matched receipt persistence replay and injected I/O failures, no GUI input."""
import hashlib,io,json,statistics,tempfile,time
from pathlib import Path
from receipt_journal import ReceiptJournal

HERE=Path(__file__).resolve().parent
source=HERE/'results/delivery-self-use-02/delivery-flush.jsonl'
records=[json.loads(line) for line in source.read_text().splitlines()]
expected=b''.join((json.dumps(r)+'\n').encode() for r in records)
out=HERE/'results/receipt-journal-01';out.mkdir(exist_ok=False)
rows=[]
for block in range(20):
    for mode in (('reopen','persistent') if block%2==0 else ('persistent','reopen')):
        with tempfile.TemporaryDirectory(prefix='receipt-cost-',dir=HERE) as temporary:
            path=Path(temporary)/'receipts.jsonl'
            start=time.perf_counter_ns()
            if mode=='persistent':
                journal=ReceiptJournal(path.open('xb'))
                try:
                    for record in records:journal.append(record)
                finally:journal.close()
                assert journal.confirmed==len(records)
            else:
                for record in records:
                    with path.open('ab') as stream:
                        data=(json.dumps(record)+'\n').encode()
                        assert stream.write(data)==len(data)
                        stream.flush()
            elapsed=(time.perf_counter_ns()-start)/1e6
            assert path.read_bytes()==expected
            rows.append(dict(block=block,mode=mode,elapsed_ms=elapsed,bytes=len(expected)))

class Fault(io.BytesIO):
    def __init__(self,kind):super().__init__();self.kind=kind
    def write(self,data):
        if self.kind=='write':raise OSError('injected write failure')
        if self.kind=='short':return super().write(data[:3])
        return super().write(data)
    def flush(self):
        if self.kind=='flush':raise OSError('injected flush failure')
        return super().flush()

failures={}
for kind in ('write','short','flush'):
    stream=Fault(kind);journal=ReceiptJournal(stream)
    try:journal.append(records[0])
    except OSError as exc:failures[kind]=str(exc)
    else:raise AssertionError(kind)
    assert journal.failed and journal.confirmed==0
    size=len(stream.getvalue())
    try:journal.append(records[1])
    except RuntimeError:pass
    else:raise AssertionError('failure was not sticky')
    assert len(stream.getvalue())==size
    journal.close()
journal=ReceiptJournal(io.BytesIO());journal.close();journal.close()
try:journal.append(records[0])
except RuntimeError:pass
else:raise AssertionError('append after close')
delta=[next(r['elapsed_ms'] for r in rows if r['block']==b and r['mode']=='persistent')-next(r['elapsed_ms'] for r in rows if r['block']==b and r['mode']=='reopen') for b in range(20)]
summary=dict(records=len(records),bytes=len(expected),blocks=20,
             median_ms={m:statistics.median(r['elapsed_ms'] for r in rows if r['mode']==m) for m in ('reopen','persistent')},
             paired_delta_median_ms=statistics.median(delta),paired_delta_range_ms=[min(delta),max(delta)],
             persistent_faster_blocks=sum(d<0 for d in delta),faults=failures)
(out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n')
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
(out/'sources.json').write_text(json.dumps({str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),HERE/'receipt_journal.py',source)},indent=2)+'\n')
print(json.dumps(summary,indent=2))
