#!/usr/bin/env python3
import argparse,json,hashlib
from pathlib import Path

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--evidence',required=True);a=ap.parse_args();root=Path(a.root);ev=Path(a.evidence);sched=json.loads((root/'schedule.json').read_text())['cases'];rows=json.loads((ev/'ledger.json').read_text());errors=[];counts={'macro_stable':0,'macro_stale_before_call':0};passes={k:0 for k in counts}
 if len(rows)!=len(sched): errors.append('ledger_len')
 for i,s in enumerate(sched):
  if i>=len(rows):break
  row=rows[i];counts[s]+=1
  if row.get('index')!=i or row.get('scenario')!=s or row.get('returncode')!=0:errors.append(f'{i}:row');continue
  r=row['result'];events=json.loads((ev/row['case_id']/'events.json').read_text());names=[x['event'] for x in events];expected=['fixture_ready']+(['external_write_complete'] if s=='macro_stale_before_call' else [])+['macro_complete']
  if names!=expected:errors.append(f'{i}:events={names}')
  if r.get('final_b_x')!=5000 or r.get('case_gate_pass') is not True:errors.append(f'{i}:gate')
  mr=r.get('macro_return') or {}
  if s=='macro_stable':
   if not (mr.get('status')=='APPLIED' and mr.get('before_x')==1000 and mr.get('after_x')==1200 and r.get('final_a_x')==1200):errors.append(f'{i}:stable')
  else:
   ej=(r.get('external') or {}).get('json') or {}
   if not (ej.get('after_x')==1700 and mr.get('status')=='REFUSED' and mr.get('before_x')==1700 and r.get('final_a_x')==1700 and r['external']['parent_end_ns'] < r['macro_start_ns']):errors.append(f'{i}:stale')
  passes[s]+=int(r.get('case_gate_pass') is True)
 if counts!={'macro_stable':5,'macro_stale_before_call':5}:errors.append(f'counts={counts}')
 outcome='PASS_COOPERATIVE_CONDITIONAL_CALL_SCOPED' if not errors else 'AUDIT_FAIL';rep={'audit_pass':not errors,'outcome':outcome,'counts':counts,'passes':passes,'errors':errors,'source_sha256':{f:sha(root/f) for f in ['conditional_macro.py','external_writer.py','run_case.py','run_block.py','audit.py','schedule.json','prereg.json']}};(ev/'audit.json').write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n');print(json.dumps(rep,indent=2,sort_keys=True));return 0 if not errors else 2
if __name__=='__main__':raise SystemExit(main())
