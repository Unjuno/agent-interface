"""Read-only evidence reconstruction. Imports no runner/policy/fixture code."""
import argparse, hashlib, json
from pathlib import Path

SCENARIOS=('NORMAL','DUPLICATE_CHILD','OLD_GENERATION_CHILD','FOREIGN_SESSION','WRONG_PARENT','MISSING_CHILD')
MODES=('COUNT_ONLY_POP','LINEAGE_BOUND_POP')
FIELDS=('session','id','generation','parent')

def audit(records, reps, sources=None):
    errors=[]
    checks=0
    def require(ok, code):
        nonlocal checks
        checks+=1
        if not ok: errors.append(code)
    expected={(r,s,m) for r in reps for s in SCENARIOS for m in MODES}
    seen=[]
    counts={'candidate_complete':0,'candidate_unresolved':0,'candidate_wrong':0,'weak_wrong':0}
    for item in records:
        r,j=item['row'],item['journal']
        ident=r.get('session','missing')
        try:
            key=(r['rep'],r['scenario'],r['mode']);seen.append(key)
            s,m=r['scenario'],r['mode']
            require(key in expected,ident+':case_identity')
            require(r['status']=='COMPLETE',ident+':incomplete')
            require(r['app_exit']==0 and r['xvfb_exit']==0 and r['socket_removed'] is True,ident+':process_cleanup')
            if sources is not None: require(r['sources']==sources,ident+':source')
            require(len(r['initial_keymap'])==32 and not any(r['initial_keymap']),ident+':initial_neutral')
            require(len(r['final_keymap'])==32 and not any(r['final_keymap']) and r['final_buttons']==0,ident+':final_neutral')
            require(len({z['pid'] for z in j})==1,ident+':app_pid')
            require(all(type(z['ns']) is int for z in j) and all(a['ns']<=b['ns'] for a,b in zip(j,j[1:])),ident+':app_time_order')
            require(not any(z['kind']=='error' for z in j),ident+':app_error')
            e=r['events']
            require(all(a['ns']<=b['ns'] for a,b in zip(e,e[1:])),ident+':controller_time_order')
            require(j[0]['kind']=='ready' and j[0]['session']==ident,ident+':ready')
            ready=[z['response'] for z in e if z['kind']=='ready']
            require(ready==[dict(ready=True,pid=j[0]['pid'],session=ident)],ident+':ready_process_binding')
            require(j[-1]['kind']=='quit',ident+':app_terminal')
            app_commands=[z['command'] for z in j if z['kind']=='command']
            requests=[z['request'] for z in e if z['kind']=='command']
            require(app_commands==requests,ident+':command_lineage')
            opened=[z['frame'] for z in j if z['kind']=='opened']
            closed=[dict(z['frame'],status='RESOLVED',closed_ns=z['ns']) for z in j if z['kind']=='closed']
            pg=dict(session=ident,id='P',generation=1,parent='ROOT:1')
            c1=dict(session=ident,id='C',generation=1,parent='P:1')
            c2=dict(c1,generation=2)
            require(opened==[pg,c1]+([c2] if s=='OLD_GENERATION_CHILD' else []),ident+':opened_frames')
            require([ {k:c[k] for k in FIELDS} for c in closed]==([c1,c2,pg] if s=='OLD_GENERATION_CHILD' else [c1,pg]),ident+':closed_frames')
            expected_receipts=[]
            current=closed[-2]
            if s=='OLD_GENERATION_CHILD': expected_receipts.append(closed[0])
            if s=='FOREIGN_SESSION': expected_receipts.append(dict(current,session='foreign-session'))
            if s=='WRONG_PARENT': expected_receipts.append(dict(current,parent='OTHER:1'))
            if s!='MISSING_CHILD': expected_receipts.append(current)
            if s=='DUPLICATE_CHILD': expected_receipts.append(current)
            expected_receipts.append(closed[-1])
            deliveries=[z for z in e if z['kind']=='delivery']
            require([z['receipt'] for z in deliveries]==expected_receipts,ident+':delivery_schedule')
            state=[pg,c2 if s=='OLD_GENERATION_CHILD' else c1]
            require(r['initial_stack']==state,ident+':initial_stack')
            resumed=0
            for d in deliveries:
                receipt,t=d['receipt'],d['transition']
                require(t['before']==state,ident+':stack_before')
                consume=bool(state) and receipt.get('status')=='RESOLVED'
                if m=='LINEAGE_BOUND_POP' and consume:
                    current_top=state[-1]
                    consume=all(k in receipt and type(receipt[k]) is type(current_top[k]) and receipt[k]==current_top[k] for k in FIELDS)
                if consume: state=state[:-1]
                fires=consume and not state and resumed==0
                resumed+=int(fires)
                require(t==dict(before=t['before'],after=state,accepted=consume,resume=fires,authority=False),ident+':transition')
            require(state==r['final_stack'],ident+':final_stack')
            suffix=[z for z in e if z['kind']=='suffix']
            require(len(suffix)==resumed,ident+':suffix_count')
            emitted=[(z['letter'],z['edge']) for z in e if z['kind']=='key']
            require(emitted==[('a','down'),('a','up')]+([('b','down'),('b','up')] if resumed else []),ident+':native_edges')
            presses=[z for z in j if z['kind']=='KeyPress']
            releases=[z for z in j if z['kind']=='KeyRelease']
            require([z['key'] for z in presses]==['a']+(['b'] if resumed else []),ident+':app_press')
            require([(z['key'],z['widget']) for z in releases]==[(z['key'],z['widget']) for z in presses],ident+':app_release')
            require(presses[0]['widget']=='ROOT:1' and presses[0]['live']==[],ident+':prefix_destination')
            snapshots=[z['value'] for z in j if z['kind']=='snapshot']
            require(snapshots==[r['prefix'],r['final']],ident+':snapshot_lineage')
            require(r['prefix']['root']=='a' and r['prefix']['live']==[],ident+':prefix_effect')
            require(r['final']['live']==[] and r['final']==j[-1]['value'],ident+':terminal_effect')
            wrong=sum(z['widget']!='ROOT:1' or bool(z['live']) for z in presses if z['key']=='b')
            directed=s not in ('NORMAL','MISSING_CHILD')
            expect_wrong=(m=='COUNT_ONLY_POP' and directed)
            require(wrong==int(expect_wrong),ident+':wrong_surface_discriminator')
            expected_root='a' if s=='MISSING_CHILD' or expect_wrong else 'ab'
            require(r['final']['root']==expected_root,ident+':root_effect')
            values=[(z['widget'],z['value']) for z in j if z['kind']=='value']
            require(values==[('ROOT:1','a')]+([('P:1','b') if expect_wrong else ('ROOT:1','ab')] if resumed else []),ident+':independent_value_trace')
            if resumed:
                app_b=next(z for z in presses if z['key']=='b')
                parent_close=next(z for z in j if z['kind']=='closed' and z['frame']['id']=='P')
                require((app_b['ns']<parent_close['ns'])==bool(expect_wrong),ident+':parent_close_effect_order')
            for d in deliveries:
                require(d['ns']>=d['receipt']['closed_ns'],ident+':receipt_after_close')
            expected_retired=['']*(3 if s=='OLD_GENERATION_CHILD' else 2)
            if expect_wrong: expected_retired[-1]='b'
            require([z['text'] for z in r['final']['retired']]==expected_retired,ident+':retired_effect')
            require([z['frame'] for z in r['final']['retired']]==[{k:c[k] for k in FIELDS} for c in closed],ident+':retired_lineage')
            if m=='LINEAGE_BOUND_POP':
                counts['candidate_wrong']+=wrong
                counts['candidate_complete']+=int(r['final']['root']=='ab')
                counts['candidate_unresolved']+=int(s=='MISSING_CHILD' and not resumed and bool(state))
            else: counts['weak_wrong']+=wrong
        except (KeyError,TypeError,IndexError,ValueError) as exc:
            errors.append(ident+':malformed:'+type(exc).__name__)
    require(len(seen)==len(expected) and len(set(seen))==len(seen) and set(seen)==expected,'denominator')
    require(counts==dict(candidate_complete=5*len(reps),candidate_unresolved=len(reps),candidate_wrong=0,weak_wrong=4*len(reps)),'aggregate_gates')
    return dict(decision='PASS_NESTED_INTERRUPT_LINEAGE_SCOPED' if not errors else 'HOLD_OR_FAIL_REQUIRES_CLASSIFICATION',checks=checks,errors=errors,counts=counts,cases=len(records))

def load(root):
    records=[];integrity=[]
    for batchpath in sorted(Path(root).glob('batch-*/BATCH.json')):
        b=json.loads(batchpath.read_text());folder=batchpath.parent
        if b['status']!='COMPLETE': integrity.append(str(batchpath)+':incomplete_batch')
        if len(b['cases'])!=12: integrity.append(str(batchpath)+':batch_denominator')
        for c in b['cases']:
            p=folder/c['path'];raw=(p/'row.json').read_bytes();r=json.loads(raw)
            if hashlib.sha256(raw).hexdigest()!=c['row_sha256']: integrity.append(str(p)+':row_digest')
            jb=(p/'app.jsonl').read_bytes()
            if hashlib.sha256(jb).hexdigest()!=r['app_journal_sha256']: integrity.append(str(p)+':journal_digest')
            records.append(dict(row=r,journal=[json.loads(x) for x in jb.splitlines()]))
    return records,integrity

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('--reps',nargs='+',type=int,required=True);p.add_argument('--freeze');p.add_argument('--out',required=True)
    a=p.parse_args();records,integrity=load(a.root)
    sources=json.loads(Path(a.freeze).read_text())['sources'] if a.freeze else None
    result=audit(records,a.reps,sources)
    result['integrity_errors']=integrity
    if integrity: result['decision']='HOLD_INTEGRITY'
    Path(a.out).write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))
    raise SystemExit(bool(result['errors'] or integrity))
