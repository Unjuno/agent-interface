#!/usr/bin/env python3
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def audit(root):
    r=json.loads((root/'RESULT.json').read_text());e=r.get('events',[]);errs=[]
    if r.get('formal_invocation')!=1 or r.get('formal_reruns')!=0:errs.append('formal_count')
    if r.get('decision')!='PASS_MINDUSTRY_REPEAT_FIXTURE_PROTOCOL_SCOPED':errs.append('decision')
    if not all(r.get('source_checks',{}).values()):errs.append('source_checks')
    if not all(r.get('controls',{}).values()):errs.append('controls')
    ready=[x.get('task_id') for x in e if x.get('event')=='task_ready']
    if ready!=['A1','A2','A3','B1','B2','B3']:errs.append('ready_order')
    for n in range(1,7):
        names=[x['event'] for x in e if x.get('epoch')==n]
        required=['checkpoint_snapshot','score_verified','reset_applied','reset_witness']
        pos=[]
        for x in required:
            if x not in names:errs.append(f'missing:{n}:{x}');break
            pos.append(names.index(x))
        if len(pos)==4 and pos!=sorted(pos):errs.append(f'order:{n}')
    geom=[i for i,x in enumerate(e) if x.get('event')=='geometry_mutation']
    if len(geom)!=1:errs.append('geometry_count')
    private={'checkpoint_snapshot','score_verified','reset_applied','reset_witness','geometry_mutation','task_failed','reset_witness_failed'}
    if any(x.get('event') in private for x in r.get('controller_projection',[])):errs.append('control_plane_leak')
    return {'schema':'mindustry_repeat_fixture_protocol_audit_v1','passed':not errs,'errors':errs,'decision':'PASS_MINDUSTRY_REPEAT_FIXTURE_PROTOCOL_SCOPED' if not errs else 'FAIL_MINDUSTRY_REPEAT_FIXTURE_PROTOCOL','result_sha256':sha(root/'RESULT.json')}
def main():
    root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT;out=audit(root)
    if len(sys.argv)==1:(root/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True));raise SystemExit(0 if out['passed'] else 1)
if __name__=='__main__':main()
