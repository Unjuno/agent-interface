from __future__ import annotations
import hashlib,json
CAPS=('XTEST_INPUT','CORE_INPUT_FALLBACK','OBSERVE_CONTEXT')
OBL={'XTEST_INPUT':'POINTER_KEY_INPUT','CORE_INPUT_FALLBACK':'POINTER_KEY_INPUT','OBSERVE_CONTEXT':'OBSERVE_CONTEXT'}
FB={'XTEST_INPUT':'CORE_INPUT_FALLBACK'}
REV='fallback-v1'

def snapshot_id(scope,generation,supported,authority=False):
    obj={'scope':str(scope),'generation':int(generation),'supported':sorted(supported),'fallback_revision':REV,'authority':bool(authority)}
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def mint(scope,generation,supported):
    supported=tuple(sorted(supported))
    return {'scope':str(scope),'generation':int(generation),'supported':supported,'runtime_owned':True,'authority':False,'snapshot_id':snapshot_id(scope,generation,supported,False),'fallback_revision':REV}

def resolve(current,snap,request):
    invalid=lambda reason:{'disposition':reason,'selected':None,'grants_action_authority':False}
    if not snap.get('runtime_owned'): return invalid('INVALID_PROVENANCE')
    if snap.get('authority'): return invalid('INVALID_AUTHORITY_FRAME')
    if snap.get('fallback_revision')!=REV: return invalid('INVALID_FALLBACK_REVISION')
    if snap.get('snapshot_id')!=snapshot_id(snap.get('scope'),snap.get('generation'),snap.get('supported',()),False): return invalid('INVALID_DIGEST')
    if snap.get('snapshot_id')!=snapshot_id(current['scope'],current['generation'],current['supported'],False): return invalid('STALE_OR_WRONG_SCOPE')
    if snap.get('scope')!=current['scope'] or snap.get('generation')!=current['generation']: return invalid('STALE_OR_WRONG_SCOPE')
    S=set(snap['supported'])
    if request in S: return {'disposition':'DIRECT','selected':request,'grants_action_authority':False}
    fb=FB.get(request)
    if fb and fb in S and OBL[request]==OBL[fb]: return {'disposition':'FALLBACK','selected':fb,'grants_action_authority':False}
    return {'disposition':'UNSUPPORTED','selected':None,'grants_action_authority':False}
