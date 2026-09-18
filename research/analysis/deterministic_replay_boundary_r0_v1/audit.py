import argparse,itertools,json,hashlib
from pathlib import Path
EV=(('OBS',0),('OBS',1),('MODEL',0),('MODEL',1),('TOOL',0),('TOOL',1),('AUTH_OPEN',None),('AUTH_CLOSE',None),('TICK',None),('REQUEST',None))
MODES=('ORDERLESS','MODEL_PAYLOAD_DROPPED','AUTH_DROPPED','CLOCK_DROPPED','TOOL_PAYLOAD_DROPPED')

def execute(seq):
    obs=0;plan=None;tool=0;op=False;gen=0;now=0;deadline=-1;outs=[];effects=[]
    trace=[(0,-1,0,False,0,0,-1,(),())]
    for k,p in seq:
        if k=='OBS':obs=p
        elif k=='MODEL':plan=p
        elif k=='TOOL':tool=p
        elif k=='AUTH_OPEN':gen+=1;op=True;deadline=now+1
        elif k=='AUTH_CLOSE':op=False
        elif k=='TICK':now+=2
        elif k=='REQUEST':
            if not op:r='REFUSE_AUTH'
            elif now>deadline:r='REFUSE_EXPIRED'
            elif plan is None:r='REFUSE_NO_PLAN'
            elif plan!=obs:r='REFUSE_PLAN_OBS'
            elif tool!=1:r='REFUSE_TOOL'
            else:r='ADMIT';effects.append((gen,plan,obs,tool,now))
            outs.append(r)
        trace.append((obs,-1 if plan is None else plan,tool,op,gen,now,deadline,tuple(outs),tuple(effects)))
    return tuple(trace)

def sig(seq,m):
    if m=='ORDERLESS':return tuple(sorted(seq,key=lambda x:(x[0],-1 if x[1] is None else x[1])))
    if m=='MODEL_PAYLOAD_DROPPED':return tuple((k,None if k=='MODEL' else p) for k,p in seq)
    if m=='AUTH_DROPPED':return tuple((k,p) for k,p in seq if k not in ('AUTH_OPEN','AUTH_CLOSE'))
    if m=='CLOCK_DROPPED':return tuple((k,p) for k,p in seq if k!='TICK')
    if m=='TOOL_PAYLOAD_DROPPED':return tuple((k,None if k=='TOOL' else p) for k,p in seq)
    raise AssertionError

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--result',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();r=json.loads(Path(a.result).read_text())
    seq_count=sum(len(EV)**n for n in range(6))
    fork_count=sum((len(EV)**n)*(n+1)*len(EV) for n in range(5))
    seen={m:{} for m in MODES};amb={m:set() for m in MODES}
    for n in range(6):
      for seq in itertools.product(EV,repeat=n):
        out=execute(seq)[-1]
        for m in MODES:
          s=sig(seq,m);old=seen[m].get(s)
          if old is None:seen[m][s]=out
          elif old!=out:amb[m].add(s)
    ambc={m:len(amb[m]) for m in MODES}
    errs=[]
    if r['sequences']!=seq_count:errs.append('sequence_count')
    if r['fork_checks']!=fork_count:errs.append('fork_count')
    if r['exact_replay_mismatches']!=0:errs.append('exact_mismatch')
    if r['fork_mismatches']!=0:errs.append('fork_mismatch')
    if r['sequence_integrity_errors']!=0:errs.append('sequence_integrity')
    if r['ambiguous_signature_counts']!=ambc:errs.append('ambiguity_counts')
    if not all(v>0 for v in ambc.values()):errs.append('weak_discriminator')
    if not all(r['corruption_controls'].values()):errs.append('corruption')
    if r['formal_invocations']!=1 or r['reruns']!=0:errs.append('invocation')
    if r['decision']!='PASS_DETERMINISTIC_REPLAY_BOUNDARY_SUFFICIENCY_SCOPED':errs.append('decision')
    q={'pass':not errs,'errors':errs,'sequence_count':seq_count,'fork_count':fork_count,'ambiguity_counts':ambc,'result_digest':r['digest']}
    q['audit_digest']=hashlib.sha256(json.dumps(q,sort_keys=True,separators=(',',':')).encode()).hexdigest();Path(a.output).write_text(json.dumps(q,indent=2,sort_keys=True)+'\n');print(json.dumps(q,indent=2,sort_keys=True))
if __name__=='__main__':main()
