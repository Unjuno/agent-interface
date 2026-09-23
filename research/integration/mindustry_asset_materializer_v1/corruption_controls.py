#!/usr/bin/env python3
import copy,json,subprocess,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parent; orig=json.loads((R/'RESULT.json').read_text())

def reject(name,mut):
    with tempfile.TemporaryDirectory() as td:
        p=Path(td); (p/'fixture.json').write_text((R/'fixture.json').read_text()); x=copy.deepcopy(orig); mut(x); (p/'RESULT.json').write_text(json.dumps(x)); (p/'audit.py').write_text((R/'audit.py').read_text())
        q=subprocess.run([sys.executable,str(p/'audit.py')],capture_output=True,text=True)
        return {'name':name,'rejected':q.returncode!=0}
rows=[
 reject('decision',lambda x:x.__setitem__('decision','PASS_ASSETS_READY')),
 reject('wrong_save_cleanup',lambda x:x['controls']['wrong_save']['cleanup'].__setitem__('clean',False)),
 reject('manifest_hash',lambda x:x['good']['manifest']['files']['jar'].__setitem__('sha256','0'*64)),
 reject('formal_count',lambda x:x.__setitem__('formal_reruns',1)),
]
out={'schema':'mindustry_asset_materializer_corruption_v1','controls':rows,'all_rejected':all(r['rejected'] for r in rows)}
(R/'CORRUPTION.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,sort_keys=True)); sys.exit(0 if out['all_rejected'] else 1)
