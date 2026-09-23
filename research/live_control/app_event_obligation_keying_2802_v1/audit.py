from __future__ import annotations
import copy,json,sys
from pathlib import Path
EXPECTED={'BOTH_COMPLETE':'SATISFIED','CROSS_ONLY':'PENDING','WRONG_B_THEN_RIGHT':'SATISFIED','O2_COMPLETE_ONLY':'PENDING','INTERLEAVED_COMPLETE':'SATISFIED','MISSING_ID':'UNKNOWN_ID'}
FALSE_PREFIX_EXPECTED={'CROSS_ONLY':1,'WRONG_B_THEN_RIGHT':1,'O2_COMPLETE_ONLY':1,'INTERLEAVED_COMPLETE':1,'MISSING_ID':1}

def oracle(events,target='o1'):
    seen=False; prefix=[]; term=None; last=0
    for e in events:
        if e['seq']<=last: term='UNKNOWN_ORDER'; prefix.append(term); return term,prefix
        last=e['seq']; oid=e.get('obligation_id')
        if oid is None: term='UNKNOWN_ID'; prefix.append(term); return term,prefix
        if oid==target and e['label']=='A': seen=True
        if oid==target and e['label']=='B' and seen: term='SATISFIED'
        prefix.append('SATISFIED' if term=='SATISFIED' else 'PENDING')
    return term or 'PENDING',prefix

def unsafe(events):
    seen=False; prefix=[]; term=None
    for e in events:
        if e['label']=='A': seen=True
        if e['label']=='B' and seen: term='SATISFIED'
        prefix.append('SATISFIED' if term else 'PENDING')
    return term or 'PENDING',prefix

def check(doc):
    errs=[]; rows=doc.get('rows',[]); counts={k:0 for k in EXPECTED}; false_prefix={k:0 for k in FALSE_PREFIX_EXPECTED}
    if len(rows)!=18: errs.append('row_count')
    seen=set()
    for r in rows:
        key=(r.get('rep'),r.get('scenario'))
        if key in seen: errs.append('duplicate_case')
        seen.add(key); s=r.get('scenario')
        if s not in EXPECTED: errs.append('scenario'); continue
        counts[s]+=1
        ev=r.get('events',[])
        if r.get('child_returncode')!=0: errs.append(f'exit:{s}')
        if any(e.get('tick')!=1000+r.get('rep') for e in ev): errs.append(f'tick:{s}')
        if any(e.get('source_id')!='app' or e.get('clock_domain')!='APP_LOGICAL_TICK' for e in ev): errs.append(f'provenance:{s}')
        if [e.get('seq') for e in ev] != list(range(1,len(ev)+1)): errs.append(f'seq:{s}')
        o,op=oracle(ev); u,up=unsafe(ev)
        if o!=EXPECTED[s]: errs.append(f'oracle:{s}:{o}')
        if r.get('candidate')!=o or r.get('candidate_prefix')!=op: errs.append(f'candidate:{s}')
        if r.get('unsafe')!=u or r.get('unsafe_prefix')!=up: errs.append(f'unsafe_record:{s}')
        if s in FALSE_PREFIX_EXPECTED:
            # count any prefix where unsafe is SATISFIED while candidate is not
            if any(a=='SATISFIED' and b!='SATISFIED' for a,b in zip(up,op)): false_prefix[s]+=1
        fs=r.get('final_state') or {}
        expected_o1='DONE' if s in {'BOTH_COMPLETE','WRONG_B_THEN_RIGHT','INTERLEAVED_COMPLETE'} else 'READY'
        if fs.get('o1')!=expected_o1: errs.append(f'effect_o1:{s}')
    for s,n in counts.items():
        if n!=3: errs.append(f'count:{s}:{n}')
    for s,n in false_prefix.items():
        if n!=3: errs.append(f'false_prefix:{s}:{n}')
    return {'errors':errs,'counts':counts,'unsafe_false_prefix_cases':false_prefix,'pass':not errs}

def muts(doc):
    out=[]
    def add(name,fn): x=copy.deepcopy(doc); fn(x); out.append((name,x))
    add('drop_row',lambda x:x['rows'].pop())
    add('dup_row',lambda x:x['rows'].append(copy.deepcopy(x['rows'][0])))
    add('candidate_flip',lambda x:x['rows'][0].__setitem__('candidate','PENDING'))
    add('target_effect_flip',lambda x:x['rows'][0]['final_state'].__setitem__('o1','READY'))
    add('id_cross_fix',lambda x:x['rows'][1]['events'][1].__setitem__('obligation_id','o1'))
    add('missing_id_fix',lambda x:x['rows'][5]['events'][1].__setitem__('obligation_id','o1'))
    add('seq_flip',lambda x:x['rows'][0]['events'][1].__setitem__('seq',1))
    add('tick_flip',lambda x:x['rows'][0]['events'][0].__setitem__('tick',9999))
    add('source_flip',lambda x:x['rows'][0]['events'][0].__setitem__('source_id','other'))
    add('clock_flip',lambda x:x['rows'][0]['events'][0].__setitem__('clock_domain','OTHER'))
    add('prefix_flip',lambda x:x['rows'][2]['candidate_prefix'].__setitem__(1,'SATISFIED'))
    add('exit_flip',lambda x:x['rows'][0].__setitem__('child_returncode',1))
    return out

def main():
    doc=json.loads(Path(sys.argv[1]).read_text()); r=check(doc); rejected=0
    for _,m in muts(doc): rejected += bool(check(m)['errors'])
    r['corruption_controls_rejected']=rejected; r['corruption_controls_total']=12; r['formal_pass']=r['pass'] and rejected==12
    print(json.dumps(r,sort_keys=True,indent=2)); raise SystemExit(0 if r['formal_pass'] else 1)
if __name__=='__main__': main()
