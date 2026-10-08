import json,random,hashlib
from pathlib import Path
from contract import validate_row,validate_dataset
from oracle import row_valid,dataset_valid
from generator import base,mutate
H=Path(__file__).resolve().parent; seed=113220260918001;rng=random.Random(seed)
rows=120000;mismatch=0;valid_rows=0;invalid_rows=0;invalid_accepted=0;authority_errors=0
for i in range(rows):
    r=base(i,rng); intended_valid=(i%3)!=0
    if not intended_valid:r=mutate(r,rng.randrange(10))
    ov=row_valid(r)
    try: c=validate_row(r); cv=True; authority_errors += int(c['grants_input_authority'] is not False)
    except ValueError: cv=False
    mismatch += int(cv!=ov); valid_rows += int(ov); invalid_rows += int(not ov); invalid_accepted += int((not ov) and cv)
dataset_cases=20000;dataset_mismatch=0;split_leakage_accepted=0
for i in range(dataset_cases):
    a=base(200000+i*2,rng); b=base(200001+i*2,rng)
    if i%2==0:
        b['episode_id']=a['episode_id'];b['split']='eval' if a['split']=='train' else 'train'
    ov=dataset_valid([a,b])
    try: validate_dataset([a,b]);cv=True
    except ValueError:cv=False
    dataset_mismatch+=int(cv!=ov);split_leakage_accepted+=int((not ov) and cv)
out={'schema':'operation_target_row_contract_result_v1','task':'OPERATION-TARGET-ROW-CONTRACT-20260918-001','decision':'PASS_OPERATION_TARGET_ROW_CONTRACT_SCOPED' if mismatch==dataset_mismatch==invalid_accepted==split_leakage_accepted==authority_errors==0 else 'FAIL_ROW_CONTRACT','seed':seed,'formal_invocation':1,'reruns':0,'rows':rows,'valid_rows':valid_rows,'invalid_rows':invalid_rows,'candidate_oracle_mismatches':mismatch,'invalid_accepted':invalid_accepted,'dataset_cases':dataset_cases,'dataset_mismatches':dataset_mismatch,'split_leakage_accepted':split_leakage_accepted,'authority_errors':authority_errors,'model_calls':0,'gui_actions':0,'task_input_actions':0,'real_rows_counted_toward_1015':0}
out['digest']=hashlib.sha256(json.dumps(out,sort_keys=True,separators=(',',':')).encode()).hexdigest();(H/'RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(out['decision'])
