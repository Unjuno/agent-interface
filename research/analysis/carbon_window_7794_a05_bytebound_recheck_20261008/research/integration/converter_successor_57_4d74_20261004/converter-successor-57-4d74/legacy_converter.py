"""Research-only projection; retains whole native receipt, grants no authority."""
import copy,hashlib,json
INPUT={'key_state','key_chord','text','pointer_move','pointer_button','scroll'}
def convert(program,receipt):
    raw=copy.deepcopy(receipt);status=raw.get('status')
    if status=='refused' and 'execution' not in raw:
        decision={'status':'safe_yield','reason':'execution_refused','completed_actions':0,'input_dispatched':False}
    else:
        execution=raw.get('execution');ops=program['ops']
        if status not in {'completed','execution_failed','release_unverified'} or not isinstance(execution,dict):raise ValueError('unknown native shape')
        completed=execution.get('completed_ops')
        if not isinstance(completed,list) or any(type(i) is not int for i in completed) or completed!=list(range(len(completed))) or len(completed)>len(ops):raise ValueError('invalid contiguous prefix')
        count=sum(ops[i]['op'] in INPUT for i in completed)
        failed=execution.get('failed_op')
        uncertain_input=status=='execution_failed' and type(failed) is int and 0<=failed<len(ops) and ops[failed]['op'] in INPUT
        dispatched=bool(count or uncertain_input)
        releases=execution.get('releases')
        clean=isinstance(releases,list) and bool(releases) and all(isinstance(r,dict) and r.get('verified') is True and r.get('keys_down')==[] and r.get('buttons_down')==[] for r in releases)
        if status=='completed' and len(completed)==len(ops) and clean and raw.get('recovery_required') is False:
            decision={'status':'completed'}
        else:
            reason='delivery_uncertain' if status=='release_unverified' or not clean else 'execution_failed'
            decision={'status':'safe_yield','reason':reason,'completed_actions':count,'input_dispatched':dispatched}
    return {'decision':decision,'native_receipt':raw,'native_receipt_sha256':hashlib.sha256(json.dumps(raw,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'count_unit':'completed input-bearing native IR operations; not XTEST emissions','authority':'none'}
