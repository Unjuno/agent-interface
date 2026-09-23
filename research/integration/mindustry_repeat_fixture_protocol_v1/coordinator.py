CONTROLLER_OPS=frozenset(('submit','clock','cancel'))
PRIVATE_OPS=frozenset(('checkpoint','score','reset','geometry_mutation'))

def controller_accepts(op): return op in CONTROLLER_OPS

def next_private_actions(task_id, score_verified, reset_witness):
    if not score_verified: return ['stop_failed_task']
    actions=['write_score_pass','write_reset_request','wait_reset_witness']
    if not reset_witness: return actions+['stop_bad_reset']
    if task_id=='A3': actions += ['geometry_mutation_A_to_B']
    actions += ['publish_next_ready']
    return actions
