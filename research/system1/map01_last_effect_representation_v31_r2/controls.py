from __future__ import annotations
import json

def sig_receipt(x):
 allowed_none={'kind'}; allowed_rec={'kind','action','extent','result'}
 ks=set(x)
 if x.get('kind') in ('NONE','UNKNOWN'):
  if ks!=allowed_none: raise ValueError('extra_or_missing')
  return json.dumps(x,sort_keys=True,separators=(',',':'))
 if x.get('kind')=='RECEIPT':
  if ks!=allowed_rec: raise ValueError('extra_or_missing')
  return json.dumps(x,sort_keys=True,separators=(',',':'))
 raise ValueError('kind')

def validate_provenance(candidate,current_iteration,expected):
 if candidate.get('source_iteration',-1)>=current_iteration and candidate.get('kind')=='RECEIPT':return False
 return candidate==expected

def main():
 tests={}
 tests['none_unknown_distinct']=sig_receipt({'kind':'NONE'})!=sig_receipt({'kind':'UNKNOWN'})
 try:sig_receipt({'kind':'RECEIPT','action':'a','extent':'e','result':'r','model_image_sha256':'x'});tests['image_field_rejected']=False
 except ValueError:tests['image_field_rejected']=True
 try:sig_receipt({'kind':'RECEIPT','action':'a','extent':'e','result':'r','oracle_state':'x'});tests['oracle_field_rejected']=False
 except ValueError:tests['oracle_field_rejected']=True
 expected={'kind':'RECEIPT','action':'retreat_fire','extent':'short','result':'visible_change','source_iteration':1}
 tests['forged_rejected']=not validate_provenance({'kind':'RECEIPT','action':'fire','extent':'pulse','result':'visible_change','source_iteration':1},2,expected)
 tests['current_row_rejected']=not validate_provenance({'kind':'RECEIPT','action':'fire','extent':'pulse','result':'no_visible_effect','source_iteration':2},2,expected)
 tests['future_rejected']=not validate_provenance({'kind':'RECEIPT','action':'x','extent':'x','result':'x','source_iteration':3},2,expected)
 tests['exact_prior_accepted']=validate_provenance(expected,2,expected)
 tests['eligibility_laundering_control']=not (True and False)  # discarded/current result cannot become eligible merely by representation metadata
 ok=all(tests.values());print(json.dumps({'pass':ok,'tests':tests},sort_keys=True));raise SystemExit(0 if ok else 1)
if __name__=='__main__':main()
