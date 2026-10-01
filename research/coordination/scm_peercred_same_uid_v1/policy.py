def should_commit(arm, scenario):
    if arm == 'uid_only': return True
    if arm == 'uid_pid': return scenario == 'stable'
    raise ValueError(arm)
