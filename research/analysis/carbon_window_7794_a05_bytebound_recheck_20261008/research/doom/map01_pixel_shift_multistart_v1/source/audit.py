from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from metric import decide
EXPECTED_METRIC_SHA='04f8ea8c42f950b5e8df9e45cf5a19cc7cc0ab38558b3f7568aabdcb298f93c9'
EXPECTED_IWAD_SHA='a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b'
EXPECTED_RUNTIME_DEPS={
 'research/doom/doom_typed_coast_backend_v1.py':'fda541e12414d6c77b41787eaf208e8dae6b462846ad401d4c7b235b8ae2b079',
 'research/doom/doom_typed_release_backend_v1.py':'ceef50881dc0619ffee5b7ef551ce0851f2650c7371fc37775a80755f077d12f',
 'research/live_control/input_owner_v10.py':'ceae7d9983cd0ba13a35e01ce2ce7dbbf03a0397b23ddc123b0110b4d4de670b',
 'research/live_control/lease.py':'e71f9850d3999a31fcb86c00f9ef7a8ba19bae8d3a8bdc11bf7bd620817a535f',
 'research/live_control/lease_release_v1.py':'b4b1521b5207ea14654463f769b05337685750e9040bed36a8acf006aa1d34ff',
 'research/observation_gating/gui_suite.py':'953a078a06d55b9278bd7b31e176404912340a4f13407e1db343b7776645e97f',
}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def wrap(x): return ((x+180)%360)-180

def audit_case(case_dir,expected):
    errs=[]; rp=case_dir/'result.json'
    if not rp.exists(): return ['missing_result']
    try:r=json.loads(rp.read_text())
    except Exception:return ['bad_result_json']
    for k in ('id','kind','seed','setup_right_pulses','displacement','missing_reference'):
        if r.get(k)!=expected.get(k): errs.append('identity:'+k)
    if r.get('source',{}).get('metric_py')!=EXPECTED_METRIC_SHA: errs.append('metric_sha')
    if r.get('runtime',{}).get('iwad_sha256')!=EXPECTED_IWAD_SHA: errs.append('iwad_sha')
    if r.get('runtime',{}).get('dependency_sha256')!=EXPECTED_RUNTIME_DEPS: errs.append('runtime_deps')
    ref=case_dir/'reference.png'
    if not ref.exists() or sha(ref)!=r.get('reference_sha256'): errs.append('reference_sha')
    if not isinstance(r.get('decisions'),list) or not r['decisions']: return errs+['decisions_missing']
    for row in r['decisions']:
        cur=case_dir/str(row.get('image',''))
        if not cur.exists(): errs.append('missing_image:'+str(row.get('correction'))); continue
        if sha(cur)!=row.get('image_sha256'): errs.append('image_sha:'+str(row.get('correction')))
        refarg=None if r.get('kind')=='missing_reference' else ref
        try:d=decide('HORIZONTAL_SHIFT_STOP',refarg,cur)
        except Exception as e: errs.append('decision_exception:'+type(e).__name__); continue
        if d!=row.get('decision'): errs.append('decision_recompute:'+str(row.get('correction')))
        expected_err=wrap(float(row['evaluator_yaw'])-float(r['reference_yaw']))
        if abs(expected_err-float(row['yaw_error']))>1e-9: errs.append('yaw_recompute:'+str(row.get('correction')))
    last=r['decisions'][-1]; expected_err=wrap(float(last['evaluator_yaw'])-float(r['reference_yaw']))
    if abs(expected_err-float(r['terminal_yaw_error']))>1e-9: errs.append('terminal_yaw')
    if bool(abs(expected_err)<=6.0)!=bool(r['within_6deg']): errs.append('within6')
    exp_false=(r['terminal_status']=='MATCHED' and abs(expected_err)>6.0)
    if bool(r['false_matched'])!=exp_false: errs.append('false_flag')
    if int(r['correction_pulses'])!=int(last['correction']): errs.append('pulse_count')
    neutral=r.get('neutral_keymap')
    if not isinstance(neutral,dict) or any(neutral.values()) or r.get('owned_keys_final')!=[]: errs.append('not_neutral')
    if r.get('death_count')!=0: errs.append('death')
    releases=[x for x in r.get('owner_records',[]) if isinstance(x,dict) and x.get('event')=='owner_release']
    exp_releases=int(r.get('setup_input_program_count',0))+int(r.get('scored_input_program_count',0))
    if len(releases)!=exp_releases: errs.append('release_count')
    if any(x.get('verified') is not True or x.get('keys_down')!=[] or x.get('buttons_down')!=[] for x in releases): errs.append('release_unverified')
    if r['kind']=='aligned' and (r['terminal_status']!='MATCHED' or r['correction_pulses']!=0 or r['scored_input_program_count']!=0): errs.append('aligned_control')
    if r['kind']=='missing_reference' and (r['terminal_status']!='UNKNOWN_MISSING_REFERENCE' or r['correction_pulses']!=0): errs.append('missing_ref_control')
    return errs

def audit(root,plan):
    p=json.loads(plan.read_text()); rows=[]; allerr=[]
    for c in p['cases']:
        e=audit_case(root/c['id'],c); rows.append({'id':c['id'],'errors':e}); allerr += [c['id']+':'+x for x in e]
    return {'schema':'map01-pixel-shift-multistart-audit-v1','errors':allerr,'rows':rows,'pass':not allerr}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--plan',type=Path,required=True);a=ap.parse_args();v=audit(a.root,a.plan);print(json.dumps(v,indent=2));raise SystemExit(0 if v['pass'] else 1)
