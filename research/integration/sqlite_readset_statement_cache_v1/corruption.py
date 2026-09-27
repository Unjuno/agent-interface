"""Eight case-level semantic controls with rebuilt local byte bindings.

Every relocated intact case must pass before mutation. These are not an
adversarial security test and do not claim arbitrary auditor soundness.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from audit import audit_case, load


def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def sync(root,r):
    write(root/'PREPARED.json',r['prepared'])
    named=['initial','before_operation','before_prepare','mutation','after_mutation','final']
    for i,name in enumerate(named):
        write(root/f'peer-{i:02}.stdout',r[name])
        r['peer_calls'][i]['stdout_sha256']=h(root/f'peer-{i:02}.stdout')
    write(root/'peer-06.stdout',r['peer_process']['terminal'])
    r['peer_calls'][6]['stdout_sha256']=h(root/'peer-06.stdout')
    write(root/'PEER_PROCESS.json',r['peer_process']);write(root/'PEER_CALLS.json',r['peer_calls']);write(root/'RAW.json',r)
    write(root/'COPIED_CASE_MANIFEST.json',{p.name:h(p) for p in sorted(root.iterdir()) if p.is_file() and p.name!='COPIED_CASE_MANIFEST.json'})


def run(root):
    raws=[p for p in sorted(root.glob('batch-*/*/RAW.json')) if load(p)['spec']['mode']=='METADATA_REUSE']
    def choose(condition):return next(p for p in raws if load(p)['spec']['condition']==condition)
    controls=[
        ('integer_in_boolean','cold_stable','commit_boolean_type'),
        ('wrong_prepared_revision','cold_stable','receipt_current_at_prepare'),
        ('missing_dependency','cold_stable','metadata_dep_reconstruction'),
        ('foreign_payload','cold_stable','prepared_value_from_actual_table'),
        ('lost_peer_exit','cold_stable','peer_exit'),
        ('false_observed_final_value','cold_stable','readonly_database_reconstruction'),
        ('wrong_cached_schema_lineage','warm_stable','metadata_key_lineage'),
        ('reused_old_version_token','warm_change_before_prepare','receipt_current_at_prepare')]
    result=[]
    for name,condition,expected in controls:
        src=choose(condition)
        with tempfile.TemporaryDirectory() as td:
            dst=Path(td)/'case';shutil.copytree(src.parent,dst)
            base=load(dst/'RAW.json');baseline,_=audit_case(base,dst,base['spec'])
            if baseline:raise RuntimeError('INTACT_RELOCATED_BASELINE_FAILED:'+str(baseline))
            r=copy.deepcopy(base)
            if name=='integer_in_boolean':r['commit']['accepted']=1
            elif name=='wrong_prepared_revision':r['prepared']['receipts'][0]['revision']+=10
            elif name=='missing_dependency':r['prepared']['receipts']=[]
            elif name=='foreign_payload':r['prepared']['value']='foreign-payload'
            elif name=='lost_peer_exit':r['peer_process']['returncode']=None
            elif name=='false_observed_final_value':r['final']['result']['tables']['a'][0]='fabricated-final'
            elif name=='wrong_cached_schema_lineage':r['prime']['schema_version']+=10
            elif name=='reused_old_version_token':r['prepared']['receipts'][0]['revision']=r['prime']['receipts'][0]['revision']
            sync(dst,r)
            rebound=load(dst/'RAW.json');errors,_=audit_case(rebound,dst,base['spec'])
            result.append({'name':name,'intact_relocated_pass':not baseline,
                           'expected_error':expected,'errors':errors,
                           'rejected_with_expected_reason':expected in errors})
    return {'scope':'case-level; edited payloads and local digests reconciled; not a full-allocation rewrite',
            'controls':result,'pass':all(x['rejected_with_expected_reason'] for x in result)}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('--out',required=True);a=p.parse_args()
    r=run(Path(a.root));write(Path(a.out),r);print(json.dumps(r,indent=2));raise SystemExit(0 if r['pass'] else 1)
