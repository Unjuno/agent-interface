def should_commit(arm, scenario):
    if arm == 'control':
        return scenario == 'stable'
    if arm == 'inject_fd':
        return True
    raise ValueError(arm)
