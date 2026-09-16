def expected(arm, scenario):
    if arm == 'no_fd':
        return scenario == 'stable'
    if arm == 'leaked_fd':
        return True
    raise ValueError(arm)
