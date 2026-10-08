import hashlib,json
from pathlib import Path
from generator import generate,corpus_digest
from analyze import analyze
PARENT_DIGEST='ea4a86baf3d2efc6f79f75703ef164d2c830cd3f5634e7ad057c26315da752dd'
rows=generate(113320260918001,units=12)
digest=corpus_digest(rows)
r=analyze(rows)
if digest!=PARENT_DIGEST:decision='FAIL_INTEGRITY'
elif r['full_conflicting_groups']!=0:decision='FAIL_PARENT_COLLISION_REPRODUCTION'
elif r['id_invariant_conflicting_groups']>0:decision='HOLD_ID_INVARIANT_REPRESENTATION_ALIAS'
else:decision='PASS_ID_INVARIANT_REPRESENTATION_SUFFICIENT_SCOPED'
out={'task':'OPERATION-TARGET-ID-INVARIANT-REPRESENTATION-AUDIT-20260918-001','parent_corpus_digest_sha256':digest,'parent_digest_expected':PARENT_DIGEST,'rows':len(rows),'primary_invocations':1,'reruns':0,'full_conflicting_groups':r['full_conflicting_groups'],'id_invariant_conflicting_groups':r['id_invariant_conflicting_groups'],'witnesses':r['id_invariant_witnesses'],'decision':decision,'model_calls':0,'gui_actions':0,'task_input_actions':0}
Path('RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,sort_keys=True))
