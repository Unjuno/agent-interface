from pathlib import Path
import hashlib,json,statistics,time,platform,sys
from runtime.guarded_x11_v1.receipt_journal import ReceiptJournal
base=Path('research/integration/calc_g10_mcp_profile_candidate_20261115/raw')
src=base/'standard-caller-journal-mode-20261116/run/guarded-session-02c71830faba4f72be77d135bc11d5ea/retention.jsonl'
if not src.exists():
    matches=list((base/'standard-caller-journal-mode-20261116/run').rglob('retention.jsonl'))
    if len(matches)!=1: raise RuntimeError(f'expected unique source journal, found {len(matches)}')
    src=matches[0]
raw=src.read_bytes(); rows=[json.loads(line) for line in raw.splitlines()]
out=Path(__file__).resolve().parent/'rerun'; out.mkdir(exist_ok=False)
target=out/'replayed-retention.jsonl'; timings=[]; journal=ReceiptJournal(target)
try:
    for row in rows:
        started=time.perf_counter_ns()
        journal.append(row['reference'],row['kind'],row['payload'])
        elapsed=time.perf_counter_ns()-started
        timings.append({'sequence':row['sequence'],'reference':row['reference'],'kind':row['kind'],'append_elapsed_ns':elapsed})
finally: journal.close()
summary={'schema':'receipt-journal-append-microbench-v1','source_journal_sha256':hashlib.sha256(raw).hexdigest(),'source_journal_bytes':len(raw),'records':len(rows),'python':sys.version,'platform':platform.platform(),'timings':timings,'summary':{'append_total_ns':sum(x['append_elapsed_ns'] for x in timings),'append_median_ns':statistics.median(x['append_elapsed_ns'] for x in timings),'append_p95_ns':sorted(x['append_elapsed_ns'] for x in timings)[int(.95*(len(timings)-1))],'append_min_ns':min(x['append_elapsed_ns'] for x in timings),'append_max_ns':max(x['append_elapsed_ns'] for x in timings),'final_journal_bytes':target.stat().st_size}}
(out/'RESULT.json').write_text(json.dumps(summary,indent=2)+'\n')
