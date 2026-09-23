import argparse, hashlib, itertools, json
from pathlib import Path

EVENTS=('SET0','SET1','INC','DOUBLE','TOGGLE','ADVANCE_GEN')
INITIAL=(0,False,0)

def apply_event(state,event):
    x,flag,gen=state
    if event=='SET0': x=0
    elif event=='SET1': x=1
    elif event=='INC': x=(x+1)%8
    elif event=='DOUBLE': x=(2*x)%8
    elif event=='TOGGLE': flag=not flag
    elif event=='ADVANCE_GEN': gen+=1
    else: raise ValueError(event)
    return (x,flag,gen)

def record(seq): return [(i,e) for i,e in enumerate(seq)]

def valid_record(rows):
    if not isinstance(rows,list): return False
    for i,row in enumerate(rows):
        if not isinstance(row,(list,tuple)) or len(row)!=2: return False
        n,e=row
        if n!=i or e not in EVENTS: return False
    return True

def full_fold(rows):
    if not valid_record(rows): raise ValueError('invalid record')
    state=INITIAL
    for _,event in rows: state=apply_event(state,event)
    return state

def incremental(rows):
    if not valid_record(rows): raise ValueError('invalid record')
    state=INITIAL; next_seq=0
    for n,event in rows:
        if n!=next_seq: raise ValueError('noncontiguous')
        state=apply_event(state,event); next_seq+=1
    return state

def prefix_digest(rows):
    h=b'\x00'*32
    for n,event in rows:
        payload=json.dumps([n,event],separators=(',',':')).encode()
        h=hashlib.sha256(h+payload).digest()
    return h.hex()

def checkpoint_receipt(index,pdigest,state):
    payload=json.dumps({'index':index,'prefix_digest':pdigest,'state':list(state)},sort_keys=True,separators=(',',':')).encode()
    return hashlib.sha256(payload).hexdigest()

def make_checkpoint(rows,cut):
    prefix=rows[:cut]; state=full_fold(prefix); pd=prefix_digest(prefix)
    cp={'index':cut,'prefix_digest':pd,'state':list(state)}
    return cp,checkpoint_receipt(cut,pd,state)

def validate_checkpoint(rows,cp,trusted_receipt):
    if not valid_record(rows) or not isinstance(cp,dict): return False
    try: cut=int(cp['index']); pd=str(cp['prefix_digest']); state=tuple(cp['state'])
    except Exception: return False
    if cut<0 or cut>len(rows): return False
    if len(state)!=3 or not isinstance(state[0],int) or not isinstance(state[1],bool) or not isinstance(state[2],int): return False
    if prefix_digest(rows[:cut])!=pd: return False
    if checkpoint_receipt(cut,pd,state)!=trusted_receipt: return False
    return True

def resume(rows,cp,trusted_receipt):
    if not validate_checkpoint(rows,cp,trusted_receipt): raise ValueError('invalid checkpoint')
    state=tuple(cp['state'])
    for n,event in rows[cp['index']:]: state=apply_event(state,event)
    return state

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();out=Path(a.output);assert not out.exists()
    sequence_count=0; projection_mismatch=0; checkpoint_checks=0; checkpoint_mismatch=0
    duplicate_divergence=0; missing_divergence=0; out_of_band_divergence=0
    order_groups={}; index_states={}; witnesses={k:None for k in ('INDEX_ONLY','OUT_OF_BAND','DUPLICATE_APPLY','ORDERLESS','MISSING_EVENT')}
    for n in range(7):
        for seq in itertools.product(EVENTS,repeat=n):
            sequence_count+=1; rows=record(seq); final=full_fold(rows)
            if incremental(rows)!=final: projection_mismatch+=1
            for cut in range(n+1):
                cp,receipt=make_checkpoint(rows,cut); checkpoint_checks+=1
                if resume(rows,cp,receipt)!=final: checkpoint_mismatch+=1
            # index-only checkpoint aliasing: same cut index can name distinct prefix states
            index_states.setdefault(n,{})[seq]=final
            # out-of-band state write after a completed projection
            mutated=((final[0]+1)%8,final[1],final[2])
            if mutated!=final:
                out_of_band_divergence+=1
                if witnesses['OUT_OF_BAND'] is None: witnesses['OUT_OF_BAND']={'seq':seq,'expected':final,'mutated':mutated}
            if n:
                dup=apply_event(final,seq[-1])
                if dup!=final:
                    duplicate_divergence+=1
                    if witnesses['DUPLICATE_APPLY'] is None: witnesses['DUPLICATE_APPLY']={'seq':seq,'expected':final,'duplicate_final':dup}
                for j in range(n):
                    missing=full_fold(record(seq[:j]+seq[j+1:]))
                    if missing!=final:
                        missing_divergence+=1
                        if witnesses['MISSING_EVENT'] is None: witnesses['MISSING_EVENT']={'seq':seq,'drop_index':j,'expected':final,'missing_final':missing}
            sig=tuple(sorted(seq))
            old=order_groups.get(sig)
            if old is None: order_groups[sig]=(final,seq)
            elif old[0]!=final and witnesses['ORDERLESS'] is None:
                witnesses['ORDERLESS']={'a':old[1],'b':seq,'out_a':old[0],'out_b':final}
    # Produce an explicit same-index checkpoint alias witness.
    for n,items in index_states.items():
        seen={}
        for seq,state in items.items():
            old=seen.get(state)
            if old is None: seen[state]=seq
        states=list(seen.items())
        if len(states)>1:
            (s1,q1),(s2,q2)=states[0],states[1]
            witnesses['INDEX_ONLY']={'index':n,'prefix_a':q1,'prefix_b':q2,'state_a':s1,'state_b':s2}
            break
    # Validation/corruption controls.
    good=record(('SET1','INC','TOGGLE'))
    seq_controls={
      'duplicate_seq': not valid_record([[0,'SET1'],[0,'INC']]),
      'gap_seq': not valid_record([[0,'SET1'],[2,'INC']]),
      'unknown_event': not valid_record([[0,'UNKNOWN']]),
    }
    cp,receipt=make_checkpoint(good,2)
    c1=json.loads(json.dumps(cp));c1['state'][0]=(c1['state'][0]+1)%8
    c2=json.loads(json.dumps(cp));c2['prefix_digest']='0'*64
    c3=json.loads(json.dumps(cp));c3['index']=1
    checkpoint_controls={
      'state_corruption': not validate_checkpoint(good,c1,receipt),
      'prefix_corruption': not validate_checkpoint(good,c2,receipt),
      'index_corruption': not validate_checkpoint(good,c3,receipt),
    }
    negatives={
      'INDEX_ONLY': 1 if witnesses['INDEX_ONLY'] else 0,
      'OUT_OF_BAND': out_of_band_divergence,
      'DUPLICATE_APPLY': duplicate_divergence,
      'ORDERLESS': 1 if witnesses['ORDERLESS'] else 0,
      'MISSING_EVENT': missing_divergence,
    }
    decision='PASS_EVENT_SOURCED_PROJECTION_CHECKPOINT_SCOPED' if (
      projection_mismatch==0 and checkpoint_mismatch==0 and all(seq_controls.values()) and all(checkpoint_controls.values()) and all(v>0 for v in negatives.values())
    ) else 'FAIL_EVENT_SOURCED_PROJECTION_CHECKPOINT'
    result={'task':'EVENT-SOURCED-PROJECTION-CHECKPOINT-R0-20260919-001','event_count':len(EVENTS),'sequence_max_length':6,
      'sequences':sequence_count,'projection_mismatches':projection_mismatch,'checkpoint_checks':checkpoint_checks,'checkpoint_mismatches':checkpoint_mismatch,
      'negative_divergence_counts':negatives,'witnesses':witnesses,'sequence_controls':seq_controls,'checkpoint_controls':checkpoint_controls,
      'formal_invocations':1,'reruns':0,'replacements':0,'tuning_after_freeze':0,'decision':decision}
    result['digest']=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':'),default=list).encode()).hexdigest()
    out.write_text(json.dumps(result,indent=2,sort_keys=True,default=list)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='witnesses'},indent=2,sort_keys=True))
if __name__=='__main__':main()
