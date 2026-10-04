import json
from pathlib import Path
from planner_contract_schema import compile_contract
raw=json.loads(Path('/prior/formal-output/model-calls/call-011/answer.json').read_text())
compiled=compile_contract(raw['contract'],{'field':'field','submit':'submit'},'construction')
def positive(c):x0,y0,x1,y1=c;return 0<=x0<x1<=1280 and 0<=y0<y1<=800
assert not positive(raw['value_crop'])
assert positive([0,0,1,1])
Path('/out/REGRESSION.json').write_text(json.dumps({'scope':'saved-output preflight regression, no provider/GUI task','old_zero_crop_refused':True,'dummy_crop_valid':True,'saved_provider_contract_semantically_valid':True,'compiled':compiled},indent=2))
print('PASS retained contract valid; zero crop refused, explicit dummy valid')
