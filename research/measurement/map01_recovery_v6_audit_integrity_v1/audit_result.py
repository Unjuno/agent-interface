from __future__ import annotations
import argparse,json
from pathlib import Path
EXPECTED={
 'audit_map01_recovery_cover_mechanism_v4.py':'c193b8e985b5e047d4a28f8f04b2ccaf60daac12',
 'audit_map01_recovery_cover_mechanism_v6.py':'e3c34caad26a5a7e17d2464c945b74f747b75d4b',
}
def audit(path:Path)->dict:
    r=json.loads(path.read_text(encoding='utf-8'));errors=[]
    if r.get('source_git_blobs')!=EXPECTED:errors.append('source_identity')
    s=r.get('static_source_check') or {}
    if not all(s.get(k) is True for k in ('pair_coast_read','pair_recovery_read','arm_bounds_read')):errors.append('static_required_reads')
    if s.get('arm_no_input_numeric_read') is not False:errors.append('unexpected_arm_numeric_binding')
    t=r.get('truth') or {};c=r.get('summary_only_corrupt') or {}
    if t.get('non_summary_tree_sha256')!=c.get('non_summary_tree_sha256') or r.get('identical_non_summary_tree') is not True:errors.append('non_summary_tree_changed')
    if t.get('summary_sha256')==c.get('summary_sha256'):errors.append('summary_not_changed')
    if not (t.get('valid_experiment') is True and t.get('decision')=='HOLD' and c.get('valid_experiment') is True and c.get('decision')=='PASS_MECHANISM_ONLY'):errors.append('decision_flip_missing')
    if t.get('guard_failures')!=[] or not c.get('guard_failures'):errors.append('binding_guard_control')
    ctr=r.get('controls') or {}
    for k in ('invalid_arm','wrong_phase'):
        if (ctr.get(k) or {}).get('decision')!='FAIL' or (ctr.get(k) or {}).get('valid_experiment') is not False:errors.append(f'{k}_not_rejected')
    if r.get('decision')!='CONFIRMED_V6_SUMMARY_ARM_BINDING_GAP':errors.append('decision')
    return {'schema':'map01-recovery-v6-audit-integrity-independent-audit-v1','errors':errors,'pass':not errors}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('result',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();v=audit(a.result);a.out.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n');print(json.dumps(v,indent=2,sort_keys=True));raise SystemExit(0 if v['pass'] else 1)
