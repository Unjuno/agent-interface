#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,statistics
from pathlib import Path
CONDITIONS=[0.8,0.9,1.0,1.1]
BATCHES=range(1,6)
def key(ms): return f'{int(round(ms*1000)):04d}us'
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    receipts=[]; rows=[]
    for batch in BATCHES:
        bdir=a.root/f'batch-{batch:02d}'
        rp=bdir/'batch-receipt.json'
        if not rp.is_file(): raise SystemExit(f'missing {rp}')
        receipt=json.loads(rp.read_text()); receipts.append(receipt)
        if receipt.get('complete') is not True: raise SystemExit(f'incomplete batch {batch}')
        for ms in CONDITIONS:
            p=bdir/key(ms)/'report.json'
            if not p.is_file(): raise SystemExit(f'missing {p}')
            r=json.loads(p.read_text()); r['batch']=batch; rows.append(r)
    controls=all(r['transport_passed'] and r['release_verified'] and r['stale_zero_injected_events'] for r in rows)
    summary=[]
    for ms in CONDITIONS:
        rs=[r for r in rows if abs(float(r['pacing_ms'])-ms)<1e-9]
        summary.append({'pacing_ms':ms,'sessions':len(rs),'eligible_sessions':sum(bool(r['eligible']) for r in rs),'exact_sessions':sum(int(r['exact_count'])==16 for r in rs),'total_exact_strings':sum(int(r['exact_count']) for r in rs),'median_char_start_interval_ns':statistics.median(int(r['median_char_start_interval_ns']) for r in rs),'min_char_start_interval_ns':min(int(r['median_char_start_interval_ns']) for r in rs),'max_char_start_interval_ns':max(int(r['median_char_start_interval_ns']) for r in rs),'median_edit_elapsed_ns':statistics.median(int(r['edit_elapsed_ns']) for r in rs),'output_sha256':[r['output_xlsx_sha256'] for r in rs]})
    candidates=[x['pacing_ms'] for x in summary if x['sessions']==5 and x['eligible_sessions']==5 and x['exact_sessions']==5]
    robust=min(candidates) if candidates else None
    result={'schema':'agent-interface/native-x11-subms-robustness-aggregate-v2','batch_count':len(receipts),'session_count':len(rows),'all_batches_complete':len(receipts)==5 and all(r.get('complete') is True for r in receipts),'controls_passed':controls,'condition_summary':summary,'robust_candidate_ms':robust,'disposition':('ROBUST_CANDIDATE' if controls and robust is not None else 'HOLD_NO_5_OF_5_CANDIDATE'),'formal_pass':controls and robust is not None}
    a.out.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2)); return 0 if result['formal_pass'] else 1
if __name__=='__main__': raise SystemExit(main())
