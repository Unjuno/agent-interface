import hashlib, json

def digest(verifier, generation, claim, observer):
 return hashlib.sha256(f'{verifier}|{generation}|{claim}|{observer}'.encode()).hexdigest()

def main():
 rows=[]
 for equiv in (False,True):
  receipts=[]
  for observer in ('A','B'):
   claim='COMMIT' if (not equiv or observer=='A') else 'ABORT'
   receipts.append({'verifier':'v1','generation':7,'claim':claim,'observer':observer,'digest':digest('v1',7,claim,observer)})
  same_claim=len({r['claim'] for r in receipts})==1
  bound=len({(r['verifier'],r['generation'],r['digest']) for r in receipts})==len(receipts)
  fork_detected=(not same_claim) and all(r['generation']==7 for r in receipts)
  rows.append({'equivocation':equiv,'same_claim':same_claim,'binding_valid':bound,'fork_detected':fork_detected,'admit':same_claim and bound})
 print(json.dumps({'experiment':'5314-equivocation-t1','rows':rows,'scope':'hash-bound toy receipts; no signatures, key compromise, network ordering, or external effect'},sort_keys=True,indent=2))
if __name__=='__main__': main()
