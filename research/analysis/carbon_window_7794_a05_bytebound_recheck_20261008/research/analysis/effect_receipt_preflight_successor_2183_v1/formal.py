import json

def decision(receipt, actuation):
    if receipt.get('status')!='VALID': return 'QUERY_EFFECT'
    if receipt.get('protocol')!=actuation['protocol']: return 'QUERY_EFFECT'
    if receipt.get('sequence')<=actuation['sequence']: return 'QUERY_EFFECT'
    if receipt.get('authenticity')!='INDEPENDENT': return 'QUERY_EFFECT'
    if receipt.get('effect')=='NO_EFFECT': return 'ABORT'
    if receipt.get('effect')=='SELF_EFFECT': return 'DONE'
    return 'QUERY_EFFECT'

def main():
    a={'protocol':'p1','sequence':10}
    rows=[
      ({'status':'VALID','protocol':'p1','sequence':11,'authenticity':'INDEPENDENT','effect':'SELF_EFFECT'},'DONE'),
      ({'status':'VALID','protocol':'p1','sequence':11,'authenticity':'INDEPENDENT','effect':'EXTERNAL_EFFECT'},'QUERY_EFFECT'),
      ({'status':'VALID','protocol':'p1','sequence':11,'authenticity':'UNKNOWN','effect':'SELF_EFFECT'},'QUERY_EFFECT'),
      ({'status':'VALID','protocol':'p2','sequence':11,'authenticity':'INDEPENDENT','effect':'SELF_EFFECT'},'QUERY_EFFECT'),
      ({'status':'VALID','protocol':'p1','sequence':9,'authenticity':'INDEPENDENT','effect':'SELF_EFFECT'},'QUERY_EFFECT'),
      ({'status':'VALID','protocol':'p1','sequence':11,'authenticity':'INDEPENDENT','effect':'NO_EFFECT'},'ABORT'),
      ({'status':'MALFORMED'},'QUERY_EFFECT'),
    ]
    assert all(decision(r,a)==expected for r,expected in rows)
    result={'cases':len(rows),'safe_done':1,'query_or_abort':6,'status':'STOP_LIVE_MODEL_TRANSFER_NOT_EXECUTED','preflight':'PASS_EFFECT_RECEIPT_AUTHORITY_BOUNDARY','stop_reason':'No live model/provider or independent GUI application scorer was invoked; synthetic policy preflight is insufficient for #2183 acceptance.','automatic_input':False}
    open('result.json','w').write(json.dumps(result,sort_keys=True,indent=2)+'\n'); print(json.dumps(result,sort_keys=True))
if __name__=='__main__': main()
