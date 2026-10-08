from __future__ import annotations

EXPECTED_SOURCE = {
    'session_map01_v13_git_blob': '51c644ce424e41bb2cd3d401a52b6c9820f70135',
    'doom_retained_input_backend_v3_git_blob': '65d3f1a7b21af09ab8fe10ef883e3e17a9f6cb27',
    'input_transition_owner_v3_git_blob': '0ea631abcf6272f0538a9ef9198ad8069b47b464',
    'input_owner_v12_sha256': 'b63e8a925a5ff741385fb69b8cf20ac07e01a520f34607778d8d28a0256c1508',
    'adapter_contract_sha256': 'ed7e4f00675e79a9ef86984c7c129bb6c3eda64855c6c71821c313c9feb9badf',
}

DOWN_OK = 'CONFIRMED_PHYSICAL_DOWN'
UP_OK = 'CONFIRMED_PHYSICAL_UP'
DOWN_STATUSES = {DOWN_OK, 'OWNER_ALREADY_HELD', 'PREEXISTING_PHYSICAL_DOWN', 'PRESS_UNCONFIRMED'}
UP_STATUSES = {UP_OK, 'NOOP_ALREADY_UP', 'FOREIGN_OR_STALE_DOWN', 'OWNER_PHYSICAL_MISMATCH', 'RELEASE_UNCONFIRMED'}


def _nonblank(x):
    return type(x) is str and bool(x.strip())


def _edge(e, edge):
    if type(e) is not dict or e.get('edge') != edge:
        raise ValueError('edge')
    allowed = DOWN_STATUSES if edge == 'down' else UP_STATUSES
    status = e.get('status')
    if status not in allowed:
        raise ValueError('edge_status')
    if any(not _nonblank(e.get(k)) for k in ('actuation_id','owner_id','intent_token','key')):
        raise ValueError('edge_lineage')
    confirmed = status == (DOWN_OK if edge == 'down' else UP_OK)
    iv = e.get('interval')
    if confirmed:
        if not isinstance(iv, (list,tuple)) or len(iv) != 2:
            raise ValueError('edge_interval')
        a,b = iv
        if type(a) is not int or type(b) is not int or a < 0 or b < a:
            raise ValueError('edge_interval')
        return (a,b)
    if iv is not None:
        raise ValueError('nonconfirmed_interval')
    return None


def _release_row(r):
    if type(r) is not dict:
        raise ValueError('release_row')
    if r.get('event') != 'input_release_transition' or r.get('operation') != 'up':
        raise ValueError('release_event')
    if r.get('transition_schema') != 'input-release-transition-v3':
        raise ValueError('release_schema')
    if r.get('release_batch_schema') != 'input-release-batch-v3':
        raise ValueError('batch_schema')
    if r.get('ordinary_release_candidate') is not True or r.get('owner_transition_verified') is not True:
        raise ValueError('unverified_release')
    # Current v3 metadata may bind a program but must never be treated as physical truth.
    if r.get('physical_verification_authoritative') is not False:
        raise ValueError('v3_physical_authority')
    if r.get('grants_input_authority') is not False:
        raise ValueError('authority')
    for k in ('release_batch_identifier','owner_id','intent_token','key'):
        if not _nonblank(r.get(k)):
            raise ValueError('release_lineage')
    step=r.get('release_batch_step'); pos=r.get('release_batch_position'); size=r.get('release_batch_size')
    if type(step) is not int or step < 0 or type(pos) is not int or pos < 0 or type(size) is not int or size < 1:
        raise ValueError('batch_shape')
    s=r.get('release_call_started_ns'); t=r.get('release_call_returned_ns')
    if type(s) is not int or type(t) is not int or s < 0 or t < s:
        raise ValueError('release_rpc_interval')
    return (s,t)


def bind_batch(release_rows, physical_pairs, source_identity):
    if source_identity != EXPECTED_SOURCE:
        return {'status':'SOURCE_IDENTITY_DRIFT','actuations':None,'grants_input_authority':False}
    if not isinstance(release_rows,list) or not release_rows:
        return {'status':'INVALID_BATCH','actuations':None,'grants_input_authority':False}
    if not isinstance(physical_pairs,dict):
        return {'status':'INVALID_PHYSICAL_MAP','actuations':None,'grants_input_authority':False}
    try:
        rpc={id(r):_release_row(r) for r in release_rows}
    except ValueError as e:
        return {'status':'RELEASE_'+str(e).upper(),'actuations':None,'grants_input_authority':False}

    base=release_rows[0]
    ident=base['release_batch_identifier']; step=base['release_batch_step']; size=base['release_batch_size']
    if size != len(release_rows):
        return {'status':'BATCH_SIZE_MISMATCH','actuations':None,'grants_input_authority':False}
    if any((r['release_batch_identifier'],r['release_batch_step'],r['release_batch_size']) != (ident,step,size) for r in release_rows):
        return {'status':'BATCH_CONTEXT_MISMATCH','actuations':None,'grants_input_authority':False}
    positions=[r['release_batch_position'] for r in release_rows]
    if sorted(positions) != list(range(size)) or len(set(positions)) != size:
        return {'status':'BATCH_POSITION_MISMATCH','actuations':None,'grants_input_authority':False}
    keys=[r['key'] for r in release_rows]
    if len(set(keys)) != size or set(physical_pairs) != set(keys):
        return {'status':'KEY_SET_MISMATCH','actuations':None,'grants_input_authority':False}

    out=[]; seen_act=set()
    for r in sorted(release_rows,key=lambda x:x['release_batch_position']):
        pair=physical_pairs.get(r['key'])
        if not isinstance(pair,(list,tuple)) or len(pair)!=2:
            return {'status':'MISSING_PHYSICAL_PAIR','actuations':None,'grants_input_authority':False}
        d,u=pair
        try:
            div=_edge(d,'down'); uiv=_edge(u,'up')
        except ValueError as e:
            return {'status':'PHYSICAL_'+str(e).upper(),'actuations':None,'grants_input_authority':False}
        lineage=('actuation_id','owner_id','intent_token','key')
        if any(d[k] != u[k] for k in lineage):
            return {'status':'PHYSICAL_LINEAGE_MISMATCH','actuations':None,'grants_input_authority':False}
        if d['status'] != DOWN_OK or u['status'] != UP_OK:
            return {'status':'INCOMPLETE_PHYSICAL_EVIDENCE','actuations':None,'grants_input_authority':False}
        if div[1] > uiv[0]:
            return {'status':'PHYSICAL_EDGE_ORDER_AMBIGUOUS','actuations':None,'grants_input_authority':False}
        if any(d[k] != r[k] for k in ('owner_id','intent_token','key')):
            return {'status':'MAP01_PHYSICAL_LINEAGE_MISMATCH','actuations':None,'grants_input_authority':False}
        if d['actuation_id'] in seen_act:
            return {'status':'DUPLICATE_ACTUATION_ID','actuations':None,'grants_input_authority':False}
        seen_act.add(d['actuation_id'])
        rs,re=rpc[id(r)]
        # The authoritative v12 UP bracket must be nested inside the same outer MAP01 release RPC.
        # This binds the physical UP evidence to that release request without replacing/narrowing either interval.
        if not (rs <= uiv[0] <= uiv[1] <= re):
            return {'status':'UP_NOT_WITHIN_RELEASE_RPC','actuations':None,'grants_input_authority':False}
        out.append({
            'id':ident,'step':step,'batch_size':size,'batch_position':r['release_batch_position'],
            'actuation_id':d['actuation_id'],'owner_id':d['owner_id'],'intent_token':d['intent_token'],'key':d['key'],
            'physical_down_interval':list(div),'physical_up_interval':list(uiv),
            'map01_release_rpc_interval':[rs,re],
            'physical_evidence_authoritative':True,
            'map01_v3_physical_authoritative':False,
            'grants_input_authority':False,
        })
    return {'status':'BOUND_MAP01_PHYSICAL_BATCH','actuations':out,'grants_input_authority':False}
