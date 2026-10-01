#!/usr/bin/env python3
import copy,json,subprocess,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parent
origf=json.loads((R/'fixture.json').read_text()); origr=json.loads((R/'RESULT.json').read_text())
def rejected(name, mutate_f=None, mutate_r=None):
    with tempfile.TemporaryDirectory() as d:
        p=Path(d); f=copy.deepcopy(origf); r=copy.deepcopy(origr)
        if mutate_f: mutate_f(f)
        if mutate_r: mutate_r(r)
        (p/'fixture.json').write_text(json.dumps(f)); (p/'RESULT.json').write_text(json.dumps(r)); (p/'audit.py').write_text((R/'audit.py').read_text())
        q=subprocess.run([sys.executable,str(p/'audit.py')],capture_output=True,text=True)
        return {'name':name,'rejected':q.returncode!=0}
rows=[
 rejected('preflight',lambda f:f['arms']['persistent'].__setitem__('preflight_ns',f['arms']['persistent']['preflight_ns']+1)),
 rejected('task_order',lambda f:f['arms']['persistent']['task_elapsed_ns'].__setitem__(1,f['arms']['persistent']['task_elapsed_ns'][2])),
 rejected('repair_route',lambda f:f['arms']['persistent']['routes'].__setitem__(3,'reuse')),
 rejected('final_total',lambda f:f['arms']['plain'].__setitem__('expected_final_ns',f['arms']['plain']['expected_final_ns']+1)),
 rejected('break_even_claim',mutate_r=lambda r:r.__setitem__('wall_break_even_vs_plain_task',3))
]
out={'schema':'integrated_efficiency_cumulative_wall_payback_corruption_v1','controls':rows,'all_rejected':all(x['rejected'] for x in rows)}
(R/'CORRUPTION.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,sort_keys=True)); sys.exit(0 if out['all_rejected'] else 1)
