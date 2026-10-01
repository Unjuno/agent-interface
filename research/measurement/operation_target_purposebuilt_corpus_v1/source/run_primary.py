import json
from pathlib import Path
from generator import generate,corpus_digest
from validator import validate
SEED=113320260918001
rows=generate(SEED,units=12)
errors,stats=validate(rows,expected_rows=96,expected_units=12)
gates={
 'positive_rows':stats['positives']>=32,'semantic_negatives':stats['semantic_negatives']>=32,
 'operation_families':len(stats['executable_operation_families'])>=2,'no_local_action':stats['no_local_action']>=8,
 'yield':stats['yield']>=8,'target_alternatives':stats['target_alternative_rows']>=16,
 'split_units':stats['train_units']>=1 and stats['eval_units']>=1,'no_alias':stats['alias_groups']==0,
}
if errors: decision='FAIL_INTEGRITY'
elif not all(gates.values()): decision='HOLD_CORPUS_BALANCE_OR_SPLIT_INSUFFICIENT'
else: decision='READY_PURPOSEBUILT_OPERATION_TARGET_CORPUS_SCOPED'
out={'task':'OPERATION-TARGET-PURPOSEBUILT-CORPUS-20260918-001','seed':SEED,'primary_invocations':1,'reruns':0,'stats':stats,'gates':gates,'errors':errors,'corpus_digest_sha256':corpus_digest(rows),'decision':decision,'model_calls':0,'gui_actions':0,'task_input_actions':0}
Path('CORPUS.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
Path('RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,sort_keys=True))
