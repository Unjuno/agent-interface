"""Actual report controls plus unresolved/historical-evidence mutations."""
import copy,hashlib,json
from pathlib import Path
from phased_outcome_v3 import present,feedback
H=Path(__file__).resolve().parent;R=H/'results/phased-outcome-controls-03';R.mkdir(exist_ok=False)
def read(p):return json.loads(p.read_text(encoding='utf-8'))
calc_path=H/'results/sampled-effect-calc-02/turns.json'
prior_path=H/'results/shared-phased-calc-01/turns.json'
calc=read(calc_path);prior=read(prior_path);cases=[]
def case(name,report,expected,blocked=False):
 before=copy.deepcopy(report);view=present(report)
 assert report==before and view['disposition']==expected
 assert (view['new_input']=='blocked')==blocked
 assert view['application_effect'].startswith('unknown')
 assert all(p['effect']=='unknown' for p in view['programs'])
 cases.append({'name':name,'view':view})
 return view
case('preinput_patch_refusal',prior[1]['phases'],'not_submitted')
v=case('actual_confirmation_interrupted',calc[1]['phases'],'program_interrupted')
assert v['programs'][0]['steps_completed']==0 and v['programs'][0]['input_ack_events']==2
case('actual_save_interrupted',calc[0]['phases'],'program_interrupted')
case('actual_completed_resave',calc[2]['phases'],'programs_completed')
phase_path=H/'results/phased-focus-01/phases.json'
case('real_handoff_focus_refusal',read(phase_path),'partial_sequence_stopped')
report=copy.deepcopy(calc[1]['phases']);report['exchanges'][-1]['state']['pending']={'unresolved':True}
case('pending_overrides_old_terminal',report,'protocol_pending',True)
report=copy.deepcopy(calc[1]['phases']);report['exchanges'][-1]['state']['last_resolution']['terminal']['id']='unrelated'
case('unrelated_terminal_not_current',report,'evidence_unresolved',True)
report=copy.deepcopy(calc[1]['phases']);report['exchanges'][-1]['state']['continuation']['channel_closed']=True
case('closed_channel_blocks_input',report,'program_interrupted',True)
report=copy.deepcopy(calc[1]['phases']);report['exchanges'][-1]['state']['last_resolution']['terminal']['release']['verified']=False
case('unverified_release_blocks_input',report,'program_interrupted',True)
report=copy.deepcopy(calc[1]['phases']);last=report['exchanges'][-1]
last['reply']['records']=[e for e in last['reply']['records'] if e['event']!='accepted']
case('absent_admission_not_rejection',report,'evidence_unresolved',True)
report=copy.deepcopy(calc[1]['phases']);report['exchanges'][-1]['state']['last_resolution']['terminal']['status']='future_unknown'
case('unrecognized_terminal_not_negative_proof',report,'evidence_unresolved',True)
report=read(phase_path)
passive=next(r for r in report['exchanges'] if r['request']['command'].get('steps')==[{'op':'observe'}])
passive['state']['last_resolution']['terminal']['release']['verified']=False
case('passive_release_failure_blocks_input',report,'partial_sequence_stopped',True)
original=copy.deepcopy(calc[2]['feedback']);before=copy.deepcopy(original)
adapted=feedback(original,calc[1]['phases']);assert original==before
assert adapted['resolution']==original['resolution'] and adapted['phase_status']=='program_interrupted'
adapted['resolution'].clear();assert original==before
from phased_outcome_v2 import present as previous_view
for phase in [calc[0]['phases'],calc[1]['phases'],prior[1]['phases']]:assert present(phase)==previous_view(phase)
out={'fixed_replay_views_equal_to_v2':True,'scope':'archived live reports and synthetic evidence controls; no GUI input',
     'sources':{str(p.relative_to(H)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),H/'phased_outcome_v3.py',calc_path,prior_path,phase_path]},
     'cases':cases,'feedback_nonalias_and_raw_resolution_preserved':True}
(R/'result.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'cases':len(cases),'passed':True}))
