VALID='VALID_CONTINUATION'; HARD='HARD_INVALIDATION'; AMBIG='AMBIGUOUS_BOUNDARY'
SCOPES=('A','B','C','D')

class RequestOriginBound:
    def __init__(self):
        self.epochs={s:0 for s in SCOPES}; self.requests={}; self.cache={s:None for s in SCOPES}; self.regime={s:VALID for s in SCOPES}; self.invalidations=set(); self.responses=set(); self.authority_promotions=0
    def snapshot(self):
        return {'epochs':dict(self.epochs),'requests':{k:dict(v) for k,v in sorted(self.requests.items())},'cache':{k:(None if v is None else dict(v)) for k,v in self.cache.items()},'regime':dict(self.regime),'invalidations':sorted(self.invalidations),'responses':sorted(self.responses),'authority_promotions':self.authority_promotions}
    def begin(self,scope,request_id,planner_generation,authority=False):
        if scope not in self.epochs or not isinstance(request_id,str) or not request_id or request_id in self.requests or authority is not False:return {'status':'REFUSE_MALFORMED'}
        self.requests[request_id]={'scope':scope,'origin_epoch':self.epochs[scope],'planner_generation':planner_generation}
        return {'status':'REQUEST_BEGUN','origin_epoch':self.epochs[scope]}
    def invalidate(self,scope,invalidation_id):
        if scope not in self.epochs or not isinstance(invalidation_id,str) or not invalidation_id:return {'status':'REFUSE_MALFORMED'}
        key=(scope,invalidation_id)
        if key in self.invalidations:return {'status':'DUPLICATE_INVALIDATION','epoch':self.epochs[scope]}
        self.invalidations.add(key);self.epochs[scope]+=1
        return {'status':'INVALIDATED','epoch':self.epochs[scope]}
    def install(self,scope,request_id,response_id,planner_generation,authority=False):
        if scope not in self.epochs or not isinstance(response_id,str) or not response_id or response_id in self.responses or authority is not False:return {'status':'REFUSE_MALFORMED'}
        req=self.requests.get(request_id)
        if req is None or req['scope']!=scope:return {'status':'REFUSE_REQUEST'}
        self.responses.add(response_id); self.requests.pop(request_id,None)
        if req['origin_epoch']!=self.epochs[scope]:return {'status':'REFUSE_STALE_ORIGIN','origin_epoch':req['origin_epoch'],'current_epoch':self.epochs[scope]}
        self.cache[scope]={'response_id':response_id,'request_origin_epoch':req['origin_epoch'],'installed_epoch':self.epochs[scope],'planner_generation':planner_generation,'grants_authority':False}
        return {'status':'INSTALLED','epoch':self.epochs[scope]}
    def observe(self,scope,regime):
        if scope not in self.epochs or regime not in (VALID,HARD,AMBIG):return {'status':'REFUSE_MALFORMED'}
        self.regime[scope]=regime;return {'status':'OBSERVED','regime':regime}
    def use(self,scope):
        if scope not in self.epochs:return {'status':'REFUSE_MALFORMED','effect':False}
        c=self.cache[scope];r=self.regime[scope]
        if c is None:return {'status':'NO_CACHE','effect':False}
        if c['installed_epoch']!=self.epochs[scope]:return {'status':'REFUSE_STALE_CACHE','effect':False}
        if r==HARD:return {'status':'REFUSE_HARD','effect':False}
        if r==AMBIG:return {'status':'YIELD_AMBIGUOUS','effect':False}
        return {'status':'EFFECT','effect':True}

class InstallTimeOnly(RequestOriginBound):
    def install(self,scope,request_id,response_id,planner_generation,authority=False):
        if scope not in self.epochs or not isinstance(response_id,str) or not response_id or response_id in self.responses or authority is not False:return {'status':'REFUSE_MALFORMED'}
        req=self.requests.get(request_id)
        if req is None or req['scope']!=scope:return {'status':'REFUSE_REQUEST'}
        self.responses.add(response_id); self.requests.pop(request_id,None)
        self.cache[scope]={'response_id':response_id,'request_origin_epoch':req['origin_epoch'],'installed_epoch':self.epochs[scope],'planner_generation':planner_generation,'grants_authority':False}
        return {'status':'INSTALLED','epoch':self.epochs[scope]}
