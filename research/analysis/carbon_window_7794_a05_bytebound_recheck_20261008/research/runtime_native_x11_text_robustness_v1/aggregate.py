#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,statistics
from pathlib import Path
CONDITIONS=[0.8,0.9,1.0,1.1]
ROUNDS=5

def key(ms): return f'{int(round(ms*1000)):04d}us'
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    rows=[]
    for rnd in range(1,ROUNDS+1):
        for ms in CONDITIONS:
            p=a.root/f'r{rnd:02d}'/key(ms)/'report.json'
            if not p.is_file(): raise SystemExit(f'missing {p}')
            r=json.loads(p.read_text()); r['round']=rnd; rows.append(r)
    controls=all(r['transport_passed'] and r['release_verified'] and r['stale_zero_injected_events'] for r in rows)
    cond=[]
    for ms in CONDITIONS:
        rs=[r for r in rows if abs(float(r['pacing_ms'])-ms)<1e-9]
        cond.append({'pacing_ms':ms,'sessions':len(rs),'eligible_sessions':sum(bool(r['eligible']) for r in rs),'exact_sessions':sum(int(r['exact_count'])==16 for r in rs),'total_exact_strings':sum(int(r['exact_count']) for r in rs),'median_char_start_interval_ns':statistics.median(int(r['median_char_start_interval_ns']) for r in rs),'min_char_start_interval_ns':min(int(r['median_char_start_interval_ns']) for r in rs),'max_char_start_interval_ns':max(int(r['median_char_start_interval_ns']) for r in rs),'median_edit_elapsed_ns':statistics.median(int(r['edit_elapsed_ns']) for r in rs),'output_sha256':[r['output_xlsx_sha256'] for r in rs]})
    candidates=[c['pacing_ms'] for c in cond if c['eligible_sessions']==ROUNDS and c['exact_sessions']==ROUNDS]
    robust=min(candidates) if candidates else None
    result={'schema':'agent-interface/native-x11-subms-robustness-aggregate-v1','conditions':CONDITIONS,'rounds':ROUNDS,'session_count':len(rows),'controls_passed':controls,'condition_summary':cond,'robust_candidate_ms':robust,'disposition':('ROBUST_CANDIDATE' if controls and robust is not None else 'HOLD_NO_5_OF_5_CANDIDATE'),'formal_pass':controls and robust is not None}
    a.out.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2)); return 0 if result['formal_pass'] else 1
if __name__=='__main__': raise SystemExit(main())
