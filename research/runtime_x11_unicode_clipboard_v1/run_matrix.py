#!/usr/bin/env python3
import argparse,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False);rows=[]
 for app,disp in [('writer',':101'),('calc',':102')]:
  od=a.out/app;r=subprocess.run([sys.executable,str(HERE/'run_arm.py'),'--app',app,'--display',disp,'--out',str(od)],text=True,capture_output=True);(a.out/f'{app}.stdout').write_text(r.stdout);(a.out/f'{app}.stderr').write_text(r.stderr);rep=json.loads((od/'report.json').read_text());rep['runner_exitcode']=r.returncode;rows.append(rep)
 out={'schema':'agent-interface/x11-unicode-clipboard-matrix-v1','arms':rows,'both_scoped_pass':all(x['passed_scoped'] for x in rows),'owner_identity_restored_all':all(x['owner_identity_restored'] for x in rows),'owner_reclaimed_after_close_all':all(x['owner_reclaimed_after_close'] for x in rows),'disposition':'PASS_SCOPED_REQUIRES_EXPLICIT_CLIPBOARD_SIDE_EFFECT_CAPABILITY' if all(x['passed_scoped'] for x in rows) and not all(x['owner_identity_restored'] for x in rows) else 'OTHER'};(a.out/'aggregate.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2));return 0 if out['both_scoped_pass'] else 1
if __name__=='__main__':raise SystemExit(main())
