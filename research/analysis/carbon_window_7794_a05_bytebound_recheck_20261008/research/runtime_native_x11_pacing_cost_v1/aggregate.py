#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,statistics
from pathlib import Path
MECHS=['busy','sleep','hybrid200']
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args(); rows={m:[] for m in MECHS}
 for b in range(1,7):
  br=a.root/f'batch-{b:02d}';receipt=json.loads((br/'batch-receipt.json').read_text())
  if not receipt.get('complete'):raise SystemExit(f'incomplete batch {b}')
  for m in MECHS:
   arm=br/m;report=json.loads((arm/'report.json').read_text());exe=json.loads((arm/'execution.json').read_text());score=json.loads((arm/'score.json').read_text())
   controls=bool(report.get('transport_passed') and report.get('release_verified') and report.get('stale_zero_injected_events') and exe.get('edit_process_cpu_ns',-1)>=0)
   eligible=bool(report.get('eligible') and score.get('passed') and score.get('exact_count')==16 and controls)
   rows[m].append({'batch':b,'eligible':eligible,'exact_count':score.get('exact_count'),'cpu_ns':exe.get('edit_process_cpu_ns'),'wall_ns':exe.get('edit_elapsed_ns'),'start_ns':exe.get('median_char_start_interval_ns'),'xlsx_sha256':score.get('output_xlsx_sha256') or report.get('output_xlsx_sha256'),'controls':controls})
 summary=[]
 for m in MECHS:
  rr=rows[m]; summary.append({'mechanism':m,'sessions':len(rr),'eligible_sessions':sum(x['eligible'] for x in rr),'exact_sessions':sum(x['exact_count']==16 for x in rr),'median_edit_process_cpu_ns':int(statistics.median(x['cpu_ns'] for x in rr)),'median_edit_elapsed_ns':int(statistics.median(x['wall_ns'] for x in rr)),'median_char_start_interval_ns':int(statistics.median(x['start_ns'] for x in rr)),'median_cpu_wall_ratio':statistics.median(x['cpu_ns']/x['wall_ns'] for x in rr),'sessions_detail':rr})
 by={x['mechanism']:x for x in summary};busy=by['busy'];eligible=[x for x in summary if x['mechanism']!='busy' and x['eligible_sessions']==6]
 for x in summary:
  x['cpu_vs_busy_ratio']=x['median_edit_process_cpu_ns']/busy['median_edit_process_cpu_ns'] if busy['median_edit_process_cpu_ns'] else None
  x['wall_vs_busy_ratio']=x['median_edit_elapsed_ns']/busy['median_edit_elapsed_ns'] if busy['median_edit_elapsed_ns'] else None
 lower=[x for x in eligible if x['median_edit_process_cpu_ns'] <= busy['median_edit_process_cpu_ns']*0.5]
 if busy['eligible_sessions']<6: disposition='FAIL_BUSY_REFERENCE'
 elif not eligible: disposition='FAIL_NONBUSY_CORRECTNESS'
 elif not lower: disposition='HOLD_NO_SUBSTANTIAL_CPU_REDUCTION'
 else: disposition='LOWER_CPU_EQUIVALENT_CORRECTNESS'
 preferred=min(lower,key=lambda x:x['median_edit_process_cpu_ns'])['mechanism'] if lower else None
 out={'schema':'agent-interface/native-x11-pacing-cost-aggregate-v1','batch_count':6,'session_count':18,'requested_pacing_ms':1.0,'all_complete':all(len(rows[m])==6 for m in MECHS),'mechanisms':summary,'preferred_low_cpu_candidate':preferred,'disposition':disposition,'formal_pass':disposition=='LOWER_CPU_EQUIVALENT_CORRECTNESS'}
 a.out.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2));return 0 if out['formal_pass'] else 1
if __name__=='__main__':raise SystemExit(main())
