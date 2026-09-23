from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
base=json.loads((ROOT/'RESULT.json').read_text())
tests=[]
def run(name, mut):
    with tempfile.TemporaryDirectory() as td:
        t=Path(td)
        for f in ['LEDGER.json','audit.py']:(t/f).write_bytes((ROOT/f).read_bytes())
        r=json.loads(json.dumps(base)); mut(r); (t/'RESULT.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
        p=subprocess.run([sys.executable,str(t/'audit.py')],cwd=t,capture_output=True,text=True)
        tests.append({'name':name,'rejected':p.returncode!=0})
run('admissible_count',lambda r:r.__setitem__('admissible_pairs',1))
run('gate_erasure',lambda r:r['rows'][0].__setitem__('failed_gates',[]))
run('source_blob',lambda r:r['rows'][1].__setitem__('git_blob','0'*40))
run('decision',lambda r:r.__setitem__('decision','PASS_RETAINED_SYMBOL_REPRESENTATION_IDENTIFIABLE_SCOPED'))
out={'all_rejected':all(x['rejected'] for x in tests),'tests':tests}
(ROOT/'CORRUPTION.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,sort_keys=True))
raise SystemExit(0 if out['all_rejected'] else 2)
