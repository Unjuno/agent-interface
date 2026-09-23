import json

def usable(sidecar, current):
    if sidecar.get('role') != 'OBSERVED': return 'UNKNOWN'
    if sidecar.get('identity') != current['identity']: return 'UNKNOWN'
    if sidecar.get('generation') != current['generation']: return 'UNKNOWN'
    if sidecar.get('epoch') != current['epoch']: return 'UNKNOWN'
    if sidecar.get('occluded'): return 'UNKNOWN'
    if 'box' not in sidecar: return 'UNKNOWN'
    return sidecar['box']

def main():
    cur={'identity':'target-A','generation':3,'epoch':9}
    good={'role':'OBSERVED','identity':'target-A','generation':3,'epoch':9,'box':[1,2,3,4]}
    cases=[
      (good,[1,2,3,4]),
      ({**good,'role':'INFERRED'},'UNKNOWN'),
      ({**good,'generation':2},'UNKNOWN'),
      ({**good,'identity':'target-B'},'UNKNOWN'),
      ({**good,'epoch':8},'UNKNOWN'),
      ({**good,'occluded':True},'UNKNOWN'),
      ({'role':'OBSERVED','identity':'target-A','generation':3,'epoch':9},'UNKNOWN'),
    ]
    assert all(usable(s,cur)==expected for s,expected in cases)
    result={'cases':len(cases),'unknown_cases':6,'status':'PASS_GEOMETRIC_SIDECAR_PROVENANCE_CONSTRUCTION_SCOPED','model_compaction_utility':None,'automatic_input':False}
    open('result.json','w').write(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))
if __name__=='__main__': main()
