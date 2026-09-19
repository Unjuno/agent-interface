from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--plan',type=Path,required=True); a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=False)
    rows=[]
    for i in range(3):
        arm=a.out/f'arm-{i:02d}'
        c=['xvfb-run','-a','-s','-screen 0 800x600x24',sys.executable,str(Path(__file__).with_name('run_arm.py')),'--out',str(arm),'--plan',str(a.plan)]
        p=subprocess.run(c,text=True,capture_output=True,timeout=20); (a.out/f'arm-{i:02d}.stdout').write_text(p.stdout); (a.out/f'arm-{i:02d}.stderr').write_text(p.stderr)
        if not (arm/'result.json').exists(): raise RuntimeError(f'arm {i} no result rc={p.returncode}')
        r=json.loads((arm/'result.json').read_text()); r['process_returncode']=p.returncode; rows.append(r)
    ds=[r['decision'] for r in rows]
    decision='PASS_NATIVE_XKB_MAP_ROUNDTRIP_SCOPED' if all(x=='PASS_NATIVE_XKB_MAP_ROUNDTRIP_SCOPED' for x in ds) else ('SETUP_BLOCKED_NATIVE_XKB_APPLY' if all(x=='SETUP_BLOCKED_NATIVE_XKB_APPLY' for x in ds) else 'FAIL_INTEGRITY')
    s={'schema':'agent-interface/xkb-native-map-block-v1','decision':decision,'arms':len(rows),'arm_decisions':ds,'formal_reruns':0,'input_operations':sum(r['input_operations'] for r in rows)}
    (a.out/'summary.json').write_text(json.dumps(s,indent=2,sort_keys=True)+'\n'); print(json.dumps(s))
    return 0 if decision!='FAIL_INTEGRITY' else 2
if __name__=='__main__': raise SystemExit(main())
