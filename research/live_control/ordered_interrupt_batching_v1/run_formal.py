from __future__ import annotations
import hashlib,itertools,json,os,time
from model import Event,VALID_KINDS,ordered_batch,priority_sorted_batch,flatten
from cases import directed_cases

TASK='EVENT-ORDERED-INTERRUPT-BATCHING-20260919-001'
BATCH_SIZE=4
ALPHABET=[(s,k) for s in ['A','B'] for k in ['PROGRESS','NEEDS_DECISION','TARGET_LOST','LEASE_EXPIRED']]

def make(seq):
    return [Event(f'r{i}',s,i,i,k,VALID_KINDS[k],f'ev{i}') for i,(s,k) in enumerate(seq)]

def digest_update(h, obj):
    h.update(json.dumps(obj,sort_keys=True,separators=(',',':')).encode())

def main(out_path='FORMAL_RESULT.json'):
    if os.path.exists(out_path):
        raise SystemExit('formal_result_exists_refuse_rerun')
    start=time.perf_counter()
    seq_count=0; prefix_count=0; mismatch=0; identity_err=0; session_err=0; metadata_err=0; reduced=0
    h=hashlib.sha256()
    for n in range(0,7):
        for symbols in itertools.product(ALPHABET, repeat=n):
            xs=make(symbols); seq_count += 1
            batches=ordered_batch(xs,BATCH_SIZE); flat=flatten(batches); ref=[e.to_dict() for e in xs]
            if flat != ref: mismatch += 1
            if sorted(e['record_id'] for e in flat) != sorted(e.record_id for e in xs): identity_err += 1
            for s in ['A','B']:
                if [e['record_id'] for e in flat if e['session']==s] != [e.record_id for e in xs if e.session==s]: session_err += 1
            for b in batches:
                es=b['events']
                if b['highest_priority'] != max(e['priority'] for e in es): metadata_err += 1
                if b['first_arrival'] != min(e['arrival'] for e in es): metadata_err += 1
                if b['last_arrival'] != max(e['arrival'] for e in es): metadata_err += 1
                if b['sessions'] != list(dict.fromkeys(e['session'] for e in es)): metadata_err += 1
                if b['input_authority'] or b['semantic_authority'] or b['resolution_claim'] is not None: metadata_err += 1
            if n>=2 and len(batches)<n: reduced += 1
            digest_update(h, {'n':n,'symbols':symbols,'batches':batches})
            for p in range(n+1):
                prefix_count += 1
                pre=xs[:p]
                if flatten(ordered_batch(pre,BATCH_SIZE)) != [e.to_dict() for e in pre]: mismatch += 1
    directed={}
    reversals=0
    for name,xs in directed_cases().items():
        ref=[e.to_dict() for e in xs]
        candidate=flatten(ordered_batch(xs,BATCH_SIZE))
        naive=flatten(priority_sorted_batch(xs,BATCH_SIZE))
        cand_ok=(candidate==ref)
        naive_reversed=([e['record_id'] for e in naive] != [e['record_id'] for e in ref])
        reversals += int(naive_reversed)
        directed[name]={'candidate_exact':cand_ok,'priority_sorted_reversed':naive_reversed,'individual_deliveries':len(xs),'candidate_deliveries':len(ordered_batch(xs,BATCH_SIZE))}
    controls={'duplicate':False,'nonmonotonic':False,'invalid_priority':False,'invalid_kind':False,'invalid_batch_size':False}
    from cases import E
    from model import ordered_batch
    checks=[
      ('duplicate',lambda: ordered_batch([E(0,'A','PROGRESS'),E(0,'A','PROGRESS')])),
      ('nonmonotonic',lambda: ordered_batch([E(0,'A','PROGRESS'),Event('r1','A',0,1,'PROGRESS',1,'ev1')])),
      ('invalid_priority',lambda: ordered_batch([Event('r0','A',0,0,'PROGRESS',4,'ev0')])),
      ('invalid_kind',lambda: ordered_batch([Event('r0','A',0,0,'BOGUS',1,'ev0')])),
      ('invalid_batch_size',lambda: ordered_batch([],0)),
    ]
    for name,fn in checks:
        try: fn()
        except ValueError: controls[name]=True
    gates={
      'sequence_exact': mismatch==0,
      'identity_exact': identity_err==0,
      'session_projection_exact': session_err==0,
      'metadata_exact': metadata_err==0,
      'directed_candidate_exact': all(v['candidate_exact'] for v in directed.values()),
      'naive_reversal_exposed': reversals>=1,
      'delivery_reduction_exposed': reduced>=1,
      'malformed_fail_closed': all(controls.values()),
    }
    result={
      'schema':'ordered-interrupt-batching-formal-v1','task':TASK,'formal_invocations':1,'reruns':0,'replacements':0,'tuning':0,
      'batch_size':BATCH_SIZE,'sequence_count':seq_count,'prefix_count':prefix_count,'sequence_mismatches':mismatch,'identity_errors':identity_err,'session_projection_errors':session_err,'metadata_errors':metadata_err,'sequences_with_delivery_reduction':reduced,'priority_sorted_directed_reversals':reversals,'directed':directed,'controls':controls,'gates':gates,'corpus_digest_sha256':h.hexdigest(),'elapsed_seconds':time.perf_counter()-start,
      'decision':'PASS_ORDERED_INTERRUPT_BATCHING_SCOPED' if all(gates.values()) else 'FAIL_ORDERED_INTERRUPT_BATCHING'
    }
    raw=json.dumps(result,indent=2,sort_keys=True)+'\n'
    open(out_path,'x').write(raw)
    print(raw,end='')

if __name__=='__main__': main()
