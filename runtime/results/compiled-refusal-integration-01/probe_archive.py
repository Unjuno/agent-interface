from pathlib import Path
import sys,json,zipfile
archive=Path(sys.argv[1]).resolve();sys.path.insert(0,str(archive))
from runtime.core_v1 import compiled_gui
assert compiled_gui.__file__.startswith(str(archive))
spec={'format':'compiled-gui-interface-v1','interface_id':'packaged-refusal','session_scope':'private','surface':'form',
'predicates':['present'],'symbols':{'field':{'kind':'target_reference','target_reference':'field','identity_predicate':'present','dependencies':['present']}},
'actions':{'enter':{'target_symbol':'field','operation':'enter','expected_effect':{'present':False}}},
'method':{'name':'one-step','version':'1','initial_state':'ready','max_transitions':1,'max_runtime_ms':1000,
'states':{'ready':{'branches':[{'when':{'present':True},'outcome':'action','action':'enter','next_state':'done','reason':None}]},
'done':{'branches':[{'when':{'present':False},'outcome':'complete','action':None,'next_state':None,'reason':None}]}}}}
def observe(_):return {'sequence':1,'captured_ns':0,'surface':'form','predicates':{'present':True},'evidence_ref':'frame','evidence_digest':'digest'}
def admit(p):return {'eligible':True,'status':'revalidated','authorization':'one-use','expected_sequence':1,'valid_until_ns':1000000}
inputs=[]
def execute(p):
 inputs.append(p)
 return {'status':'refused','input_dispatched':False,'action_id':'refused','effect_ref':'receipt','release':{'verified':False,'keys_down':[],'buttons_down':[]}}
def no_effect(_):raise AssertionError('no effect verification after no-input refusal')
r=compiled_gui.run(spec,{'observe':observe,'admit':admit,'execute':execute,'verify_effect':no_effect,'cancelled':lambda:False,'journal':lambda _:None},clock=lambda:0)
if (r['outcome'],r['reason'],r['completed_transitions'])!=('SAFE_YIELD','execution_refused',0) or len(inputs)!=1:raise ValueError('packaged refusal path differs')
print(json.dumps({'status':'PASS_PACKAGED_REFUSAL','module':compiled_gui.__file__,'release_verified':False,'completed_transitions':0,'scope':'isolated portable import, deterministic adapter only; no native/model/task efficacy'},indent=2))