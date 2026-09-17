import copy,json,tempfile,subprocess,sys
from pathlib import Path
# This control audits RESULT mutations; corpus bytes are regenerated from the frozen parent source in primary.
r=json.load(open('RESULT.json')); controls=[]
def check(name,mut):
 with tempfile.TemporaryDirectory() as d:
  # Regenerate exact corpus for independent audit input.
  q=subprocess.run([sys.executable,'-c','from generator import generate;import json;open(r"'+d+'/c.json","w").write(json.dumps(generate(113320260918001,units=12)))'])
  rp=Path(d)/'r.json';rp.write_text(json.dumps(mut))
  z=subprocess.run([sys.executable,'independent_audit.py',str(Path(d)/'c.json'),str(rp)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  controls.append({'name':name,'rejected':z.returncode!=0})
x=copy.deepcopy(r);x['id_invariant_conflicting_groups']=0;check('erase_aliases',x)
x=copy.deepcopy(r);x['full_conflicting_groups']=1;check('invent_parent_alias',x)
x=copy.deepcopy(r);x['parent_corpus_digest_sha256']='0'*64;check('wrong_parent_digest',x)
x=copy.deepcopy(r);x['decision']='PASS_ID_INVARIANT_REPRESENTATION_SUFFICIENT_SCOPED';check('flip_decision',x)
print(json.dumps({'controls':controls,'all_rejected':all(c['rejected'] for c in controls)},sort_keys=True));assert all(c['rejected'] for c in controls)
