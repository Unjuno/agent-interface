import itertools, json, hashlib, platform
from pathlib import Path

# Shape copied from existing compiled_runtime_cross_domain_compat_v1 continuous-control:
# surface_present + zone select move_left/move_right/complete.
# Add one action-specific admission guard per action; these are not planner-visible.
methods = ['state_union', 'staged_no_branch_revalidate', 'staged_revalidate']
counts = {m:{'correct_execute':0,'correct_reject':0,'stale_execute':0,'false_reject':0} for m in methods}
rows=[]

for initial_zone in ['LEFT','RIGHT']:
    selected_action = 'move_right' if initial_zone == 'LEFT' else 'move_left'
    selected_guard_name = 'guard_right' if selected_action == 'move_right' else 'guard_left'
    inactive_guard_name = 'guard_left' if selected_guard_name == 'guard_right' else 'guard_right'
    for current_zone, surface_present, guard_left, guard_right, nuisance in itertools.product(
            ['LEFT','RIGHT','GOAL'], [False,True], [False,True], [False,True], [0,1]):
        current={'surface_present':surface_present,'zone':current_zone,
                 'guard_left':guard_left,'guard_right':guard_right,'nuisance':nuisance}
        valid = (surface_present and current_zone == initial_zone and current[selected_guard_name])
        decisions={
            'state_union': (surface_present and current_zone == initial_zone and
                            guard_left and guard_right),
            'staged_no_branch_revalidate': current[selected_guard_name],
            'staged_revalidate': (surface_present and current_zone == initial_zone and
                                  current[selected_guard_name]),
        }
        canonical_digest=hashlib.sha256(json.dumps(current,sort_keys=True).encode()).hexdigest()
        for m,execute in decisions.items():
            if execute and not valid: counts[m]['stale_execute']+=1
            elif not execute and valid: counts[m]['false_reject']+=1
            elif execute: counts[m]['correct_execute']+=1
            else: counts[m]['correct_reject']+=1
        rows.append({'initial_zone':initial_zone,'selected_action':selected_action,
                     'selected_guard':selected_guard_name,'inactive_guard':inactive_guard_name,
                     'current':current,'valid_old_action':valid,'decisions':decisions,
                     'canonical_digest':canonical_digest})

summary={'schema':'compiled-staged-integration-v1','source_shape':'compiled_runtime_cross_domain_compat_v1 continuous-control',
         'states':len(rows),'environment':{'python':platform.python_version(),'platform':platform.platform()},
         'methods':counts}
assert len(rows)==96
assert counts['staged_revalidate']['stale_execute']==0 and counts['staged_revalidate']['false_reject']==0
assert counts['state_union']['stale_execute']==0 and counts['state_union']['false_reject']>0
assert counts['staged_no_branch_revalidate']['stale_execute']>0
summary['decision']='PASS_STAGED_BRANCH_REVALIDATION_ON_EXISTING_COMPILED_SPEC_SHAPE'
Path(__file__).with_name('compiled_shape_summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
print(json.dumps(summary,indent=2,sort_keys=True))
