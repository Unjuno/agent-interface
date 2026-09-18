from __future__ import annotations
import argparse,hashlib,json,random
from pathlib import Path
from candidate import RelevanceGate
from oracle import reduce_history
TASK='OBSERVATION-GATING-O3-RELEVANCE-GENERATION-20260918-001'
SEED=158020260918001
COUNTS=[('CURRENT_IRRELEVANT',30000),('CURRENT_RELEVANT',30000),('SHIFT_STALE_HIDDEN',40000),('FRESH_POST_SHIFT_IRRELEVANT',30000),('CRITICAL_OUTSIDE',20000),('MISSING_RECEIPT',20000),('WRONG_SCOPE_RECEIPT',15000),('FUTURE_OR_FORGED_GENERATION',15000)]
TOTAL=sum(n for _,n in COUNTS)

def sets_for(i):
    k=i%16
    A={k,k+16}; B={k+32,k+48}
    return A,B

def spec_for(i,cat):
    A,B=sets_for(i); r1=f'r{i:06d}-1'; r2=f'r{i:06d}-2'
    ops=[{'kind':'INSTALL','receipt_id':r1,'relevant_tiles':sorted(A)}]
    if cat=='CURRENT_IRRELEVANT':
        ops += [{'kind':'GATE','changed_tiles':[min(B)],'critical_tiles':[],'receipt_id':r1}]
    elif cat=='CURRENT_RELEVANT':
        ops += [{'kind':'GATE','changed_tiles':[min(A)],'critical_tiles':[],'receipt_id':r1}]
    elif cat=='SHIFT_STALE_HIDDEN':
        ops += [{'kind':'ADVANCE','relevant_tiles':sorted(B)}, {'kind':'GATE','changed_tiles':[min(B)],'critical_tiles':[],'receipt_id':r1}]
    elif cat=='FRESH_POST_SHIFT_IRRELEVANT':
        ops += [{'kind':'ADVANCE','relevant_tiles':sorted(B)}, {'kind':'INSTALL','receipt_id':r2,'relevant_tiles':sorted(B)}, {'kind':'GATE','changed_tiles':[min(A)],'critical_tiles':[],'receipt_id':r2}]
    elif cat=='CRITICAL_OUTSIDE':
        t=min(B); ops += [{'kind':'GATE','changed_tiles':[t],'critical_tiles':[t],'receipt_id':r1}]
    elif cat=='MISSING_RECEIPT':
        ops += [{'kind':'GATE','changed_tiles':[min(B)],'critical_tiles':[],'receipt_id':'missing'}]
    elif cat=='WRONG_SCOPE_RECEIPT':
        ops += [{'kind':'GATE','changed_tiles':[min(B)],'critical_tiles':[],'receipt_id':r1,'claimed_scope':'other'}]
    elif cat=='FUTURE_OR_FORGED_GENERATION':
        ops += [{'kind':'GATE','changed_tiles':[min(B)],'critical_tiles':[],'receipt_id':r1,'claimed_generation':99}]
    else: raise ValueError(cat)
    return {'trace_id':f't{i:06d}','scope':f's{i%4}','category':cat,'A':sorted(A),'B':sorted(B),'r1':r1,'r2':r2,'ops':ops}

def canonical_error(row):
    if row.get('ok',True): return row
    e=row.get('error','')
    if 'tile' in e: cls='MALFORMED_TILE'
    elif 'conflicting' in e and 'receipt' in e: cls='CONFLICTING_RECEIPT'
    elif 'install_not_current' in e or 'install_not_current_relevance' in e: cls='INSTALL_NOT_CURRENT'
    elif 'advance_before' in e: cls='ADVANCE_BEFORE_INIT'
    else: cls='OTHER_ERROR'
    return {'kind':row.get('kind'),'ok':False,'error_class':cls}

def run_candidate(spec):
    c=RelevanceGate(spec['scope']); rows=[]; events=[]; mismatch=False
    for op in spec['ops']:
        try:
            if op['kind']=='INSTALL': res=c.install_relevance(op['receipt_id'],op['relevant_tiles'])
            elif op['kind']=='ADVANCE': res=c.advance_relevance(op['relevant_tiles'])
            elif op['kind']=='GATE': res=c.try_gate(op['changed_tiles'],op['critical_tiles'],op['receipt_id'],op.get('claimed_scope'),op.get('claimed_generation'))
            else: raise ValueError('bad_kind')
            rows.append({'kind':op['kind'],'ok':True,'result':res})
        except ValueError as exc:
            rows.append({'kind':op['kind'],'ok':False,'error':str(exc)})
        events.append(op)
        o=reduce_history(spec['scope'],events)
        if [canonical_error(x) for x in rows] != [canonical_error(x) for x in o['rows']] or c.snapshot()!=o['state']:
            mismatch=True
    return {'rows':rows,'state':c.snapshot(),'step_mismatch':mismatch}

def static_relevance(spec):
    receipts={}; current=None; generation=1; suppressions=0; false_suppressions=0; decisions=[]
    for op in spec['ops']:
        if op['kind']=='INSTALL':
            rel=set(op['relevant_tiles'])
            if current is None: current=set(rel)
            receipts.setdefault(op['receipt_id'],{'scope':spec['scope'],'generation':generation,'relevant':set(rel)})
        elif op['kind']=='ADVANCE':
            rel=set(op['relevant_tiles'])
            if current != rel: generation+=1; current=set(rel)
        elif op['kind']=='GATE':
            rec=receipts.get(op['receipt_id']); changed=set(op['changed_tiles']); critical=set(op['critical_tiles'])
            action='FORWARD_FULL_CURRENT'
            if rec is not None and op.get('claimed_scope',rec['scope'])==spec['scope'] and op.get('claimed_generation',rec['generation'])==rec['generation']:
                if changed & critical: action='FORWARD_FULL_CURRENT'
                elif changed & rec['relevant']: action='FORWARD_RELEVANT'
                else: action='SUPPRESS_STATIC_IRRELEVANT'
            suppressions += int(action.startswith('SUPPRESS'))
            must_forward=bool(changed & (current or set()) or changed & critical)
            false_suppressions += int(action.startswith('SUPPRESS') and must_forward)
            decisions.append({'action':action,'must_forward_current':must_forward})
    return {'suppressions':suppressions,'false_suppressions':false_suppressions,'decisions':decisions}

def construction():
    rows=[]
    for i,(cat,_) in enumerate(COUNTS):
        s=spec_for(i,cat); c=run_candidate(s); o=reduce_history(s['scope'],s['ops'])
        rows.append({'category':cat,'match':(not c['step_mismatch'] and [canonical_error(x) for x in c['rows']]==[canonical_error(x) for x in o['rows']] and c['state']==o['state']),'candidate':c,'oracle':o,'static':static_relevance(s)})
    controls=[]
    c=RelevanceGate('s0')
    tests=[('bad_tile_neg',lambda:c.install_relevance('r',[-1])),('bad_tile_hi',lambda:c.install_relevance('r',[64])),('advance_before_init',lambda:RelevanceGate('x').advance_relevance([1]))]
    for name,fn in tests:
        try: fn(); controls.append({'name':name,'rejected':False})
        except ValueError: controls.append({'name':name,'rejected':True})
    c=RelevanceGate('s0'); c.install_relevance('r',[1,2]); dup=c.install_relevance('r',[1,2]); same=c.advance_relevance([1,2])
    try: c.install_relevance('r',[3]); conflict=False
    except ValueError: conflict=True
    controls += [{'name':'duplicate_receipt_noop','rejected':dup['result']=='DUPLICATE_NOOP'},{'name':'same_relevance_advance_noop','rejected':same['result']=='NOOP_SAME_RELEVANCE'},{'name':'conflicting_receipt_rejected','rejected':conflict}]
    return {'task':TASK,'phase':'construction','formal_invocations':0,'reruns':0,'replacements':0,'tuning':0,'rows':rows,'controls':controls}

def schedule():
    arr=[]
    for cat,n in COUNTS: arr.extend([cat]*n)
    random.Random(SEED).shuffle(arr); return arr

def formal(source_sha256):
    metrics={k:0 for k in ['traces','candidate_oracle_mismatch','current_relevant_false_suppressions','stale_hidden_false_suppressions','critical_false_suppressions','current_irrelevant_suppressions','fresh_post_shift_irrelevant_suppressions','fallback_missing','fallback_wrong_scope','fallback_forged_generation','static_stale_false_suppressions']}
    digest=hashlib.sha256(); samples=[]
    for i,cat in enumerate(schedule()):
        s=spec_for(i,cat); c=run_candidate(s); o=reduce_history(s['scope'],s['ops']); st=static_relevance(s)
        metrics['traces']+=1
        bad=c['step_mismatch'] or [canonical_error(x) for x in c['rows']] != [canonical_error(x) for x in o['rows']] or c['state']!=o['state']
        metrics['candidate_oracle_mismatch']+=int(bad)
        gates=[x['result'] for x in c['rows'] if x['kind']=='GATE' and x['ok']]; g=gates[-1]
        suppress=int(g['action'].startswith('SUPPRESS'))
        if cat=='CURRENT_RELEVANT': metrics['current_relevant_false_suppressions']+=suppress
        elif cat=='SHIFT_STALE_HIDDEN': metrics['stale_hidden_false_suppressions']+=suppress; metrics['static_stale_false_suppressions']+=st['false_suppressions']
        elif cat=='CRITICAL_OUTSIDE': metrics['critical_false_suppressions']+=suppress
        elif cat=='CURRENT_IRRELEVANT': metrics['current_irrelevant_suppressions']+=suppress
        elif cat=='FRESH_POST_SHIFT_IRRELEVANT': metrics['fresh_post_shift_irrelevant_suppressions']+=suppress
        elif cat=='MISSING_RECEIPT': metrics['fallback_missing']+=int(g['action']=='FORWARD_FULL_CURRENT')
        elif cat=='WRONG_SCOPE_RECEIPT': metrics['fallback_wrong_scope']+=int(g['action']=='FORWARD_FULL_CURRENT')
        elif cat=='FUTURE_OR_FORGED_GENERATION': metrics['fallback_forged_generation']+=int(g['action']=='FORWARD_FULL_CURRENT')
        compact={'i':i,'category':cat,'gate':g,'static':st,'state':c['state']}
        digest.update(json.dumps(compact,sort_keys=True,separators=(',',':')).encode())
        if len(samples)<24: samples.append(compact)
    return {'task':TASK,'phase':'formal','seed':SEED,'formal_invocations':1,'reruns':0,'replacements':0,'tuning':0,'source_sha256':source_sha256,'metrics':metrics,'ledger_sha256':digest.hexdigest(),'samples':samples}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--phase',choices=['construction','formal'],required=True); ap.add_argument('--out',required=True); ap.add_argument('--source-manifest')
    a=ap.parse_args()
    if a.phase=='construction': out=construction()
    else:
        if not a.source_manifest: raise SystemExit('--source-manifest required')
        out=formal(json.loads(Path(a.source_manifest).read_text())['sha256'])
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'phase':a.phase,'rows':len(out.get('rows',[])),'metrics':out.get('metrics')},sort_keys=True))
if __name__=='__main__': main()
