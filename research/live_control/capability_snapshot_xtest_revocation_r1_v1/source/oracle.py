from __future__ import annotations
import hashlib,json
OBL={'XTEST_INPUT':'POINTER_KEY_INPUT','CORE_INPUT_FALLBACK':'POINTER_KEY_INPUT','OBSERVE_CONTEXT':'OBSERVE_CONTEXT'}
REV='fallback-v1'

def sid(scope,generation,supported):
    obj={'authority':False,'fallback_revision':REV,'generation':int(generation),'scope':str(scope),'supported':sorted(supported)}
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def resolve(current,snap,request):
    if not snap['runtime_owned'] or snap['authority'] or snap['fallback_revision']!=REV:return ('INVALID',None,False)
    if snap['snapshot_id']!=sid(snap['scope'],snap['generation'],snap['supported']):return ('INVALID',None,False)
    if snap['snapshot_id']!=sid(current['scope'],current['generation'],current['supported']):return ('INVALID',None,False)
    if snap['scope']!=current['scope'] or snap['generation']!=current['generation']:return ('INVALID',None,False)
    S=set(snap['supported'])
    if request in S:return ('DIRECT',request,False)
    if request=='XTEST_INPUT' and 'CORE_INPUT_FALLBACK' in S and OBL[request]==OBL['CORE_INPUT_FALLBACK']:return ('FALLBACK','CORE_INPUT_FALLBACK',False)
    return ('UNSUPPORTED',None,False)
