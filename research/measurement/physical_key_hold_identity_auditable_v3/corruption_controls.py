from __future__ import annotations
import copy,json
from pathlib import Path
from audit import validate
HERE=Path(__file__).resolve().parent
chunks=json.loads((HERE/'CHUNK_SUMMARIES.json').read_text()); result=json.loads((HERE/'RESULT.json').read_text()); fixed=json.loads((HERE/'FIXED.json').read_text())
controls=[]
def check(name,c=None,r=None,f=None):
    out=validate(c or copy.deepcopy(chunks),r or copy.deepcopy(result),f or copy.deepcopy(fixed)); controls.append({'name':name,'rejected':not out['passed'],'errors':out['errors']})
c=copy.deepcopy(chunks); c['chunks']=c['chunks'][:-1]; check('missing_chunk',c=c)
c=copy.deepcopy(chunks); c['chunks'][3]['counts']['mismatches']=1; check('nonzero_mismatch',c=c)
r=copy.deepcopy(result); r['chunk_digest_sha256']='0'*64; check('digest_corrupt',r=r)
r=copy.deepcopy(result); r['x11_actions']=1; check('side_effect_corrupt',r=r)
f=copy.deepcopy(fixed); f['passed']=False; check('fixed_corrupt',f=f)
out={'passed':all(x['rejected'] for x in controls),'controls':controls,'controls_total':len(controls),'controls_rejected':sum(x['rejected'] for x in controls)}
(HERE/'CORRUPTION.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,sort_keys=True))
