from __future__ import annotations
import copy, hashlib, json, sys
from pathlib import Path

EXPECTED={
 'SAME_DOMAIN_CONTIGUOUS':'SATISFIED',
 'CROSS_DOMAIN':'UNKNOWN_CLOCK_DOMAIN',
 'GAPPED_SEQUENCE':'UNKNOWN_GAP',
 'REGRESSED_SEQUENCE':'UNKNOWN_ORDER',
 'CROSS_SOURCE':'UNKNOWN_SOURCE',
 'LATE_B':'EXPIRED',
}
BOUND_NS=20_000_000

def oracle(events):
    anchor=None; cur=None
    for e in events:
        if anchor is None:
            if e['label']=='A': anchor=e; cur=e
            continue
        if e['source_id']!=anchor['source_id']: return 'UNKNOWN_SOURCE'
        if e['clock_domain']!=anchor['clock_domain']: return 'UNKNOWN_CLOCK_DOMAIN'
        if e['seq']<=cur['seq']: return 'UNKNOWN_ORDER'
        if e['seq']!=cur['seq']+1: return 'UNKNOWN_GAP'
        if e['t_ns']<cur['t_ns']: return 'UNKNOWN_TIME'
        if e['t_ns']-anchor['t_ns']>BOUND_NS: return 'EXPIRED'
        cur=e
        if e['label']=='B': return 'SATISFIED'
    return 'PENDING'

def check(doc):
    errors=[]; rows=doc.get('rows',[])
    if len(rows)!=18: errors.append('row_count')
    counts={k:0 for k in EXPECTED}; unsupported={k:0 for k in EXPECTED}
    seen=set()
    for r in rows:
        key=(r.get('rep'),r.get('scenario'))
        if key in seen: errors.append('duplicate_case')
        seen.add(key)
        s=r.get('scenario')
        if s not in EXPECTED: errors.append('scenario'); continue
        counts[s]+=1
        if r.get('child_returncode')!=0: errors.append(f'exit:{s}')
        if (r.get('final_state') or {}).get('state')!='DONE': errors.append(f'effect:{s}')
        o=oracle(r.get('events',[]))
        if o!=EXPECTED[s]: errors.append(f'oracle:{s}:{o}')
        if r.get('candidate')!=o: errors.append(f'candidate:{s}')
        if s in {'CROSS_DOMAIN','GAPPED_SEQUENCE','REGRESSED_SEQUENCE','CROSS_SOURCE'} and r.get('unsafe')=='SATISFIED': unsupported[s]+=1
    for s,n in counts.items():
        if n!=3: errors.append(f'count:{s}:{n}')
    for s in ['CROSS_DOMAIN','GAPPED_SEQUENCE','REGRESSED_SEQUENCE','CROSS_SOURCE']:
        if unsupported[s]!=3: errors.append(f'unsafe_discriminator:{s}:{unsupported[s]}')
    return {'errors':errors,'counts':counts,'unsafe_unsupported_satisfied':unsupported,'pass':not errors}

def mutations(doc):
    muts=[]
    def add(name,fn):
        x=copy.deepcopy(doc); fn(x); muts.append((name,x))
    add('drop_row',lambda x:x['rows'].pop())
    add('dup_row',lambda x:x['rows'].append(copy.deepcopy(x['rows'][0])))
    add('candidate_flip',lambda x:x['rows'][0].__setitem__('candidate','EXPIRED'))
    add('source_flip',lambda x:x['rows'][4]['events'][1].__setitem__('source_id','app-a'))
    add('domain_flip',lambda x:x['rows'][1]['events'][1].__setitem__('clock_domain','MONOTONIC'))
    add('seq_gap_fix',lambda x:x['rows'][2]['events'][1].__setitem__('seq',2))
    add('seq_regress_fix',lambda x:x['rows'][3]['events'][1].__setitem__('seq',3))
    add('effect_flip',lambda x:x['rows'][4].__setitem__('final_state',{'state':'READY'}))
    add('exit_flip',lambda x:x['rows'][5].__setitem__('child_returncode',1))
    add('scenario_flip',lambda x:x['rows'][0].__setitem__('scenario','CROSS_DOMAIN'))
    add('event_label_flip',lambda x:x['rows'][0]['events'][1].__setitem__('label','A'))
    add('time_late',lambda x:x['rows'][0]['events'][1].__setitem__('t_ns',x['rows'][0]['events'][0]['t_ns']+BOUND_NS+1))
    return muts

def main():
    p=Path(sys.argv[1]); doc=json.loads(p.read_text()); out=check(doc)
    rejected=0; controls={}
    for name,m in mutations(doc):
        bad=check(m); controls[name]=bad['errors']; rejected+=bool(bad['errors'])
    out['corruption_controls_rejected']=rejected
    out['corruption_controls_total']=12
    out['formal_pass']=out['pass'] and rejected==12
    print(json.dumps(out,sort_keys=True,indent=2))
    raise SystemExit(0 if out['formal_pass'] else 1)
if __name__=='__main__': main()
