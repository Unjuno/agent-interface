"""Controls for compact planner evidence using retained live records."""
import copy
import hashlib
import json
from pathlib import Path
from planner_evidence_v1 import checkpoint, execution, present

H = Path(__file__).resolve().parent
R = H / 'results/planner-evidence-controls-01'
R.mkdir(exist_ok=False)
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
form_root = H / 'results/checkpoint-recovery-form-01'
calc_root = H / 'results/checkpoint-decision-calc-01'
form_losses = read(form_root / 'losses.json')
calc_turns = read(calc_root / 'turns.json')
valid = []
for name, resolution in [
        ('form_unknown', form_losses[0]['recovered']['state']['last_resolution']),
        ('form_verified', form_losses[1]['recovered']['state']['last_resolution']),
        ('calc_unknown', calc_turns[1]['feedback']['checkpoint_resolution']),
        ('calc_verified', calc_turns[1]['checkpoint']['state']['last_resolution'])]:
    value = checkpoint(resolution)
    assert value['status'] == ('VERIFIED' if name.endswith('verified') else 'UNKNOWN')
    assert value['authority'] == 'none' and value['task_completion'] == 'not_scored'
    valid.append({'name': name, 'bytes': len(json.dumps(value, separators=(',', ':')).encode())})
phase = execution(calc_turns[0]['phases'])
assert phase['programs'][-1]['terminal'] == 'needs_decision'
assert all(program['application_effect'] == 'unknown' for program in phase['programs'])
view = present(calc_turns[1]['feedback']['checkpoint_resolution'],
               phase_report=calc_turns[0]['phases'], prior_steps=calc_turns[0]['proposal']['steps'])
assert view['checkpoint']['status'] == 'UNKNOWN' and view['raw_evidence'] == 'retained_by_caller'
bad = []
base = form_losses[1]['recovered']['state']['last_resolution']
for name, mutate in [
        ('wrong_request_id', lambda x: x.update(request_id='wrong')),
        ('task_success', lambda x: x['checkpoint'].update(task_success=True)),
        ('wrong_actual', lambda x: x['checkpoint']['evidence'].update(actual={'value': ['wrong']})),
        ('observation_closed', lambda x: x['checkpoint']['evidence'].update(observation_closed=True)),
        ('missing_digest', lambda x: x['checkpoint']['evidence'].pop('artifact_sha256'))]:
    value = copy.deepcopy(base); mutate(value)
    try:
        checkpoint(value)
    except ValueError:
        bad.append(name)
    else:
        raise AssertionError(name)
bad_phase = copy.deepcopy(calc_turns[0]['phases'])
bad_phase['exchanges'][-1]['state']['last_resolution']['terminal']['release']['verified'] = False
try:
    execution(bad_phase)
except ValueError:
    bad.append('unverified_release')
else:
    raise AssertionError('unverified release')
sources = [Path(__file__), H / 'planner_evidence_v1.py', H / 'checkpoint_contract_v1.py',
           form_root / 'losses.json', calc_root / 'turns.json']
report = {'scope': 'presentation controls over retained live evidence; no model or GUI input',
          'valid': valid, 'refused': bad, 'calc_compact_bytes': len(json.dumps(view, separators=(',', ':')).encode()),
          'sources': {str(p.relative_to(H)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}
(R / 'result.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'valid': len(valid), 'refused': len(bad), 'calc_compact_bytes': report['calc_compact_bytes']}))
