from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
def sha(b): return hashlib.sha256(b).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();r=a.root;e=r/'evidence';errors=[]
    stop=json.loads((e/'STOP.json').read_text(encoding='utf-8')); status=json.loads((e/'RUN_STATUS.json').read_text(encoding='utf-8'))
    identity=json.loads((e/'identity.stdout.txt').read_text(encoding='utf-8')); baseline=json.loads((e/'baseline.json').read_text(encoding='utf-8'))
    inp=json.loads((e/'INPUT_AUDIT.json').read_text(encoding='utf-8')); samples=[json.loads(x) for x in (e/'sampler.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
    src=(r/'launch.py').read_text(encoding='utf-8'); sig="def helper(root,evidence,network,script,args=(),network_none=False):"
    formal_exists=(e/'formal').exists() and any((e/'formal').glob('*.json'))
    if stop.get('model_calls')!=0 or status.get('formal_requests_sent')!=0 or status.get('completed_calls')!=0: errors.append('formal_call_count')
    if status.get('decision')!='STOP_LAUNCHER_TYPEERROR_PRECALL' or stop.get('decision')!=status.get('decision'): errors.append('stop_class')
    if stop.get('error_type')!='TypeError' or stop.get('exact_failed_expression')!='helper(..., timeout=900)' or sig not in src or 'timeout=900)' not in src: errors.append('launcher_failure_provenance')
    if formal_exists or stop.get('formal_runner_invoked') is not False: errors.append('formal_runner_may_have_started')
    if identity.get('digest')!='fb90415cde1ef08aa669ae74b082d49b158729b6db1ab183c941417d507e71a1' or identity.get('ollama_ps_empty') is not True: errors.append('model_identity_or_server_state')
    if baseline.get('empty_model_server') is not True or baseline.get('memory_used_mib')!=0 or baseline.get('ollama_ps','').count('\n')>1: errors.append('baseline_not_empty')
    if inp.get('decision')!='INPUT_AUDIT_PASS' or inp.get('errors')!=[]: errors.append('input_audit')
    if samples and any((s.get('memory_used_mib') or 0)>0 or (s.get('gpu_utilization_percent') or 0)>0 for s in samples): errors.append('unexpected_gpu_activity_before_call')
    if len(samples)!=stop.get('sampler_samples'): errors.append('sampler_count')
    result={'schema':'visual-temporal-570-r6-stop-audit-v1','allocation':stop.get('allocation'),'decision':stop.get('decision') if not errors else 'HOLD_STOP_AUDIT','errors':errors,
        'verified_formal_calls':0,'model_identity_verified':identity.get('digest')=='fb90415cde1ef08aa669ae74b082d49b158729b6db1ab183c941417d507e71a1','formal_output_directory_present':formal_exists,
        'construction_input_audit':inp.get('decision'),'precall_gpu_samples':len(samples),'precall_gpu_positive_samples':sum(1 for s in samples if (s.get('memory_used_mib') or 0)>0 or (s.get('gpu_utilization_percent') or 0)>0),
        'launcher_sha256':sha((r/'launch.py').read_bytes()),'stop_record_sha256':sha((e/'STOP.json').read_bytes()),'decision_scope':'Implementation STOP only; no model/temporal-encoding result.'}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8');print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
