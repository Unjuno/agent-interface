from __future__ import annotations
import itertools,json,hashlib,sys
VALID={'PROGRESS':1,'NEEDS_DECISION':2,'TARGET_LOST':3,'LEASE_EXPIRED':4}
ALPHABET=[(s,k) for s in ['A','B'] for k in VALID]
B=4

def batch(seq):
    out=[]
    for st in range(0,len(seq),B):
        es=seq[st:st+B]
        if not es: continue
        out.append({'events':es,'highest_priority':max(e['priority'] for e in es),'first_arrival':min(e['arrival'] for e in es),'last_arrival':max(e['arrival'] for e in es),'sessions':list(dict.fromkeys(e['session'] for e in es))})
    return out

def main(path='FORMAL_RESULT.json'):
    r=json.load(open(path)); errors=[]; h=hashlib.sha256(); seqs=0; prefixes=0; reduced=0
    for n in range(7):
      for symbols in itertools.product(ALPHABET,repeat=n):
        xs=[{'record_id':f'r{i}','session':s,'delivery_index':i,'arrival':i,'kind':k,'priority':VALID[k],'evidence_id':f'ev{i}'} for i,(s,k) in enumerate(symbols)]
        seqs+=1; bs=batch(xs); flat=[e for b in bs for e in b['events']]
        if flat!=xs: errors.append('sequence')
        if n>=2 and len(bs)<n: reduced+=1
        # Reconstruct candidate JSON shape for the exact digest produced by run_formal.
        digest_batches=[]
        for j,b in enumerate(bs):
          digest_batches.append({'batch_id':f'b{j}','events':b['events'],'highest_priority':b['highest_priority'],'first_arrival':b['first_arrival'],'last_arrival':b['last_arrival'],'sessions':b['sessions'],'input_authority':False,'semantic_authority':False,'resolution_claim':None})
        h.update(json.dumps({'n':n,'symbols':symbols,'batches':digest_batches},sort_keys=True,separators=(',',':')).encode())
        for p in range(n+1):
          prefixes+=1
          pre=xs[:p]
          if [e for bb in batch(pre) for e in bb['events']]!=pre: errors.append('prefix')
    if seqs!=r['sequence_count']: errors.append('sequence_count')
    if prefixes!=r['prefix_count']: errors.append('prefix_count')
    if reduced!=r['sequences_with_delivery_reduction']: errors.append('reduced_count')
    if h.hexdigest()!=r['corpus_digest_sha256']: errors.append('digest')
    for k in ['sequence_mismatches','identity_errors','session_projection_errors','metadata_errors']:
      if r[k]!=0: errors.append(k)
    if r['formal_invocations']!=1 or r['reruns']!=0 or r['replacements']!=0 or r['tuning']!=0: errors.append('invocation_discipline')
    if not all(r['controls'].values()): errors.append('controls')
    if not all(r['gates'].values()): errors.append('gates')
    if r['priority_sorted_directed_reversals']<1: errors.append('negative_comparator')
    out={'schema':'ordered-interrupt-batching-independent-audit-v1','pass':not errors,'errors':errors,'sequence_count':seqs,'prefix_count':prefixes,'corpus_digest_sha256':h.hexdigest()}
    print(json.dumps(out,indent=2,sort_keys=True)); return 0 if not errors else 1
if __name__=='__main__': raise SystemExit(main())
