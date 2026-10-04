import hashlib, json
from pathlib import Path
root = Path(__file__).resolve().parent
main = json.loads((root/'RUN-MAIN.json').read_text())
candidate = json.loads((root/'RUN-PR7330.json').read_text())
expected = {
 'main_caller':'8517d130d7336b27e6ddfc0ee06629d2b1183070cf845c3ef4ada8adc3cd79ca',
 'candidate_caller':'983d22edfd1232a42765804688e990249887723f849220fae6407f58a04dca8c',
 'compiled':'d22160919ad7fc00d8a1c6e1da3240a316b024738362d714fafa68b772005014',
}
assert main['source_sha256']=={'caller':expected['main_caller'],'compiled':expected['compiled']}
assert candidate['source_sha256']=={'caller':expected['candidate_caller'],'compiled':expected['compiled']}
for label, data in [('main',main),('candidate',candidate)]:
    p=data['cases']['warm_positive']['result']; pc=data['cases']['warm_positive']['compiled'][0]
    assert (p['outcome'],p['task_effect'],p['delivery']) == ('TASK_SUCCEEDED','succeeded','confirmed')
    assert pc['outcome']=='TASK_SUCCEEDED' and pc['completed_transitions']==2
    assert p['accounting']['attempted_calls']==0 and p['attempt_ledger']==[]
    c=data['cases']['warm_changed']['result']; cc=data['cases']['warm_changed']['compiled'][0]
    assert (c['outcome'],c['reason'],c['delivery']) == ('EXECUTION_INCOMPLETE','unknown_state','confirmed_partial')
    assert c['execution_progress']=={'status':'safe_yield','reason':'unknown_state','completed_actions':1}
    assert cc['outcome']=='SAFE_YIELD' and cc['completed_transitions']==1
    assert [t['action'] for t in cc['transitions']]==['enter']
    e=data['cases']['outer_effect_unavailable']['result']; ec=data['cases']['outer_effect_unavailable']['compiled'][0]
    assert (e['outcome'],e['task_effect'],e['delivery']) == ('TASK_NOT_VERIFIED','unavailable','confirmed')
    assert ec['outcome']=='TASK_SUCCEEDED' and ec['completed_transitions']==2
main_progress=main['cases']['outer_effect_unavailable']['result']['execution_progress']
candidate_progress=candidate['cases']['outer_effect_unavailable']['result']['execution_progress']
assert main_progress is None
assert candidate_progress=={'status':'completed'}

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
report={
 'status':'PASS_SCOPED_TEST_DOUBLE_COMPOSITION',
 'scope':'warm caller v3 + compiled GUI runtime; synthetic adapter data; no model/GUI/input; no cold accounting or live efficiency claim',
 'assertions':{
  'warm_positive_two_transitions_and_outer_effect_success':True,
  'changed_unknown_stops_after_one_transition_with_typed_progress':True,
  'outer_unavailable_keeps_confirmed_delivery_but_main_drops_execution_progress':True,
  'PR7330_candidate_preserves_completed_execution_progress':True,
  'warm_routes_make_zero_model_attempts':True},
 'observed':{'main_effect_unavailable_execution_progress':main_progress,
             'candidate_effect_unavailable_execution_progress':candidate_progress,
             'main_source_sha256':main['source_sha256'],
             'candidate_source_sha256':candidate['source_sha256']},
 'sha256':{p.name:sha(p) for p in (root/'run.py',root/'RUN-MAIN.json',root/'RUN-PR7330.json')},
}
(root/'AUDIT.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
print(json.dumps(report,sort_keys=True,indent=2))
