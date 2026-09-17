VALID={-1,1}

def _valid_dir(value):
    return type(value) is int and value in VALID

def decide(history_dir,fresh_dir):
    if not _valid_dir(history_dir):
        return {'disposition':'YIELD_UNKNOWN','authority':'none','task_input':False}
    if not _valid_dir(fresh_dir):
        return {'disposition':'YIELD_UNKNOWN','authority':'none','task_input':False}
    if fresh_dir == history_dir:
        d='CONTINUE'
    else:
        d='YIELD_REVERSAL'
    return {'disposition':d,'authority':'none','task_input':False}

def immediate(_history_dir):
    return {'disposition':'CONTINUE','authority':'none','task_input':False}
