#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
ORDER=[0,12,1]
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    arms=[]
    for ms in ORDER:
        p=a.root/f'{ms:02d}ms'/'report.json'
        if not p.is_file(): raise SystemExit(f'missing {p}')
        row=json.loads(p.read_text()); arms.append(row)
    by={int(r['pacing_ms']):r for r in arms}
    controls=all(r['transport_passed'] and r['release_verified'] and r['stale_zero_injected_events'] for r in arms)
    positive=by[1]['semantic_passed'] and by[12]['semantic_passed'] and by[1]['eligible'] and by[12]['eligible']
    if not controls: disposition='FAIL_CONTROL_GATE'
    elif not by[12]['semantic_passed']: disposition='FAIL_12MS_POSITIVE_CONTROL'
    elif not by[1]['semantic_passed']: disposition='FAIL_NATIVE_1MS_TRANSFER'
    elif by[0]['semantic_passed']: disposition='TRANSFER_PASS_WITH_0MS_COUNTEREVIDENCE'
    else: disposition='TRANSFER_PASS_NATIVE_TIGHT_1MS'
    d12=by[12]['edit_elapsed_ns']; d1=by[1]['edit_elapsed_ns']; delta=d12-d1
    result={'schema':'agent-interface/native-x11-tight-text-pacing-aggregate-v1','formal_order':ORDER,'complete':len(arms)==3,'controls_passed':controls,'positive_controls_passed':positive,'zero_ms_semantic_passed':by[0]['semantic_passed'],'disposition':disposition,'arm_summary':[{'pacing_ms':r['pacing_ms'],'exact_count':r['exact_count'],'eligible':r['eligible'],'edit_elapsed_ns':r['edit_elapsed_ns'],'median_char_call_ns':r['median_char_call_ns'],'median_char_start_interval_ns':r['median_char_start_interval_ns'],'output_xlsx_sha256':r['output_xlsx_sha256']} for r in arms],'one_vs_twelve_delta_ns':delta,'one_vs_twelve_reduction_pct':(100.0*delta/d12 if d12 else None)}
    result['formal_pass']=controls and positive
    a.out.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2)); return 0 if result['formal_pass'] else 1
if __name__=='__main__': raise SystemExit(main())
