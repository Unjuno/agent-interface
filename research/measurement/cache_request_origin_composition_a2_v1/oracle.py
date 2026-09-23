from candidate import VALID,HARD,AMBIG,SCOPES

def new_state():
    return {'epochs':{s:0 for s in SCOPES},'requests':{},'cache':{s:None for s in SCOPES},'regime':{s:VALID for s in SCOPES},'invalidations':set(),'responses':set(),'authority_promotions':0}
def snapshot(s):
    return {'epochs':dict(s['epochs']),'requests':{k:dict(v) for k,v in sorted(s['requests'].items())},'cache':{k:(None if v is None else dict(v)) for k,v in s['cache'].items()},'regime':dict(s['regime']),'invalidations':sorted(s['invalidations']),'responses':sorted(s['responses']),'authority_promotions':s['authority_promotions']}
def apply(s,op):
    k=op['op'];scope=op.get('scope')
    if k=='BEGIN':
        rid=op.get('request_id');auth=op.get('authority',False)
        if scope not in s['epochs'] or not isinstance(rid,str) or not rid or rid in s['requests'] or auth is not False:return {'status':'REFUSE_MALFORMED'}
        s['requests'][rid]={'scope':scope,'origin_epoch':s['epochs'][scope],'planner_generation':op.get('planner_generation')};return {'status':'REQUEST_BEGUN','origin_epoch':s['epochs'][scope]}
    if k=='INVALIDATE':
        iid=op.get('invalidation_id')
        if scope not in s['epochs'] or not isinstance(iid,str) or not iid:return {'status':'REFUSE_MALFORMED'}
        key=(scope,iid)
        if key in s['invalidations']:return {'status':'DUPLICATE_INVALIDATION','epoch':s['epochs'][scope]}
        s['invalidations'].add(key);s['epochs'][scope]+=1;return {'status':'INVALIDATED','epoch':s['epochs'][scope]}
    if k=='INSTALL':
        rid=op.get('request_id');resp=op.get('response_id');auth=op.get('authority',False)
        if scope not in s['epochs'] or not isinstance(resp,str) or not resp or resp in s['responses'] or auth is not False:return {'status':'REFUSE_MALFORMED'}
        req=s['requests'].get(rid)
        if req is None or req['scope']!=scope:return {'status':'REFUSE_REQUEST'}
        s['responses'].add(resp);s['requests'].pop(rid,None)
        if req['origin_epoch']!=s['epochs'][scope]:return {'status':'REFUSE_STALE_ORIGIN','origin_epoch':req['origin_epoch'],'current_epoch':s['epochs'][scope]}
        s['cache'][scope]={'response_id':resp,'request_origin_epoch':req['origin_epoch'],'installed_epoch':s['epochs'][scope],'planner_generation':op.get('planner_generation'),'grants_authority':False};return {'status':'INSTALLED','epoch':s['epochs'][scope]}
    if k=='OBSERVE':
        reg=op.get('regime')
        if scope not in s['epochs'] or reg not in (VALID,HARD,AMBIG):return {'status':'REFUSE_MALFORMED'}
        s['regime'][scope]=reg;return {'status':'OBSERVED','regime':reg}
    if k=='USE':
        if scope not in s['epochs']:return {'status':'REFUSE_MALFORMED','effect':False}
        c=s['cache'][scope];reg=s['regime'][scope]
        if c is None:return {'status':'NO_CACHE','effect':False}
        if c['installed_epoch']!=s['epochs'][scope]:return {'status':'REFUSE_STALE_CACHE','effect':False}
        if reg==HARD:return {'status':'REFUSE_HARD','effect':False}
        if reg==AMBIG:return {'status':'YIELD_AMBIGUOUS','effect':False}
        return {'status':'EFFECT','effect':True}
    return {'status':'REFUSE_MALFORMED'}
