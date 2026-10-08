"""Compare original local MCP observation with its context-enriched successor."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
base=root/'before.json'
next_path=root/'after.json'
old=json.loads(base.read_bytes());new=json.loads(next_path.read_bytes())
assert not old['isError'] and not new['isError']
before=json.loads(old['content'][0]['text']);after=json.loads(new['content'][0]['text'])
context=after.pop('session_context')
assert before==after and old['content'][1]==new['content'][1]
for key in ['goal','exchange_contract']:
    row=context[key];data=(root/('goal.json' if key=='goal' else 'exchange-contract.json')).read_bytes()
    assert hashlib.sha256(data).hexdigest()==row['source']['sha256']
    assert json.loads(data)==row['value']
assert set(context)=={'authority','goal','exchange_contract'}
assert context['authority']=='none'
print(json.dumps({'status':'PASS_SCOPED','prior_metadata_and_image_unchanged':True,
 'goal_sha256':context['goal']['source']['sha256'],
 'contract_sha256':context['exchange_contract']['source']['sha256'],
 'new_gui_execution':False,'model_utility_tokens_latency':'unmeasured'},indent=2))
