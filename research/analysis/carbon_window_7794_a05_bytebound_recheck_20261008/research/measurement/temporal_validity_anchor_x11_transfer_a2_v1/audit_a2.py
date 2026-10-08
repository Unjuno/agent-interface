import argparse,hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
PARENT=HERE.parent/'parent'
sys.path.insert(0,str(PARENT))
import audit as parent_audit
TASK='TEMPORAL-SPECULATION-VALIDITY-ANCHOR-X11-TRANSFER-A2-20260918-002'

def verify(r,batch_dir=None):
    e=[]
    if r.get('task')!=TASK:e.append('task')
    if r.get('formal_invocations')!=1 or r.get('formal_batch_invocations')!=8 or r.get('batch_reruns')!=0 or r.get('reruns')!=0:e.append('invocation')
    if len(r.get('batch_manifest',[]))!=8:e.append('batch_manifest_count')
    ids=[x.get('batch_index') for x in r.get('batch_manifest',[])]
    if ids!=list(range(8)):e.append('batch_manifest_order')
    if batch_dir is not None:
        for m in r.get('batch_manifest',[]):
            p=batch_dir/m['file']
            if not p.exists():e.append('missing_batch');continue
            raw=p.read_bytes()
            if hashlib.sha256(raw).hexdigest()!=m.get('sha256') or len(raw)!=m.get('bytes'):e.append('batch_hash')
    parent=parent_audit.verify(r)
    if not parent['audit_pass']:e.extend('parent_'+x for x in parent['errors'])
    decision='PASS_CURRENT_EVIDENCE_VALIDITY_ANCHOR_X11_TRANSFER_A2_SCOPED' if not e else 'FAIL_LIVE_ANCHOR_TRANSFER_A2'
    return {'audit_pass':not e,'errors':e,'decision':decision,'parent_decision':parent['decision']}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('result');ap.add_argument('--batch-dir');a=ap.parse_args();p=Path(a.result);r=json.loads(p.read_text());o=verify(r,Path(a.batch_dir) if a.batch_dir else None);o['result_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();print(json.dumps(o,indent=2,sort_keys=True));raise SystemExit(0 if o['audit_pass'] else 1)
if __name__=='__main__':main()
