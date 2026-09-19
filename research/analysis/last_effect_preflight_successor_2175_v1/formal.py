import json

def use(receipt,current):
    if receipt.get('status')!='VALID': return 'UNKNOWN'
    if receipt.get('allocation')!=current['allocation']: return 'UNKNOWN'
    if receipt.get('epoch')!=current['epoch']: return 'UNKNOWN'
    if receipt.get('effect') in ('STALE','CONTRADICTORY','MISSING'): return 'UNKNOWN'
    return receipt['effect']

def main():
    cur={'allocation':'heldout-A','epoch':4}
    rows=[({'status':'VALID','allocation':'heldout-A','epoch':4,'effect':'SELF_EFFECT'},'SELF_EFFECT'),({'status':'VALID','allocation':'heldout-A','epoch':3,'effect':'SELF_EFFECT'},'UNKNOWN'),({'status':'VALID','allocation':'v31','epoch':4,'effect':'SELF_EFFECT'},'UNKNOWN'),({'status':'VALID','allocation':'heldout-A','epoch':4,'effect':'STALE'},'UNKNOWN'),({'status':'VALID','allocation':'heldout-A','epoch':4,'effect':'CONTRADICTORY'},'UNKNOWN'),({'status':'MALFORMED'},'UNKNOWN')]
    assert all(use(r,cur)==expected for r,expected in rows)
    result={'cases':len(rows),'known':1,'unknown':5,'status':'STOP_HELD_OUT_MODEL_EVALUATION_NOT_EXECUTED','preflight':'PASS_LAST_EFFECT_PROVENANCE_BOUNDARY','stop_reason':'No model/provider or independent current-state scorer is connected; deterministic receipt policy is insufficient for #2175 acceptance.','automatic_input':False}
    open('result.json','w').write(json.dumps(result,sort_keys=True,indent=2)+'\n'); print(json.dumps(result,sort_keys=True))
if __name__=='__main__': main()
