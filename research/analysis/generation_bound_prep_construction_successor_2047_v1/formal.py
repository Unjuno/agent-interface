import json

def select(cache, current_generation, request_generation):
    if request_generation != current_generation: return 'WAIT'
    if cache.get('generation') != current_generation: return 'REBUILD'
    if cache.get('status') != 'READY': return 'REBUILD'
    if cache.get('timestamp') is None: return 'WAIT'
    return 'REUSE'

def main():
    cur=7
    cases=[({'generation':7,'status':'READY','timestamp':1},7,'REUSE'),({'generation':6,'status':'READY','timestamp':1},7,'REBUILD'),({'generation':7,'status':'ENCODING','timestamp':1},7,'REBUILD'),({'generation':7,'status':'READY','timestamp':None},7,'WAIT'),({'generation':7,'status':'READY','timestamp':1},6,'WAIT')]
    assert all(select(c,cur,g)==expected for c,g,expected in cases)
    result={'cases':len(cases),'reuse':1,'rebuild':2,'wait':2,'status':'PASS_GENERATION_BOUND_PREPARATION_CONSTRUCTION_SCOPED','model_utility':None,'stale_exposure':False}
    open('result.json','w').write(json.dumps(result,sort_keys=True,indent=2)+'\n'); print(json.dumps(result,sort_keys=True))
if __name__=='__main__': main()
