import json
ALLOWED_OPS={'CLICK','TYPE_TEXT','SCROLL'}
DISPOSITIONS={'ACTION_SET','WATCH','NO_LOCAL_ACTION','YIELD','DONE_CANDIDATE'}
MV_FIELDS={'intent_id','observation_ref','observation_epoch','allowed_operations','targets','payload_refs','prior_receipt_refs'}
ROW_FIELDS={'row_id','episode_id','split_group','split','model_visible','oracle','grants_input_authority'}
ORACLE_FIELDS={'disposition','acceptable_actions','oracle_source_ref','independent','postdecision_refs','done_verifier_ref'}

def _s(x): return type(x) is str and bool(x.strip())
def _canon(x): return json.dumps(x,sort_keys=True,separators=(',',':'))

def _proposal_ok(p,mv,target_by_id,payloads):
    if type(p) is not dict or 'operation' not in p: return False
    op=p.get('operation')
    if op not in ALLOWED_OPS or op not in mv['allowed_operations']: return False
    tid=p.get('target_id')
    if not _s(tid) or tid not in target_by_id or op not in target_by_id[tid]['operations']: return False
    if op=='CLICK': return set(p)=={'operation','target_id'}
    if op=='TYPE_TEXT':
        return set(p)=={'operation','target_id','payload_ref'} and _s(p.get('payload_ref')) and p['payload_ref'] in payloads
    if op=='SCROLL':
        return set(p)=={'operation','target_id','delta'} and type(p.get('delta')) is int and p['delta']!=0 and -3<=p['delta']<=3
    return False

def validate_row(row):
    if type(row) is not dict or set(row)!=ROW_FIELDS: raise ValueError('row_fields')
    if not all(_s(row[k]) for k in ('row_id','episode_id','split_group')): raise ValueError('identity')
    if row['split'] not in ('train','eval'): raise ValueError('split')
    if row['grants_input_authority'] is not False: raise ValueError('authority')
    mv=row['model_visible']; oracle=row['oracle']
    if type(mv) is not dict or set(mv)!=MV_FIELDS: raise ValueError('model_visible_fields')
    if not all(_s(mv[k]) for k in ('intent_id','observation_ref')): raise ValueError('mv_identity')
    if type(mv['observation_epoch']) is not int or mv['observation_epoch']<0: raise ValueError('epoch')
    ops=mv['allowed_operations']
    if type(ops) is not list or not ops or any(op not in ALLOWED_OPS for op in ops) or len(ops)!=len(set(ops)): raise ValueError('ops')
    targets=mv['targets']; payloads=mv['payload_refs']; receipts=mv['prior_receipt_refs']
    if type(targets) is not list or type(payloads) is not list or type(receipts) is not list: raise ValueError('lists')
    if len(payloads)!=len(set(payloads)) or any(not _s(x) for x in payloads+receipts): raise ValueError('refs')
    target_by_id={}
    for t in targets:
        if type(t) is not dict or set(t)!={'target_id','observation_ref','observation_epoch','operations'}: raise ValueError('target_fields')
        tid=t.get('target_id')
        if not _s(tid) or tid in target_by_id: raise ValueError('target_id')
        if t.get('observation_ref')!=mv['observation_ref'] or t.get('observation_epoch')!=mv['observation_epoch']: raise ValueError('target_scope')
        tops=t.get('operations')
        if type(tops) is not list or not tops or any(op not in ops for op in tops) or len(tops)!=len(set(tops)): raise ValueError('target_ops')
        target_by_id[tid]=t
    if type(oracle) is not dict or set(oracle)!=ORACLE_FIELDS: raise ValueError('oracle_fields')
    if oracle['disposition'] not in DISPOSITIONS or not _s(oracle['oracle_source_ref']) or oracle['independent'] is not True: raise ValueError('oracle_identity')
    if type(oracle['postdecision_refs']) is not list or any(not _s(x) for x in oracle['postdecision_refs']): raise ValueError('post_refs')
    acts=oracle['acceptable_actions']
    if type(acts) is not list: raise ValueError('acceptable')
    if oracle['disposition']=='ACTION_SET':
        if not acts or oracle['done_verifier_ref'] is not None: raise ValueError('action_set')
        if any(not _proposal_ok(p,mv,target_by_id,set(payloads)) for p in acts): raise ValueError('proposal')
        cs=[_canon(p) for p in acts]
        if len(cs)!=len(set(cs)): raise ValueError('duplicate_proposal')
    elif oracle['disposition']=='DONE_CANDIDATE':
        if acts or not _s(oracle['done_verifier_ref']): raise ValueError('done')
    else:
        if acts or oracle['done_verifier_ref'] is not None: raise ValueError('nonaction')
    return {'row_id':row['row_id'],'disposition':oracle['disposition'],'acceptable_count':len(acts),'grants_input_authority':False}

def validate_dataset(rows):
    if type(rows) is not list or not rows: raise ValueError('dataset')
    ids=set(); episode_split={}; group_split={}; out=[]
    for r in rows:
        x=validate_row(r)
        if r['row_id'] in ids: raise ValueError('duplicate_row')
        ids.add(r['row_id'])
        for key,map_ in ((r['episode_id'],episode_split),(r['split_group'],group_split)):
            if key in map_ and map_[key]!=r['split']: raise ValueError('split_leakage')
            map_[key]=r['split']
        out.append(x)
    return out
