import copy,json
from pathlib import Path
from audit import case_errors
HERE=Path(__file__).resolve().parent
src=[]
for p in sorted((HERE/'construction').glob('*/result.json')): src.append(json.loads(p.read_text()))
lookup={(r['mutation'],r['policy']):r for r in src}
controls=[]
def check(name,key,mut):
 r=copy.deepcopy(lookup[key]); mut(r); controls.append({'name':name,'rejected':bool(case_errors(r))})
check('candidate_rejected_but_clicks',('swap','preinput_revalidate'),lambda r:(r['clicks'].append({'role':'decoy'}),r.__setitem__('click_started_ns',1),r.__setitem__('click_done_ns',2)))
check('candidate_swap_admitted',('swap','preinput_revalidate'),lambda r:r.__setitem__('admission_disposition','ADMITTED'))
check('candidate_revalidation_before_swap',('swap','preinput_revalidate'),lambda r:r['admission_capture'].__setitem__('started_ns',r['mutation_receipt']['time_ns']-1))
check('stable_wrong_role',('stable','preinput_revalidate'),lambda r:r['clicks'][0].__setitem__('role','decoy'))
check('terminal_button_live',('stable','single_gate'),lambda r:r.__setitem__('button1_down_terminal',True))
out={'schema':'target_gate_preinput_revalidation_corruption_v1','controls':controls,'all_rejected':all(x['rejected'] for x in controls)}
(HERE/'CORRUPTION_CONSTRUCTION.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if out['all_rejected'] else 1)
