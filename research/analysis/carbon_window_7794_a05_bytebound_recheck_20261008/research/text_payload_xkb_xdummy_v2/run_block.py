import argparse,json,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--plan',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False);rows=[]
for i in range(3):
 d=a.out/f'arm-{i:02d}';q=subprocess.run([sys.executable,str(Path(__file__).with_name('run_arm.py')),'--out',str(d),'--plan',str(a.plan),'--index',str(i)],text=True,capture_output=True,timeout=25);(a.out/f'arm-{i:02d}.stdout').write_text(q.stdout);(a.out/f'arm-{i:02d}.stderr').write_text(q.stderr)
 if (d/'result.json').exists(): r=json.loads((d/'result.json').read_text())
 else: r={'decision':'HARNESS_FAIL','error':'NO_RESULT','input_operations':0,'startup':False}
 r['process_returncode']=q.returncode;rows.append(r)
ds=[r.get('decision','HARNESS_FAIL') for r in rows]
if all(x=='PASS_XDUMMY_NATIVE_XKB_MAP_SCOPED' for x in ds): decision='PASS_XDUMMY_NATIVE_XKB_MAP_SCOPED'
elif all(x=='SETUP_BLOCKED_XDUMMY' for x in ds): decision='SETUP_BLOCKED_XDUMMY'
elif all(x=='SETUP_BLOCKED_NATIVE_XKB_APPLY' for x in ds): decision='SETUP_BLOCKED_NATIVE_XKB_APPLY'
elif any(x=='HARNESS_FAIL' for x in ds): decision='HARNESS_FAIL'
else: decision='FAIL_INTEGRITY'
s={'schema':'agent-interface/xkb-xdummy-block-v2','decision':decision,'arms':3,'arm_decisions':ds,'input_operations':sum(r.get('input_operations',0) for r in rows),'formal_reruns':0};(a.out/'summary.json').write_text(json.dumps(s,indent=2,sort_keys=True)+'\n');print(json.dumps(s));raise SystemExit(0 if decision not in ('FAIL_INTEGRITY','HARNESS_FAIL') else 2)
