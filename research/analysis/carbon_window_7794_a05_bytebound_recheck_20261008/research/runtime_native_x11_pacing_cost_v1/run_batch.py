#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
DEP=HERE.parent/'runtime_native_x11_text_pacing_v1'
RUN_ARM=DEP/'run_arm.py'
ORDERS={1:['busy','sleep','hybrid200'],2:['sleep','hybrid200','busy'],3:['hybrid200','busy','sleep'],4:['busy','sleep','hybrid200'],5:['sleep','hybrid200','busy'],6:['hybrid200','busy','sleep']}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--batch',type=int,choices=range(1,7),required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--bin-dir',type=Path,required=True);a=ap.parse_args()
 if a.out.exists():raise SystemExit('batch output exists')
 a.out.mkdir(parents=True);rows=[];display=500+(a.batch-1)*3
 for mech in ORDERS[a.batch]:
  arm=a.out/mech;binary=a.bin_dir/f'{mech}-controller';disp=f':{display}';display+=1
  cp=subprocess.run([sys.executable,str(RUN_ARM),'--out',str(arm),'--display',disp,'--pacing-ms','1.0','--controller',str(binary)],text=True,capture_output=True)
  (a.out/f'{mech}.outer.stdout').write_text(cp.stdout);(a.out/f'{mech}.outer.stderr').write_text(cp.stderr);(a.out/f'{mech}.outer.exitcode').write_text(str(cp.returncode)+'\n')
  rows.append({'mechanism':mech,'display':disp,'outer_exitcode':cp.returncode,'report_exists':(arm/'report.json').is_file(),'execution_exists':(arm/'execution.json').is_file(),'score_exists':(arm/'score.json').is_file()})
 complete=all(r['report_exists'] and r['execution_exists'] and r['score_exists'] for r in rows)
 receipt={'schema':'agent-interface/native-x11-pacing-cost-batch-v1','batch':a.batch,'order':ORDERS[a.batch],'rows':rows,'complete':complete}
 (a.out/'batch-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2));return 0 if complete else 2
if __name__=='__main__':raise SystemExit(main())
