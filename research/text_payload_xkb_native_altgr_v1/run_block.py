import argparse,json,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False);ds=[]
for i in range(3):
 d=a.out/f'rep-{i}';q=subprocess.run([sys.executable,str(Path(__file__).with_name('run_arm.py')),'--rep',str(i),'--out',str(d)],capture_output=True,text=True,timeout=35);(a.out/f'rep-{i}.stdout').write_text(q.stdout);(a.out/f'rep-{i}.stderr').write_text(q.stderr);r=json.loads((d/'report.json').read_text()) if (d/'report.json').exists() else {'decision':'HARNESS_FAIL'};ds.append(r.get('decision','HARNESS_FAIL'))
dec='PASS_XDUMMY_NATIVE_ALTGR_DELIVERY_SCOPED' if all(x=='PASS_XDUMMY_NATIVE_ALTGR_DELIVERY_SCOPED' for x in ds) else ('HARNESS_FAIL' if any(x=='HARNESS_FAIL' for x in ds) else 'FAIL_DELIVERY');o={'decision':dec,'arm_decisions':ds,'repetitions':3,'trials':48,'formal_reruns':0};(a.out/'summary.json').write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(json.dumps(o));raise SystemExit(0 if dec=='PASS_XDUMMY_NATIVE_ALTGR_DELIVERY_SCOPED' else 2)
