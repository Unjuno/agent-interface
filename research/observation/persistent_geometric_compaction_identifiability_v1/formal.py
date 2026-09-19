import json,sys
from audit import evaluate
ledger=json.load(open(sys.argv[1])); result=evaluate(ledger)
if result['errors']: raise SystemExit('ledger invalid: '+repr(result['errors']))
json.dump(result,open(sys.argv[2],'w'),indent=2,sort_keys=True); open(sys.argv[2],'a').write('\n'); print(json.dumps(result,sort_keys=True))
