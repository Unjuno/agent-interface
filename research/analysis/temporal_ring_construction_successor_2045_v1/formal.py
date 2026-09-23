import json

def admissible(obs, request):
    if obs.get('status') != 'AVAILABLE': return 'UNKNOWN'
    if obs.get('surface') != request['surface']: return 'UNKNOWN'
    if obs.get('session') != request['session']: return 'UNKNOWN'
    if not (request['lo'] <= obs['time'] <= request['hi']): return 'UNKNOWN'
    if obs.get('role') not in ('CURRENT','HISTORICAL'): return 'UNKNOWN'
    return obs['label']

def main():
    req={'surface':'s1','session':'x1','lo':10,'hi':20}
    cases=[
      ({'status':'AVAILABLE','surface':'s1','session':'x1','time':15,'role':'CURRENT','label':'resolved'},'resolved'),
      ({'status':'AVAILABLE','surface':'s1','session':'x1','time':9,'role':'HISTORICAL','label':'old'},'UNKNOWN'),
      ({'status':'AVAILABLE','surface':'s2','session':'x1','time':15,'role':'HISTORICAL','label':'leak'},'UNKNOWN'),
      ({'status':'AVAILABLE','surface':'s1','session':'x2','time':15,'role':'HISTORICAL','label':'other'},'UNKNOWN'),
      ({'status':'DROPPED','surface':'s1','session':'x1','time':15,'role':'HISTORICAL','label':'missing'},'UNKNOWN'),
      ({'status':'AVAILABLE','surface':'s1','session':'x1','time':15,'role':'MISLABELED','label':'bad'},'UNKNOWN'),
    ]
    assert all(admissible(obs,req)==expected for obs,expected in cases)
    result={'cases':len(cases),'unknown_cases':sum(admissible(o,req)=='UNKNOWN' for o,_ in cases),'status':'PASS_TEMPORAL_RING_PROVENANCE_CONSTRUCTION_SCOPED','live_x11':False,'model_utility':None}
    open('result.json','w').write(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))
if __name__=='__main__': main()
