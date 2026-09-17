VALID={-1,1}

def decide(history_dir,fresh_dir):
    if history_dir not in VALID:
        return {'disposition':'YIELD_UNKNOWN','authority':'none','task_input':False}
    if fresh_dir not in VALID:
        return {'disposition':'YIELD_UNKNOWN','authority':'none','task_input':False}
    if fresh_dir == history_dir:
        d='CONTINUE'
    else:
        d='YIELD_REVERSAL'
    return {'disposition':d,'authority':'none','task_input':False}

def immediate(_history_dir):
    return {'disposition':'CONTINUE','authority':'none','task_input':False}
