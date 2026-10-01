import argparse, hashlib, itertools, json
from pathlib import Path

INITIAL_ID='INIT0'
INITIAL=(0,-1,0,False,0,0,-1,(),())
# state: obs, plan(-1/0/1), tool, auth_open, generation, now, deadline, outcomes, effects
EVENTS=(
 ('OBS',0),('OBS',1),('MODEL',0),('MODEL',1),('TOOL',0),('TOOL',1),
 ('AUTH_OPEN',None),('AUTH_CLOSE',None),('TICK',None),('REQUEST',None),
)
PAYLOAD_KINDS={'OBS','MODEL','TOOL'}
KINDS={x[0] for x in EVENTS}

def candidate_step(state,event):
    obs,plan,tool,opened,gen,now,deadline,outcomes,effects=state
    kind,payload=event
    if kind=='OBS': obs=payload
    elif kind=='MODEL': plan=payload
    elif kind=='TOOL': tool=payload
    elif kind=='AUTH_OPEN':
        gen+=1; opened=True; deadline=now+1
    elif kind=='AUTH_CLOSE': opened=False
    elif kind=='TICK': now+=2
    elif kind=='REQUEST':
        if not opened: reason='REFUSE_AUTH'
        elif now>deadline: reason='REFUSE_EXPIRED'
        elif plan<0: reason='REFUSE_NO_PLAN'
        elif plan!=obs: reason='REFUSE_PLAN_OBS'
        elif tool!=1: reason='REFUSE_TOOL'
        else:
            reason='ADMIT'
            effects=effects+((gen,plan,obs,tool,now),)
        outcomes=outcomes+(reason,)
    else: raise ValueError(kind)
    return (obs,plan,tool,opened,gen,now,deadline,outcomes,effects)

def record(seq,initial_id=INITIAL_ID):
    return {'initial_id':initial_id,'events':[(i,e[0],e[1]) for i,e in enumerate(seq)]}

def validate_record(rec):
    if rec.get('initial_id')!=INITIAL_ID: return False
    evs=rec.get('events')
    if not isinstance(evs,list): return False
    for i,row in enumerate(evs):
        if not isinstance(row,(tuple,list)) or len(row)!=3: return False
        seq,kind,payload=row
        if seq!=i or kind not in KINDS: return False
        if kind in PAYLOAD_KINDS:
            if payload not in (0,1): return False
        elif payload is not None: return False
    return True

def replay(rec):
    if not validate_record(rec): raise ValueError('invalid_record')
    state=INITIAL; trace=[state]
    for _,kind,payload in rec['events']:
        state=candidate_step(state,(kind,payload)); trace.append(state)
    return tuple(trace)

def oracle_execute(seq):
    s={'obs':0,'plan':None,'tool':0,'open':False,'gen':0,'now':0,'deadline':-1,'out':[],'eff':[]}
    trace=[(0,-1,0,False,0,0,-1,(),())]
    for kind,payload in seq:
        if kind=='OBS': s['obs']=payload
        elif kind=='MODEL': s['plan']=payload
        elif kind=='TOOL': s['tool']=payload
        elif kind=='AUTH_OPEN': s['gen']+=1; s['open']=True; s['deadline']=s['now']+1
        elif kind=='AUTH_CLOSE': s['open']=False
        elif kind=='TICK': s['now']+=2
        elif kind=='REQUEST':
            if not s['open']: x='REFUSE_AUTH'
            elif s['now']>s['deadline']: x='REFUSE_EXPIRED'
            elif s['plan'] is None: x='REFUSE_NO_PLAN'
            elif s['plan']!=s['obs']: x='REFUSE_PLAN_OBS'
            elif s['tool']!=1: x='REFUSE_TOOL'
            else: x='ADMIT'; s['eff'].append((s['gen'],s['plan'],s['obs'],s['tool'],s['now']))
            s['out'].append(x)
        trace.append((s['obs'],-1 if s['plan'] is None else s['plan'],s['tool'],s['open'],s['gen'],s['now'],s['deadline'],tuple(s['out']),tuple(s['eff'])))
    return tuple(trace)

def observable(trace):
    return trace[-1]

def signature(seq,mode):
    if mode=='ORDERLESS': return tuple(sorted(seq,key=lambda x:(x[0],-1 if x[1] is None else x[1])))
    if mode=='MODEL_PAYLOAD_DROPPED': return tuple((k,None if k=='MODEL' else p) for k,p in seq)
    if mode=='AUTH_DROPPED': return tuple((k,p) for k,p in seq if k not in ('AUTH_OPEN','AUTH_CLOSE'))
    if mode=='CLOCK_DROPPED': return tuple((k,p) for k,p in seq if k!='TICK')
    if mode=='TOOL_PAYLOAD_DROPPED': return tuple((k,None if k=='TOOL' else p) for k,p in seq)
    raise ValueError(mode)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); a=ap.parse_args(); outp=Path(a.output); assert not outp.exists()
    modes=('ORDERLESS','MODEL_PAYLOAD_DROPPED','AUTH_DROPPED','CLOCK_DROPPED','TOOL_PAYLOAD_DROPPED')
    seen={m:{} for m in modes}; ambiguous={m:set() for m in modes}; witnesses={m:None for m in modes}
    exact_mismatch=0; sequence_integrity_errors=0; sequences=0
    for n in range(6):
        for seq in itertools.product(EVENTS,repeat=n):
            sequences+=1
            rec=record(seq)
            if not validate_record(rec): sequence_integrity_errors+=1
            got=replay(rec); want=oracle_execute(seq)
            if got!=want: exact_mismatch+=1
            out=observable(want)
            for m in modes:
                sig=signature(seq,m); prev=seen[m].get(sig)
                if prev is None: seen[m][sig]=(out,seq)
                elif prev[0]!=out:
                    ambiguous[m].add(sig)
                    if witnesses[m] is None: witnesses[m]={'a':prev[1],'b':seq,'out_a':prev[0],'out_b':out}
    fork_checks=0; fork_mismatch=0
    for n in range(5):
        for seq in itertools.product(EVENTS,repeat=n):
            for cut in range(n+1):
                prefix=seq[:cut]
                for alt in EVENTS:
                    fork_checks+=1
                    rec=record(prefix)
                    base_trace=replay(rec)
                    state=base_trace[-1]
                    fork_state=candidate_step(state,alt)
                    want=oracle_execute(prefix+(alt,))[-1]
                    if fork_state!=want: fork_mismatch+=1
    # Corruption controls must all be rejected by record validation.
    good=record((('AUTH_OPEN',None),('MODEL',0),('TOOL',1),('REQUEST',None)))
    corrupt=[]
    x=json.loads(json.dumps(good)); x['events'][1][0]=0; corrupt.append(('duplicate_seq',x))
    x=json.loads(json.dumps(good)); x['events'][1][2]=2; corrupt.append(('bad_payload',x))
    x=json.loads(json.dumps(good)); x['events'][1][1]='UNKNOWN_KIND'; corrupt.append(('bad_kind',x))
    x=json.loads(json.dumps(good)); x['initial_id']='OTHER'; corrupt.append(('bad_initial',x))
    corruption={name:(not validate_record(x)) for name,x in corrupt}
    amb_counts={m:len(ambiguous[m]) for m in modes}
    decision='PASS_DETERMINISTIC_REPLAY_BOUNDARY_SUFFICIENCY_SCOPED' if (
        exact_mismatch==0 and fork_mismatch==0 and sequence_integrity_errors==0 and
        all(v>0 for v in amb_counts.values()) and all(corruption.values())
    ) else 'FAIL_DETERMINISTIC_REPLAY_BOUNDARY'
    result={
      'task':'DETERMINISTIC-REPLAY-BOUNDARY-SUFFICIENCY-R0-20260919-001',
      'events':len(EVENTS),'sequence_max_length':5,'sequences':sequences,
      'exact_replay_mismatches':exact_mismatch,'sequence_integrity_errors':sequence_integrity_errors,
      'fork_checks':fork_checks,'fork_mismatches':fork_mismatch,
      'ambiguous_signature_counts':amb_counts,'ambiguity_witnesses':witnesses,
      'corruption_controls':corruption,'formal_invocations':1,'reruns':0,'replacements':0,'tuning_after_freeze':0,
      'decision':decision,
    }
    result['digest']=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':'),default=list).encode()).hexdigest()
    outp.write_text(json.dumps(result,indent=2,sort_keys=True,default=list)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='ambiguity_witnesses'},indent=2,sort_keys=True))
if __name__=='__main__': main()
