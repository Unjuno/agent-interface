import copy,hashlib,json,sys
from pathlib import Path
POLICIES=['RAW_KEYSYM','SNAPSHOT_SYMBOLIC','CURRENT_SYMBOLIC']
CONDS=['US_UNDO','DE_UNDO','MODAL_CONFIRM','NO_MODAL_CONFIRM','STALE_CONTEXT_MODAL_TO_EDITOR','LAYOUT_CHANGED_US_TO_DE_UNDO']
ALLOWED={'UNDO':'EDITOR','CONFIRM':'MODAL'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def expected_decision(spec,plan,cur):
    policy=spec['policy'];intent='CONFIRM' if 'CONFIRM' in spec['condition'] or 'CONTEXT' in spec['condition'] else 'UNDO'
    if policy=='RAW_KEYSYM':return 'EMIT'
    if policy=='SNAPSHOT_SYMBOLIC':
        if plan['layout_hash']!=cur['layout_hash']:return 'REFUSE_STALE_LAYOUT'
        if plan['mode']!=cur['mode']:return 'REFUSE_STALE_CONTEXT'
        return 'EMIT' if ALLOWED[intent]==plan['mode'] else 'REFUSE_CONTEXT'
    return 'EMIT' if ALLOWED[intent]==cur['mode'] else 'REFUSE_CONTEXT'
def expected_effect(spec):
    p,c=spec['policy'],spec['condition']
    zero={'undo_delta':0,'redo_delta':0,'confirm_delta':0,'stray_delta':0}
    if c in ('US_UNDO','DE_UNDO'):return dict(zero,undo_delta=1)
    if c=='MODAL_CONFIRM':return dict(zero,confirm_delta=1)
    if c in ('NO_MODAL_CONFIRM','STALE_CONTEXT_MODAL_TO_EDITOR'):
        return dict(zero,stray_delta=1) if p=='RAW_KEYSYM' else zero
    if c=='LAYOUT_CHANGED_US_TO_DE_UNDO':
        if p=='RAW_KEYSYM':return dict(zero,redo_delta=1)
        if p=='CURRENT_SYMBOLIC':return dict(zero,undo_delta=1)
        return zero
    raise AssertionError(c)
def row_errors(r,spec):
    e=[]
    def ck(x,label):
        if not x:e.append(label)
    ck(r.get('spec')==spec,'spec')
    ck(r.get('error') is None,'runtime_error')
    ck(r.get('app_exit')==0 and r.get('xvfb_exit')==0 and r.get('socket_absent') is True,'process_cleanup')
    ck(r.get('initial_native',{}).get('neutral') is True and r.get('terminal_native',{}).get('neutral') is True,'neutral')
    plan,current=r.get('plan',{}),r.get('current',{})
    if spec['condition']=='LAYOUT_CHANGED_US_TO_DE_UNDO':ck(plan.get('layout_hash')!=current.get('layout_hash'),'layout_change')
    else:ck(plan.get('layout_hash')==current.get('layout_hash'),'layout_stable')
    if spec['condition']=='STALE_CONTEXT_MODAL_TO_EDITOR':ck((plan.get('mode'),current.get('mode'))==('MODAL','EDITOR'),'context_change')
    else:ck(plan.get('mode')==current.get('mode'),'context_stable')
    out=r.get('policy_output',{});decision=expected_decision(spec,plan,current)
    ck(out.get('decision')==decision and out.get('grants_action_authority') is False,'decision')
    emit=decision=='EMIT';events=r.get('native_events',[])
    intent='CONFIRM' if 'CONFIRM' in spec['condition'] or 'CONTEXT' in spec['condition'] else 'UNDO'
    ck(len(events)==(4 if emit and intent=='UNDO' else 2 if emit else 0),'native_event_count')
    if emit:
        ck(all(type(x.get('keycode')) is int and x['keycode']>0 for x in events),'keycodes')
        ck([x['down'] for x in events]==([True,True,False,False] if intent=='UNDO' else [True,False]),'press_release_order')
    got=dict(r.get('semantic_effect',{}));got.pop('expected',None)
    ck(got==expected_effect(spec),'semantic_effect')
    kinds=[x['kind'] for x in r.get('final_state',{}).get('events',[])]
    want=[]
    eff=expected_effect(spec)
    if eff['undo_delta']:want=['UNDO']
    if eff['redo_delta']:want=['REDO']
    if eff['confirm_delta']:want=['CONFIRM']
    if eff['stray_delta']:want=['STRAY_RETURN']
    ck(kinds==want,'app_journal')
    return e
def audit(root,controls=False):
    root=Path(root);schedule=json.loads((root/'SCHEDULE.json').read_text());freeze=json.loads((root/'FREEZE.json').read_text());errors=[];checks=0
    def ck(x,label):
        nonlocal checks;checks+=1
        if not x:errors.append(label)
    for rel,h in freeze['files'].items():ck(sha(root/rel)==h,'source:'+rel)
    rows=[]
    for i,spec in enumerate(schedule):
        p=root/'formal'/f'{i:02d}'/'ROW.json';ck(p.is_file(),f'{i}:row')
        if not p.is_file():continue
        r=json.loads(p.read_text());rows.append(r)
        es=row_errors(r,spec);checks+=12+len(r.get('native_events',[]));errors.extend(f'{i}:{x}' for x in es)
    counts={p:{'cases':0,'exact':0,'wrong':0,'refused':0} for p in POLICIES}
    for r in rows:
        c=counts[r['spec']['policy']];c['cases']+=1;d=r['policy_output']['decision'];eff=expected_effect(r['spec']);got=dict(r['semantic_effect']);got.pop('expected',None)
        c['refused']+=int(d!='EMIT');c['exact']+=int(d=='EMIT' and got==eff and (eff['undo_delta'] or eff['confirm_delta']));c['wrong']+=int(d=='EMIT' and not (got.get('undo_delta')==1 or got.get('confirm_delta')==1))
    ck(len(rows)==36,'denominator')
    ck(counts['RAW_KEYSYM']=={'cases':12,'exact':6,'wrong':6,'refused':0},'raw_gate')
    ck(counts['SNAPSHOT_SYMBOLIC']=={'cases':12,'exact':6,'wrong':0,'refused':6},'snapshot_gate')
    ck(counts['CURRENT_SYMBOLIC']=={'cases':12,'exact':8,'wrong':0,'refused':4},'current_gate')
    controls_out=[]
    if controls and len(rows)==36:
        muts=[]
        def add(name,index,fn):
            x=copy.deepcopy(rows[index]);fn(x);muts.append((name,index,x))
        add('authority_true',0,lambda x:x['policy_output'].__setitem__('grants_action_authority',True))
        add('effect_flip',0,lambda x:x['semantic_effect'].__setitem__('undo_delta',0))
        add('neutral_false',0,lambda x:x['terminal_native'].__setitem__('neutral',False))
        add('exit_nonzero',0,lambda x:x.__setitem__('app_exit',1))
        add('drop_event',0,lambda x:x['native_events'].pop())
        li=next(i for i,r in enumerate(rows) if r['spec']['condition']=='LAYOUT_CHANGED_US_TO_DE_UNDO' and r['spec']['policy']=='RAW_KEYSYM')
        add('hide_layout_change',li,lambda x:x['current'].__setitem__('layout_hash',x['plan']['layout_hash']))
        si=next(i for i,r in enumerate(rows) if r['spec']['condition']=='STALE_CONTEXT_MODAL_TO_EDITOR' and r['spec']['policy']=='CURRENT_SYMBOLIC')
        add('hide_context_change',si,lambda x:x['current'].__setitem__('mode','MODAL'))
        ri=next(i for i,r in enumerate(rows) if r['spec']['condition']=='NO_MODAL_CONFIRM' and r['spec']['policy']=='CURRENT_SYMBOLIC')
        add('force_emit',ri,lambda x:x['policy_output'].__setitem__('decision','EMIT'))
        for name,index,x in muts:
            es=row_errors(x,schedule[index]);controls_out.append({'name':name,'rejected':bool(es),'errors':es})
            ck(bool(es),'control:'+name)
    return {'decision':'PASS_CURRENT_SYMBOLIC_KEYBOARD_SCOPED' if not errors else 'HOLD_OR_FAIL','checks':checks,'cases':len(rows),'counts':counts,'errors':errors,'controls':controls_out,'model_evaluation':False,'runtime_promotion':False}
if __name__=='__main__':
 r=audit(sys.argv[1],'--controls' in sys.argv);print(json.dumps(r,indent=2,sort_keys=True));sys.exit(0 if not r['errors'] else 1)
