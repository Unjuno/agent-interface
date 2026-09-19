def should_commit(arm, scenario):
    if arm == 'unguarded': return True
    if arm == 'peer_guard': return scenario == 'stable'
    raise ValueError(arm)
