from __future__ import annotations
PINNED=(
 '842071284156d3ccc647f47135ee62a9e512cb56',
 'cf13d630ae22a50272a766c86d7f325f352a89d7',
 '0482cf4c08b8c04d524a3eac11b798f07f0e0524')

def judge(d,u,s):
    def no(r): return (False,r,None)
    if tuple(s.get(k) for k in ('input_owner_v11_git_blob','doom_typed_release_backend_v2_git_blob','actuation_candidate_git_blob'))!=PINNED:nope=no('source_identity_drift');return nope
    if not isinstance(d,dict) or not isinstance(u,dict): return no('missing_evidence')
    if d.get('event')!='input_admission': return no('unexpected_down_event')
    if (u.get('event'),u.get('operation'))!=('input_release_rpc','up'): return no('unexpected_up_event_or_operation')
    if bool(d.get('grants_input_authority',False)) or u.get('grants_input_authority') is not False: return no('authority_contradiction')
    if u.get('x11_release_and_sync_completed_before_return') is not True: return no('release_completion_unproven')
    vals=[]
    for k in ('id','step','owner_id','intent_token'):
        if k not in d or k not in u:return no('missing_lineage')
        if d[k]!=u[k]:return no('lineage_mismatch')
        vals.append(d[k])
    if not isinstance(d.get('key'),str) or not d.get('key') or d.get('key')!=u.get('payload'): return no('key_mismatch')
    ts=[d.get('admitted_ns'),d.get('input_ack_ns'),u.get('call_started_ns'),u.get('call_returned_ns')]
    if not all(type(x) is int for x in ts):
        return no('malformed_down_timestamp' if any(type(x) is not int for x in ts[:2]) else 'malformed_up_timestamp')
    if not (0<=ts[0]<=ts[1]<=ts[2]<=ts[3]):return no('crossed_or_invalid_intervals')
    if u.get('release_transition_interval_ns')!=ts[2:]:return no('release_interval_mismatch')
    if u.get('interval_width_ns')!=ts[3]-ts[2]:return no('release_width_mismatch')
    aid=f'{vals[0]}:{vals[1]}:{vals[2]}:{vals[3]}:{d["key"]}'
    return True,'accepted',{'actuation_id':aid,'down_lo':ts[0],'down_hi':ts[1],'up_lo':ts[2],'up_hi':ts[3],'authority':()}
