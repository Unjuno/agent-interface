"""Research consistency wrapper; source identity/current authority remain external."""
from legacy_converter import convert as project
KNOWN={'focus','activate','key_state','key_chord','text','pointer_move','pointer_button','scroll','observe','wait_update','verify','release_all'}
def require(ok,message):
    if not ok:raise ValueError(message)
def integer(value):return type(value) is int and value>=0
def convert(program,receipt):
    require(type(program) is dict and program.get('schema')=='agent-interface/program-v1','program schema')
    ops=program.get('ops');require(type(ops) is list and bool(ops) and all(type(op) is dict and op.get('op') in KNOWN for op in ops),'known program operations')
    require(type(receipt) is dict,'receipt object')
    status=receipt.get('status')
    require(status in {'completed','refused','execution_failed','release_unverified'},'native status')
    if status=='refused':
        require('execution' not in receipt and receipt.get('admission')!='accepted','refused execution/admission')
        for field in ['program_execution_started','input_dispatched']:
            require(field not in receipt or receipt[field] is False,'refused started input')
        require(type(receipt.get('error')) is str and bool(receipt['error']),'refusal reason')
        if 'program_emissions' in receipt:require(type(receipt['program_emissions']) is int and receipt['program_emissions']==0,'refusal emissions')
        if 'recovery_required' in receipt:require(type(receipt['recovery_required']) is bool,'refusal recovery type')
    else:
        require(receipt.get('admission')=='accepted','execution admission')
        require(type(receipt.get('recovery_required')) is bool,'recovery flag')
        execution=receipt.get('execution');require(type(execution) is dict,'execution evidence')
        prefix=execution.get('completed_ops')
        require(type(prefix) is list and all(type(i) is int for i in prefix) and prefix==list(range(len(prefix))) and len(prefix)<=len(ops),'contiguous typed prefix')
        require(integer(execution.get('started_ns')) and integer(execution.get('ended_ns')) and execution['ended_ns']>=execution['started_ns'],'execution clock')
        require(integer(execution.get('program_emissions')) and integer(execution.get('emissions')) and execution['program_emissions']<=execution['emissions'],'emission counters')
        releases=execution.get('releases');require(type(releases) is list and bool(releases),'release evidence')
        for row in releases:
            require(type(row) is dict and type(row.get('verified')) is bool,'typed release status')
            if row['verified']:
                require(row.get('keys_down')==[] and row.get('buttons_down')==[],'verified release neutrality')
        clean=all(row['verified'] is True for row in releases)
        require(receipt['recovery_required']==(not clean),'recovery/release consistency')
        if status=='execution_failed':
            failed=execution.get('failed_op')
            require(type(failed) is int and failed==len(prefix) and 0<=failed<len(ops),'known failed operation')
        else:
            require(len(prefix)==len(ops) and 'failed_op' not in execution,'terminal complete prefix')
            require(clean==(status=='completed'),'terminal release consistency')
    return project(program,receipt)
