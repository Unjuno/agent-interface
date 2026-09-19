#!/usr/bin/env python3
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
rows=[json.loads((a.root/f'{m:02d}ms'/'report.json').read_text()) for m in [1,12]];by={r['pacing_ms']:r for r in rows}
controls=all(r['controls_passed'] and r['controller_exit']==0 for r in rows); exact=all(r['score']['exact_count']==16 and r['score']['passed'] for r in rows)
if not controls:disp='FAIL_CONTROL_GATE'
elif not by[12]['score']['passed']:disp='FAIL_ENVIRONMENT_12MS'
elif not by[1]['score']['passed']:disp='FAIL_1MS_ENVIRONMENT_TRANSFER'
else:disp='ENVIRONMENT_TRANSFER_PASS_1MS'
d12=by[12]['execution']['edit_elapsed_ns'];d1=by[1]['execution']['edit_elapsed_ns'];delta=d12-d1
out={'schema':'agent-interface/native-x11-xorg-transfer-aggregate-v1','formal_order':[1,12],'complete':len(rows)==2,'controls_passed':controls,'exact_both':exact,'disposition':disp,'arms':[{'pacing_ms':r['pacing_ms'],'exact_count':r['score']['exact_count'],'edit_elapsed_ns':r['execution']['edit_elapsed_ns'],'median_char_start_interval_ns':r['execution']['median_char_start_interval_ns'],'xlsx_sha256':r['score']['xlsx_sha256'],'server':r['server']} for r in rows],'one_vs_twelve_delta_ns':delta,'one_vs_twelve_reduction_pct':100.0*delta/d12 if d12 else None,'formal_pass':controls and exact}
a.out.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2));raise SystemExit(0 if out['formal_pass'] else 1)
