import copy,importlib.util,pathlib
p=pathlib.Path(__file__).with_name('run.py');s=importlib.util.spec_from_file_location('candidate',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
base_arm={'fallback_id':'fallback','planner_window':{'start_ns':0,'end_ns':1000}}
base_events=[{'event':'accepted','id':'fallback','intent_token':'t','valid_until_ns':600},{'event':'input_admission','intent_token':'t','key':'d','admitted_ns':100,'input_ack_ns':110},{'event':'input_release_transition','intent_token':'t','key':'d','operation':'up','owner_transition_verified':False,'release_call_started_ns':700,'release_call_returned_ns':710},{'event':'terminal','id':'fallback','release':{'verified':True,'keys_down':[],'buttons_down':[]}}]
base_owner=[{'event':'owner_release','reason':'expired','verified':True,'keys_down':[],'buttons_down':[],'verified_ns':620,'valid_until_ns':600}]
def ok(e=None,o=None,a=None):return m.recover_arm(a or copy.deepcopy(base_arm),e or copy.deepcopy(base_events),o or copy.deepcopy(base_owner))['valid']
assert ok()
controls=[]
for name,mut in [
 ('reason',lambda e,o,a:o[0].__setitem__('reason','cancelled')),
 ('verified',lambda e,o,a:o[0].__setitem__('verified',False)),
 ('nonneutral',lambda e,o,a:o[0].__setitem__('keys_down',[40])),
 ('deadline',lambda e,o,a:o[0].__setitem__('valid_until_ns',601)),
 ('order',lambda e,o,a:o[0].__setitem__('verified_ns',701)),
 ('terminal',lambda e,o,a:e[-1]['release'].__setitem__('verified',False)),
 ('multi_key',lambda e,o,a:e[1].__setitem__('key','a')),
 ('duplicate_expiry',lambda e,o,a:o.append(copy.deepcopy(o[0]))),
]:
 e=copy.deepcopy(base_events);o=copy.deepcopy(base_owner);a=copy.deepcopy(base_arm);mut(e,o,a);controls.append((name,not ok(e,o,a)))
assert all(v for _,v in controls),controls
print('PASS construction controls',controls)
