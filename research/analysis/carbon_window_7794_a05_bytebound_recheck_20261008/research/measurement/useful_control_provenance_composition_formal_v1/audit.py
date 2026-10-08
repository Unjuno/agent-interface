from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
MEAS=HERE.parent
sys.path.insert(0,str(MEAS/'useful_control_interval_contract_v1'))
sys.path.insert(0,str(MEAS/'useful_control_provenance_composition_v1'))
sys.path.insert(0,str(HERE))
from interval_contract import Actuation,EffectEvent,Interval,ReleaseReceipt
from composed_contract import EffectRecord,analyze_composed
from oracle import oracle_analyze

def sha(path: Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()
def validate_result_data(r: dict) -> list[str]:
    errors=[]
    if r.get('composition_git_blob')!='b78ced2ca877b7c8ba28ec093c531ad4d2cbb73a': errors.append('composition_blob')
    if r.get('parent_git_blob')!='979f257b4f02be80bcaa30ae8d5a0aa92162bfb1': errors.append('parent_blob')
    for n,h in r.get('source_sha256',{}).items():
        if not (HERE/n).exists() or sha(HERE/n)!=h: errors.append(f'hash:{n}')
    if (r.get('formal_invocations'),r.get('formal_reruns'))!=(1,0): errors.append('invocations')
    if r.get('valid_cases')!=100000 or r.get('valid_exact_equal')!=100000: errors.append('valid')
    if r.get('adversarial_cases')!=50000 or r.get('adversarial_exact_equal')!=50000: errors.append('adversarial')
    if (r.get('boundary_controls_passed'),r.get('boundary_controls_total'))!=(11,11): errors.append('controls')
    if any(r.get(k)!=0 for k in ['model_calls','network_actions','task_input_actions','authority_actions']): errors.append('side_effect')
    if r.get('disposition')!='PASS_USEFUL_CONTROL_PROVENANCE_COMPOSITION_SCOPED': errors.append('disposition')
    return errors

def edge_controls()->list[str]:
    errors=[]; W=Interval(0,20); A=Actuation(5,ReleaseReceipt(10,12,False),[Interval(4,8)],'a')
    rows=[
      [EffectRecord('e1',EffectEvent(5,'a',True,True))],
      [EffectRecord('e2',EffectEvent(-1,'a',False,True))],
      [EffectRecord('e3',EffectEvent(4,'a',False,True))],
      [EffectRecord('e4',EffectEvent(-1,'   ',True,True))],
      [EffectRecord('e5',EffectEvent(15,'missing',True,False))],
    ]
    for i,records in enumerate(rows):
        exp=oracle_analyze(W,[A],records)
        try: got=('ok',analyze_composed(W,[A],records))
        except ValueError as e: got=('error',str(e))
        if got!=exp: errors.append(f'edge:{i}')
    return errors

def main():
    r=json.loads((HERE/'FORMAL_RESULT.json').read_text())
    errors=validate_result_data(r)+edge_controls()
    out={'task':r['task'],'passed':not errors,'errors':errors,'result_sha256':sha(HERE/'FORMAL_RESULT.json'),'formal_rerun_executed':False}
    (HERE/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True))
if __name__=='__main__': main()
