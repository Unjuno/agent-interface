def choose(current_child, target, known_failure):
    if type(current_child) is not int or type(target) is not int or current_child<=0 or target<=0:return 'UNKNOWN'
    return 'TRY' if current_child==target else 'BLOCK'
