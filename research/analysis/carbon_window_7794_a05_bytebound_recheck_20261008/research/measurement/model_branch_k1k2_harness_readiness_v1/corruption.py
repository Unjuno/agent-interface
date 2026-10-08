import copy,json
from audit import verify
from pathlib import Path
r=json.loads(Path('RESULT.json').read_text());out=[]
def t(name,mut):
 x=copy.deepcopy(r);mut(x);z=verify(x);out.append({'name':name,'rejected':not z['audit_pass'],'errors':z['errors']})
t('prompt_diff',lambda x:x['prompt_diff'].__setitem__('diff_count',2))
t('extra_generation',lambda x:x['generations_per_arm'].__setitem__('K2',2))
t('authority_parser',lambda x:x.__setitem__('parser_no_authority_ok',False))
t('usage_missing',lambda x:x.__setitem__('usage_arrival_extractor_ok',False))
t('fake_cli_ready',lambda x:(x.__setitem__('runtime_ready',True),x.__setitem__('decision','PASS_MODEL_BRANCH_MATCHED_HARNESS_READY_SCOPED')))
assert all(v['rejected'] for v in out),out
Path('CORRUPTION.json').write_text(json.dumps({'controls':out,'rejected':sum(v['rejected'] for v in out),'total':len(out)},indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2))
