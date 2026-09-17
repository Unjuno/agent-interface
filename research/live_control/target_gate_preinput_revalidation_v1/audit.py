from __future__ import annotations
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def case_errors(r):
    e=[]
    if r.get('gate_contract') != {'radius':5,'max_pixel_error_le':8.0}: e.append('gate_contract')
    if r.get('first_gate_eligible') is not True or r.get('first_gate_diff',999)>8: e.append('first_gate')
    if r.get('button1_down_terminal') is not False: e.append('terminal_button')
    mutation=r.get('mutation'); policy=r.get('policy'); clicks=r.get('clicks',[]); receipt=r.get('mutation_receipt'); cap=r.get('admission_capture'); disp=r.get('admission_disposition')
    if mutation=='stable':
        if receipt is not None: e.append('stable_mutation')
        if disp!='ADMITTED' or len(clicks)!=1 or clicks[0].get('role')!='task-target': e.append('stable_liveness')
        if policy=='single_gate':
            if cap is not None: e.append('baseline_second_capture')
        elif policy=='preinput_revalidate':
            if not isinstance(cap,dict) or cap.get('diff',999)>8: e.append('stable_revalidation')
            if cap and r.get('click_started_ns') is not None and cap.get('done_ns',10**30)>=r['click_started_ns']: e.append('revalidation_not_before_click')
        else:e.append('policy')
    elif mutation=='swap':
        if not isinstance(receipt,dict) or receipt.get('roles',{}).get('A')!='decoy': e.append('swap_receipt')
        if receipt and receipt.get('time_ns',0)<=r.get('first_gated_ns',10**30): e.append('swap_not_after_first_gate')
        if policy=='single_gate':
            if cap is not None: e.append('baseline_second_capture')
            if disp!='ADMITTED' or len(clicks)!=1 or clicks[0].get('role')!='decoy': e.append('baseline_failure_not_reproduced')
            if receipt and r.get('click_started_ns') is not None and r['click_started_ns']<=receipt['time_ns']: e.append('baseline_click_order')
        elif policy=='preinput_revalidate':
            if not isinstance(cap,dict): e.append('missing_revalidation_capture')
            else:
                if cap.get('started_ns',0)<=receipt.get('time_ns',10**30): e.append('revalidation_not_after_swap')
                if cap.get('diff',0)<=8: e.append('swap_not_discriminated')
            if disp!='TARGET_EVIDENCE_CHANGED': e.append('wrong_rejection')
            if clicks or r.get('click_started_ns') is not None or r.get('click_done_ns') is not None: e.append('revalidation_escape')
        else:e.append('policy')
    else:e.append('mutation')
    return e

def audit(root):
    root=Path(root); manifest=json.loads((root/'manifest.json').read_text()); errors=[]; rows=[]
    if manifest.get('formal_invocations')!=1 or manifest.get('reruns')!=0 or len(manifest.get('cases',[]))!=16: errors.append('manifest')
    for c in manifest.get('cases',[]):
        p=root/c['case_id']/'result.json'
        if c.get('returncode')!=0 or not p.exists(): errors.append(f"case_process:{c['case_id']}"); continue
        r=json.loads(p.read_text()); ce=case_errors(r); rows.append(r)
        errors.extend(f"{c['case_id']}:{x}" for x in ce)
    source=(HERE/'run_case.py').read_text()
    for bad in ["info['B']", 'info["B"]', "info['roles']", 'info["roles"]']:
        if bad in source: errors.append('privileged_or_relocation_source')
    if 'RADIUS=5; MAX_PIXEL_ERROR=8.0' not in source: errors.append('gate_constants_source')
    counts={}
    for r in rows: counts[(r['mutation'],r['policy'])]=counts.get((r['mutation'],r['policy']),0)+1
    if any(counts.get(k)!=4 for k in [('stable','single_gate'),('stable','preinput_revalidate'),('swap','single_gate'),('swap','preinput_revalidate')]): errors.append('strata_counts')
    decision='PASS_PREINPUT_VISUAL_REVALIDATION_SCOPED' if not errors else 'FAIL_REVALIDATION_OR_INTEGRITY'
    return {'schema':'target_gate_preinput_revalidation_audit_v1','passed':not errors,'decision':decision,'errors':errors,'rows':len(rows),'strata':{f'{a}|{b}':n for (a,b),n in sorted(counts.items())}}

if __name__=='__main__':
    out=audit(HERE/'formal-output'); (HERE/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if out['passed'] else 1)
