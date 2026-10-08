#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
ORDER=[0,12,1]
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); rows=[]; complete=True
 for p in ORDER:
  d=a.root/f'{p:02d}ms'; needed=[d/'report.json',d/'score.json',d/'execution'/'execution.json']
  if any(not x.exists() for x in needed): complete=False; rows.append({'pacing_ms':p,'complete':False,'eligible':False}); continue
  rep=json.loads((d/'report.json').read_text()); sc=json.loads((d/'score.json').read_text()); ex=json.loads((d/'execution'/'execution.json').read_text()); st=ex['stale']; eligible=(rep['executor_exitcode']==0 and rep['scorer_exitcode']==0 and sc['passed'] and ex['release_verified'] and st['accepted'] is False and st['error']=='STALE_OBSERVATION' and st['emissions_before']==st['emissions_after']); rows.append({'pacing_ms':p,'complete':True,'eligible':eligible,'mismatch_count':len(sc['mismatches']),'mismatches':sc['mismatches'],'task_elapsed_ns':ex['task_elapsed_ns'],'release_verified':ex['release_verified'],'backend_emissions':ex['backend_emissions'],'output_sha256':rep['output_sha256']})
 by={r['pacing_ms']:r for r in rows}; transfer=(complete and by[1]['eligible'] and by[12]['eligible'] and not by[0]['eligible']); disposition='TRANSFER_PASS' if transfer else ('UNCERTAIN_INCOMPLETE' if not complete else 'TRANSFER_REJECT')
 out={'schema':'agent-interface/writer-x11-pacing-transfer-v1','fixed_order':ORDER,'complete':complete,'rows':rows,'disposition':disposition}; a.out.write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2)); return 0 if disposition=='TRANSFER_PASS' else 1
if __name__=='__main__': raise SystemExit(main())
