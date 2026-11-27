from pathlib import Path
import hashlib, json, os, platform, statistics, sys, time
from runtime.guarded_x11_v1 import receipt_journal as module
from runtime.guarded_x11_v1.receipt_journal import ReceiptJournal

ROOT = Path(__file__).resolve().parents[3]
CANDIDATE = ROOT / 'research/integration/calc_g10_mcp_profile_candidate_20261115/raw/standard-caller-journal-mode-20261116/run'
sources = list(CANDIDATE.rglob('retention.jsonl'))
if len(sources) != 1:
    raise SystemExit(f'expected one source retention journal, found {len(sources)}')
source = sources[0]
source_bytes = source.read_bytes()
rows = [json.loads(line) for line in source_bytes.splitlines()]
if len(rows) != 38:
    raise SystemExit(f'expected 38 retained records, got {len(rows)}')

class TimedStream:
    def __init__(self, inner, stats): self.inner, self.stats = inner, stats
    def write(self, value):
        t=time.perf_counter_ns()
        try: return self.inner.write(value)
        finally: self.stats['write_ns'] += time.perf_counter_ns()-t
    def flush(self):
        t=time.perf_counter_ns()
        try: return self.inner.flush()
        finally: self.stats['flush_ns'] += time.perf_counter_ns()-t
    def __getattr__(self, name): return getattr(self.inner, name)

original_canonical=module._canonical
original_fsync=module.os.fsync
repeats=[]
try:
    for run in range(1,4):
        target=Path(__file__).resolve().parent/'raw'/f'repeat-{run}'/'retention.jsonl'
        target.parent.mkdir(parents=True,exist_ok=False)
        stats={'canonical_ns':0,'canonical_calls':0,'write_ns':0,'flush_ns':0,'fsync_ns':0,'fsync_calls':0}
        def timed_canonical(value):
            t=time.perf_counter_ns()
            try:return original_canonical(value)
            finally:
                stats['canonical_ns'] += time.perf_counter_ns()-t
                stats['canonical_calls'] += 1
        def timed_fsync(fd):
            t=time.perf_counter_ns()
            try:return original_fsync(fd)
            finally:
                stats['fsync_ns'] += time.perf_counter_ns()-t
                stats['fsync_calls'] += 1
        journal=ReceiptJournal(target)
        journal._stream=TimedStream(journal._stream,stats)
        module._canonical=timed_canonical
        module.os.fsync=timed_fsync
        append_rows=[]
        try:
            for row in rows:
                stats.update(canonical_ns=0,canonical_calls=0,write_ns=0,flush_ns=0,fsync_ns=0,fsync_calls=0)
                start=time.perf_counter_ns()
                journal.append(row['reference'],row['kind'],row['payload'])
                elapsed=time.perf_counter_ns()-start
                append_rows.append({'sequence':row['sequence'],'reference':row['reference'],
                    'payload_bytes':len(original_canonical(row['payload'])),
                    'elapsed_ns':elapsed,**stats})
        finally:
            module._canonical=original_canonical
            module.os.fsync=original_fsync
            journal.close()
        raw=target.read_bytes()
        written=[json.loads(line) for line in raw.splitlines()]
        if len(written)!=len(rows): raise RuntimeError('record count changed')
        with ReceiptJournal(target) as verify:
            for row in rows:
                if verify.lookup(row['reference'])!=row['payload']:
                    raise RuntimeError('receipt readback mismatch: '+row['reference'])
        repeats.append({'repeat':run,'journal_path':str(target.relative_to(Path(__file__).resolve().parent)),
            'journal_bytes':len(raw),'journal_sha256':hashlib.sha256(raw).hexdigest(),
            'append_elapsed_ns':sum(x['elapsed_ns'] for x in append_rows),
            'component_totals':{k:sum(x[k] for x in append_rows) for k in
                ('canonical_ns','write_ns','flush_ns','fsync_ns','fsync_calls','canonical_calls')},
            'records':append_rows})
finally:
    module._canonical=original_canonical
    module.os.fsync=original_fsync

summary={
 'schema':'receipt-journal-phase-attribution-v1',
 'source_sha256':hashlib.sha256(source_bytes).hexdigest(),'source_bytes':len(source_bytes),
 'record_count':len(rows),'python':sys.version,'platform':platform.platform(),
 'measurement':'Real ReceiptJournal.append on replayed retained payloads; fsync remains enabled. Instrumented canonical serialization, stream write/flush, and fsync wall time. Each output was scanned and every reference/payload read back.',
 'repeats':repeats,
 'median_append_total_ns':statistics.median(x['append_elapsed_ns'] for x in repeats),
 'medians':{key:statistics.median(x['component_totals'][key] for x in repeats) for key in
     ('canonical_ns','write_ns','flush_ns','fsync_ns','fsync_calls','canonical_calls')}
}
out=Path(__file__).resolve().parent/'raw'/'RESULT.json'
out.write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ('repeats',)},indent=2))
