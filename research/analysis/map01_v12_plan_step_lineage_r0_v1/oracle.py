from __future__ import annotations

DOWN='CONFIRMED_PHYSICAL_DOWN'; UP='CONFIRMED_PHYSICAL_UP'
EXPECTED_SOURCE={
'session_map01_v13_git_blob':'51c644ce424e41bb2cd3d401a52b6c9820f70135',
'doom_retained_input_backend_v3_git_blob':'65d3f1a7b21af09ab8fe10ef883e3e17a9f6cb27',
'input_transition_owner_v3_git_blob':'0ea631abcf6272f0538a9ef9198ad8069b47b464',
'input_owner_v12_sha256':'b63e8a925a5ff741385fb69b8cf20ac07e01a520f34607778d8d28a0256c1508',
'adapter_contract_sha256':'ed7e4f00675e79a9ef86984c7c129bb6c3eda64855c6c71821c313c9feb9badf'}

def nb(x):return type(x) is str and bool(x.strip())
def oracle(rows,pairs,source):
    # Independent boolean specification. It deliberately does not reproduce candidate reason precedence.
    if source != EXPECTED_SOURCE or type(rows) is not list or not rows or type(pairs) is not dict:return False
    n=len(rows); ids=[]; poss=[]; keys=[]; acts=[]
    batch=None
    for r in rows:
        try:
            if r['event']!='input_release_transition' or r['operation']!='up':return False
            if r['transition_schema']!='input-release-transition-v3' or r['release_batch_schema']!='input-release-batch-v3':return False
            if r['ordinary_release_candidate'] is not True or r['owner_transition_verified'] is not True:return False
            if r['physical_verification_authoritative'] is not False or r['grants_input_authority'] is not False:return False
            if any(not nb(r[k]) for k in ('release_batch_identifier','owner_id','intent_token','key')):return False
            if type(r['release_batch_step']) is not int or r['release_batch_step']<0:return False
            if type(r['release_batch_position']) is not int or r['release_batch_position']<0:return False
            if type(r['release_batch_size']) is not int or r['release_batch_size']<1:return False
            if type(r['release_call_started_ns']) is not int or type(r['release_call_returned_ns']) is not int:return False
            if not 0<=r['release_call_started_ns']<=r['release_call_returned_ns']:return False
        except Exception:return False
        b=(r['release_batch_identifier'],r['release_batch_step'],r['release_batch_size'])
        if batch is None:batch=b
        elif b!=batch:return False
        poss.append(r['release_batch_position']);keys.append(r['key'])
    if batch[2]!=n or sorted(poss)!=list(range(n)) or len(set(poss))!=n or len(set(keys))!=n:return False
    if set(pairs)!=set(keys):return False
    for r in rows:
        try:d,u=pairs[r['key']]
        except Exception:return False
        for e,want,statuses in ((d,'down',{DOWN,'OWNER_ALREADY_HELD','PREEXISTING_PHYSICAL_DOWN','PRESS_UNCONFIRMED'}),(u,'up',{UP,'NOOP_ALREADY_UP','FOREIGN_OR_STALE_DOWN','OWNER_PHYSICAL_MISMATCH','RELEASE_UNCONFIRMED'})):
            if type(e) is not dict or e.get('edge')!=want or e.get('status') not in statuses:return False
            if any(not nb(e.get(k)) for k in ('actuation_id','owner_id','intent_token','key')):return False
            confirmed=e['status']==(DOWN if want=='down' else UP)
            iv=e.get('interval')
            if confirmed:
                if not isinstance(iv,(list,tuple)) or len(iv)!=2:return False
                if any(type(x) is not int for x in iv) or iv[0]<0 or iv[1]<iv[0]:return False
            elif iv is not None:return False
        if any(d[k]!=u[k] for k in ('actuation_id','owner_id','intent_token','key')):return False
        if d['status']!=DOWN or u['status']!=UP:return False
        if d['interval'][1]>u['interval'][0]:return False
        if any(d[k]!=r[k] for k in ('owner_id','intent_token','key')):return False
        if d['actuation_id'] in acts:return False
        acts.append(d['actuation_id'])
        if not (r['release_call_started_ns']<=u['interval'][0]<=u['interval'][1]<=r['release_call_returned_ns']):return False
    return True
