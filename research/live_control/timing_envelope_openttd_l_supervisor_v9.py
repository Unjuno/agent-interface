"""Run a source-pinned v8 supervisor with the declared v9 live-memory patch."""
import hashlib
from pathlib import Path


HERE = Path(__file__).resolve().parent
BASE = HERE / 'timing_envelope_openttd_l_supervisor_v8.py'
BASE_SHA256 = '2b8d1e0761c45620110a184c4dd3c555fd64b512952e063c1f5e7705a58202d8'


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise RuntimeError(f'expected exactly one v8 patch site: {old[:80]}')
    return source.replace(old, new)


raw = BASE.read_bytes()
if hashlib.sha256(raw).hexdigest() != BASE_SHA256:
    raise RuntimeError('frozen v8 supervisor source changed')
source = raw.decode('utf-8')
patches = [
    ('from openttd_effect_sheet_v1 import build as build_effect_sheet',
     'from openttd_effect_memory_v1 import build as build_effect_sheet'),
    ("base=HERE/'results/timing-envelope-openttd-l-08'",
     "base=HERE/'results/timing-envelope-openttd-l-09'"),
    ("'scope':'fresh seed-991003 OpenTTD five-tile L objective after pre-action transparency, with bounded post-drag effect evidence'",
     "'scope':'fresh seed-991003 OpenTTD five-tile L objective with one bounded unresolved-drag effect memory'"),
    ("'timing_envelope_openttd_l_supervisor_v8.py','timing_envelope_openttd_l_driver_v5.py'",
     "'timing_envelope_openttd_l_supervisor_v9.py','timing_envelope_openttd_l_driver_v6.py'"),
    ("'openttd_finish_outcome_v1.py'", "'openttd_finish_outcome_v2.py'"),
    ("'openttd_effect_sheet_v1.py'", "'openttd_effect_memory_v1.py'"),
    ("'prompt_policy':'v6 prompt plus labeled bounded before/after/difference crops after each drag'",
     "'prompt_policy':'v8 prompt plus one bounded unresolved-drag row with original before/after, latest inspection and difference'"),
    ("linux(HERE/'timing_envelope_openttd_l_driver_v5.py'),arm,'timing-envelope-openttd-l-08'",
     "linux(HERE/'timing_envelope_openttd_l_driver_v6.py'),arm,'timing-envelope-openttd-l-09'"),
    ('previous=None;planner_image=None;exploration_history=[];checkpoint_required_turn=None',
     'previous=None;planner_image=None;effect_memory=None;exploration_history=[];checkpoint_required_turn=None'),
    ('The next planner image preserves intermediate tooltips as labeled strips or, after a drag, appends labeled before/after/absolute-difference crops for the drag path.',
     'The next planner image preserves intermediate tooltips and, while a drag effect is unresolved, one bounded row with original before, original after, latest inspection and action difference.'),
    ("dump(root/'abort.json',{'finish':True,'reason':'typed model safe stop: '+proposal['rationale']})",
     "dump(root/'abort.json',{'finish':True,'outcome_kind':'typed_model_safe_stop','reason':'typed model safe stop: '+proposal['rationale']})"),
    ("dump(root/f'proposal-{index}.json',{'finish':True,'reason':'typed model requested independent verification'})",
     "dump(root/f'proposal-{index}.json',{'finish':True,'outcome_kind':'visual_verify','reason':'typed model requested independent verification'})"),
    ("planner_image=build_effect_sheet(current_image,applied,proposal,root/'runtime',root/f'planner-{index+1}.png');previous=",
     "memory_input=None if checkpoint_required_turn is not None and proposal['checkpoint']['status']=='observed' and not any(step.get('op')=='pointer_drag' for step in proposal.get('steps',[])) else effect_memory;planner_image,effect_memory=build_effect_sheet(current_image,applied,proposal,root/'runtime',root/f'planner-{index+1}.png',effect=memory_input,turn=index);previous="),
    ("dump(root/'abort.json',{'finish':True,'reason':'bounded turn limit; independent failure score required'})",
     "dump(root/'abort.json',{'finish':True,'outcome_kind':'bounded_turn_limit','reason':'bounded turn limit; independent failure score required'})"),
    ("dump(root/'abort.json',{'finish':True,'reason':'supervisor failure cleanup; no success claim'})",
     "dump(root/'abort.json',{'finish':True,'outcome_kind':'supervisor_cleanup','reason':'supervisor failure cleanup; no success claim'})"),
]
for old, new in patches:
    source = replace_once(source, old, new)
code = compile(source, str(Path(__file__).resolve()), 'exec')
exec(code, {'__name__': '__main__', '__file__': str(Path(__file__).resolve())})
