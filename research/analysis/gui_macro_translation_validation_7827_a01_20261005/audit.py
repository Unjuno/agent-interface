"""Independent raw-only finite trace replay. No imports from candidate.py."""
import hashlib,json,sys
from itertools import product
from pathlib import Path

def digest(b): return hashlib.sha256(b).hexdigest()
def canonical(obj): return digest(json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())
def lower(program, repeat_limit, instruction_limit):
    result=[]
    for term in program:
        if term.get('op')=='repeat':
            amount=term.get('count')
            if type(amount) is not int or amount<0 or amount>repeat_limit: raise OverflowError('repeat_bound')
            result += lower(term.get('body',[]),repeat_limit,instruction_limit)*amount
        else: result.append(term)
        if len(result)>instruction_limit: raise OverflowError('step_bound')
    return result

def world(scenario, observed):
    cut=scenario.get('transition_after')
    return scenario['transition_state'] if cut is not None and observed>=cut else scenario['initial_state']

def interpret_source(code, scenario):
    log=[]; permission=None; cursor=0
    while cursor < len(code):
        if scenario.get('cancel_after') is not None and len(log)==scenario['cancel_after']:
            log.append(['release']); log.append(['abort','cancel']); return log
        op=code[cursor]; kind=op['op']; state=world(scenario,len(log))
        if kind=='guard':
            failure=('stale' if not state['fresh'] else 'wrong_target' if state['active_target']!=op['target'] else None)
            if failure: log.extend((['release'],['abort',failure])); return log
            permission=op['target']
        elif kind=='write':
            if permission!=op['target'] or not state['fresh'] or state['active_target']!=op['target']:
                log.extend((['release'],['abort','unauthorized'])); return log
            log.append(['effect',op['target'],op['effect'],op['value']]); permission=None
        elif kind=='wait': log.append(['wait',op['ticks']])
        elif kind=='observe': log.append(['observe',op['channel']])
        elif kind=='release': log.append(['release'])
        elif kind=='abort': log.extend((['release'],['abort',op['reason']])); return log
        elif kind=='yield': log.append(['yield']); return log
        else: raise OverflowError('unsupported_source:'+str(kind))
        cursor+=1
    return log

def handler(items):
    result=[]
    for item in items:
        if item.get('op')=='RELEASE': result.append(['release'])
        elif item.get('op')=='ABORT_CANCEL': result.append(['abort','cancel'])
        else: result.append(['trap','cancel_handler'])
    return result

def interpret_target(block, scenario):
    log=[]; pc=0; code=block.get('program',[])
    while pc<len(code):
        if scenario.get('cancel_after') is not None and len(log)==scenario['cancel_after']:
            log.extend(handler(block.get('on_cancel',[]))); return log
        op=code[pc]; kind=op.get('op'); state=world(scenario,len(log))
        if kind=='CHECK':
            fail=('stale' if not state['fresh'] else 'wrong_target' if state['active_target']!=op.get('target') else None)
            if fail: log.extend((['release'],['abort',fail])); return log
        elif kind=='EMIT': log.append(['effect',op.get('target'),op.get('effect'),op.get('value')])
        elif kind=='WAIT': log.append(['wait',op.get('ticks')])
        elif kind=='OBSERVE': log.append(['observe',op.get('channel')])
        elif kind=='RELEASE': log.append(['release'])
        elif kind=='ABORT': log.extend((['release'],['abort',op.get('reason')])); return log
        elif kind=='ABORT_NO_RELEASE': log.append(['abort',op.get('reason')]); return log
        elif kind=='YIELD': log.append(['yield']); return log
        elif kind=='CONTINUE': pass
        elif kind=='INTERNAL' and 'side_effect' in op: log.append(['forbidden',op['side_effect']])
        elif kind!='INTERNAL': log.append(['trap',str(kind)])
        pc+=1
    return log

def scenarios(code,model):
    states=[{'active_target':t,'fresh':f} for t in model['contexts']['active_targets'] for f in model['contexts']['fresh']]
    count=len(code); transitions=[(None,None)]
    transitions.extend((index,state) for index in range(1,count+1) for state in states)
    total=len(states)*len(transitions)*(count+1)
    if total>model['bounds']['max_contexts_per_artifact']: raise OverflowError('context_bound')
    for first in states:
        for index,last in transitions:
            for abort_at in (None,*range(count)):
                yield {'initial_state':first,'transition_after':index,'transition_state':last,'cancel_after':abort_at}

def validate(source,target,model):
    try:
        code=lower(source['program'],model['bounds']['max_repeat'],model['bounds']['max_expanded_steps']); seen=0
        for s in scenarios(code,model):
            seen+=1; left=interpret_source(code,s); right=interpret_target(target,s)
            if left!=right: return 'COUNTEREXAMPLE',seen,{'context':s,'source_trace':left,'target_trace':right},None
        return 'VALID',seen,None,None
    except (OverflowError,KeyError,TypeError,ValueError) as error:
        return 'UNKNOWN',0,None,str(error)

def main():
    fp,mp,rp=sys.argv[1:4]; fb=Path(fp).read_bytes(); mb=Path(mp).read_bytes(); candidate_bytes=Path(rp).read_bytes()
    fixture=json.loads(fb); model=json.loads(mb); result=json.loads(candidate_bytes); fh=digest(fb); mh=digest(mb); errors=[]; rows=[]
    if result.get('fixture_sha256')!=fh: errors.append('fixture_hash')
    if result.get('model_sha256')!=mh: errors.append('model_hash')
    accepted={x['id']:x for x in result.get('valid',[])}; rejected={x['id']:x for x in result.get('mutations',[])}; originals={x['id']:x for x in fixture['valid']}
    for p in fixture['valid']:
        status,count,ce,reason=validate(p['source'],p['target'],model); row=accepted.get(p['id'],{})
        if status!='VALID' or row.get('status')!=status or row.get('contexts_checked')!=count: errors.append('valid_pair:'+p['id'])
        certificate=row.get('certificate') or {}
        expected={'source_sha256':canonical(p['source']),'target_sha256':canonical(p['target']),'model_sha256':mh,'fixture_sha256':fh,'contexts_checked':count}
        if certificate!=expected: errors.append('certificate_binding:'+p['id'])
        rows.append({'id':p['id'],'status':status,'contexts':count})
    for mutation in fixture['mutations']:
        source=originals[mutation['source_id']]['source']; status,count,ce,reason=validate(source,mutation['target'],model); row=rejected.get(mutation['id'],{})
        if status!='COUNTEREXAMPLE' or row.get('status')!=status or row.get('contexts_checked')!=count: errors.append('mutation:'+mutation['id'])
        if row.get('counterexample')!=ce or not ce: errors.append('counterexample:'+mutation['id'])
        if row.get('certificate') is not None: errors.append('mutant_certificate:'+mutation['id'])
        rows.append({'id':mutation['id'],'status':status,'contexts':count,'counterexample_replayed':row.get('counterexample')==ce})
    u=fixture['unknown']; us,uc,ue,ur=validate(u['source'],u['target'],model); got=result.get('unknown',{})
    if us!='UNKNOWN' or got.get('status')!=us or got.get('certificate') is not None: errors.append('unknown_bound')
    if result.get('candidate_status')!='PASS_TRANSLATION_VALIDATION_METHOD_SCOPED': errors.append('candidate_gate')
    misses=[x['id'] for x in result.get('mutations',[]) if not x.get('baseline_caught',True)]
    if not misses: errors.append('baseline_no_miss')
    audit_status='PASS_METHOD_SCOPED' if not errors else 'FAIL_METHOD'
    print(json.dumps({'allocation':'UNJUNO-7827-TV-A01-20261005-01','auditor':'independent_finite_trace_replay_v1','fixture_sha256':fh,'model_sha256':mh,'rows':rows,'unknown':{'status':us,'reason':ur,'certificate':got.get('certificate')},'baseline_missed_mutations':misses,'errors':errors,'audit_status':audit_status},sort_keys=True,indent=2))
if __name__=='__main__': main()
