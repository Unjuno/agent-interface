"""Raw trace must prove all 24 registered stages in causal order."""
import copy
import hashlib
import json
import tempfile
import subprocess
import sys
from pathlib import Path
import unittest
from PIL import Image
from map01_east_return_audit import validate_trace, validate_raw_delivery, sealed_image_bytes, validate_owner_events, expected_program, validate_contract_replay, validate_close_receipt, validate_retirement, validate_visual_evidence, audit_trial, validate_caller_policy, validate_submit_deadline, validate_completion_score, validate_custody, validate_private_samples, validate_trial_deadline, validate_clock_gate, validate_environment, validate_independent_final
from map01_reverse_program import reverse_stages


def trace(arm='east-return'):
 prefix=[('cover-0',[{'op':'coast','duration_ms':200,'sample_ms':100}])]
 prefix += [('approach-'+str(i),[{'op':'hold','keys':['Up'],'duration_ms':600}]) for i in range(1,5)]
 prefix += [('intervention',[{'op':'hold','keys':['e'],'duration_ms':120}]),('traverse-1',[{'op':'hold','keys':['Up'],'duration_ms':300}])]
 expected=prefix+reverse_stages(arm);events=[{'event':'ready'},{'event':'typed_observation','id':'initial'},{'event':'observation','id':'initial'}];samples=[]
 for i,(identifier,steps) in enumerate(expected):
  t=1000+i*100
  events += [{'event':'command','received_ns':t,'command':{'op':'submit','id':identifier,'steps':steps}},
             {'event':'accepted','id':identifier,'accepted_ns':t+10}]
  if steps[0]['op']=='hold':
   events += [{'event':'input_admission','id':identifier}, {'event':'input_release_transition','id':identifier}]
  events += [{'event':'terminal','id':identifier,'status':'completed','terminal_ns':t+30},
             {'event':'command','received_ns':t+40,'command':{'op':'door-settle'}},
             {'event':'door_settle','operation_id':identifier,'status':'DONE','emit_ns':t+60}]
  samples.append({'stage':identifier,'status':'observed','terminal_ns':t+30,'started_ns':t+45,'finished_ns':t+55,'refresh_count':1,'physical_neutral_before_after':True})
 events.append({'event':'command','received_ns':4000,'command':{'op':'finish'}})
 return events,samples

class EastReturnTraceTests(unittest.TestCase):
 def test_reopen_trace_requires_exact_reopen_and_wait(self):
  events,samples=trace('east-return-reopen')
  validate_trace(events,samples,arm='east-return-reopen')
  changed=copy.deepcopy(events)
  command=next(row['command'] for row in changed if row.get('event')=='command' and row.get('command',{}).get('id')=='east-reopen')
  command['steps'][0]['keys']=['Up']
  with self.assertRaises(ValueError):validate_trace(changed,samples,arm='east-return-reopen')
  with self.assertRaises(ValueError):validate_trace(events,samples,arm='east-return-turn75')

 def test_independent_final_agrees_and_follows_post_score(self):
  score={'map_exit':False,'episode_finished':False,'player_dead':False,'death_count':0,'kill_count':0}
  payload=dict(score,schema='independent-progress-sample-v2',sample_ns=110)
  samples=[{'direct_final_sample':True,'controller_visible':False,'payload':payload,'sample_started_ns':111,'sample_finished_ns':111}]
  summary={'controller_visible':False,'schema':'map01-independent-scorer-integration-v3','sample_count':1}
  events=[{'event':'post_control_score','emit_ns':100}]
  self.assertIsNone(validate_independent_final(events,score,samples,summary))
  for kind in ('missing','state','time','count','duplicate','visible'):
   a=copy.deepcopy(samples); b=copy.deepcopy(summary)
   if kind=='missing':a=[]
   if kind=='state':a[-1]['payload']['player_dead']=True
   if kind=='time':a[-1]['payload']['sample_ns']=99
   if kind=='count':b['sample_count']=2
   if kind=='duplicate':a.append(copy.deepcopy(a[-1]));b['sample_count']=2
   if kind=='visible':a[-1]['controller_visible']=True
   with self.subTest(kind=kind),self.assertRaises(ValueError):validate_independent_final(events,score,a,b)
 def test_environment_must_match_registered_mode_and_ready_fixture(self):
  manifest='16f2bcf78b1d7739afd1fa0c141f1bbaee9dd2c9e3ff8e356ef3df743899d8d5';save='4e5b990cba8a86ca8a526ecdc59798c1869ea23c8f53468369e811f41d057ddc';evidence='40ef78b09f62fcd1b66cc6dc08257aa7d9d3f75fa0fe0797160c3d8fd48b58dc'
  candidate='/home/user/issue59-grandchild-bound-setup-yzkdlh9q/candidate/'
  fixture={'manifest':candidate+'fixture.json','manifest_sha256':manifest,'save':candidate+'fixture.png','save_sha256':save,'before_load_tic':89,'after_load_tic':870,'observed_restore_tic':870,'candidate_load_check':{'before_load_tic':89,'init_started_ns':1_000_000_000,'load_started_ns':1_500_000_000,'load_returned_ns':2_000_000_000,'getter_finished_ns':3_000_000_000,'observed_restore_tic':870,'natural_progress_upper_tic':180,'assumed_max_tics_per_second':45},'setup_candidate_evidence':{'evidence_sha256':evidence,'candidate_manifest_sha256':manifest,'candidate_save_sha256':save,'source_post_save_tic':870,'expected_restore_tic':870}}
  environment={'vizdoom':'1.3.0','mode':'Mode.ASYNC_SPECTATOR','ticrate':35,'seed':990619,'map':'MAP01','skill':1,'scenario_path':None,'scenario_sha256':None,'iwad':'/home/user/.cache/agent-interface-map01-20261103/lib/python3.12/site-packages/vizdoom/freedoom2.wad','iwad_sha256':'a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b','loaded_fixture':fixture,'sound_for_controller':False,'episode_timeout_seconds':75,'dbus_session_bus_address':'disabled:'}
  ready={'fixture':copy.deepcopy(fixture)};reg={'candidate_manifest_sha256':manifest,'candidate_save_sha256':save,'candidate_evidence_sha256':evidence,'candidate_restore_tic':870}
  self.assertIsNone(validate_environment(environment,ready,reg))
  for change in ({'seed':1},{'mode':'other'},{'iwad_sha256':'0'*64},{'scenario_path':'other'},{'skill':True},{'dbus_session_bus_address':'other'}):
   with self.subTest(change=change),self.assertRaises(ValueError):validate_environment(dict(environment,**change),ready,reg)
  wrong=copy.deepcopy(ready);wrong['fixture']['after_load_tic']=871
  with self.assertRaises(ValueError):validate_environment(environment,wrong,reg)
  bad=copy.deepcopy(environment);bad['loaded_fixture'].pop('candidate_load_check');wrong={'fixture':copy.deepcopy(bad['loaded_fixture'])}
  with self.assertRaises(ValueError):validate_environment(bad,wrong,reg)
  bad=copy.deepcopy(environment);bad['loaded_fixture']['before_load_tic']=870;bad['loaded_fixture']['candidate_load_check']['before_load_tic']=870;bad['loaded_fixture']['candidate_load_check']['natural_progress_upper_tic']=870;wrong={'fixture':copy.deepcopy(bad['loaded_fixture'])}
  with self.assertRaises(ValueError):validate_environment(bad,wrong,reg)
 def test_clock_gate_binds_private_display_neutrality_and_first_input(self):
  fixture=json.loads(Path(__file__).with_name('fixtures').joinpath('map01_east_clock_evidence_fixture.json').read_text())
  rows=fixture['clock_rows'];ready=fixture['ready'];active=fixture['active'];startup=fixture['startup'];events=fixture['events'];samples=fixture['samples']
  admission=next(row for row in events if row.get('event')=='input_admission');target=admission['target_process_identity']
  identity={'owner':startup['startup']['owner_id'],'generation':0,'surface':target[1],'process_digest':target[2]}
  self.assertIsNone(validate_clock_gate(rows,ready,active,startup,events,samples,identity=identity))
  for change in ({'display':':999'},{'pid':1},{'physical_keys_down':['Up']},{'pointer_mask':1},{'xtest_available':False},{'ready_emit_ns':1}):
   with self.subTest(change=change),self.assertRaises(ValueError):validate_clock_gate(rows,ready,dict(active,**change),startup,events,samples,identity=identity)
  with self.assertRaises(ValueError):validate_clock_gate(rows[:-1],ready,active,startup,events,samples,identity=identity)
  wrong_ready=copy.deepcopy(ready);wrong_ready['fixture']['candidate_load_check']['getter_finished_ns']=rows[0]['observed_ns']+1
  with self.assertRaises(ValueError):validate_clock_gate(rows,wrong_ready,active,startup,events,samples,identity=identity)
  shorter=copy.deepcopy(rows);first=shorter[-1];started=first['owner_state']['sample_started_ns'];first['observed_engine_tic']=990
  first['first_input_clock_deadline_ns']=min(shorter[5]['first_input_clock_deadline_ns'],started+(2100-990)*1_000_000_000//45)
  first['admission_deadline_ns']=min(started+1_000_000_000,first['first_input_clock_deadline_ns'])
  self.assertLess(first['first_input_clock_deadline_ns'],shorter[5]['first_input_clock_deadline_ns'])
  with self.assertRaises(ValueError):validate_clock_gate(shorter,ready,active,startup,events,samples,identity=identity)
  shorter_samples=copy.deepcopy(samples);after=next(x for x in shorter_samples if x['stage']=='approach-1')
  after.update(tic_before=990,state_tic=1010,getter_before_state=1010,getter_after_state=1010)
  self.assertIsNone(validate_clock_gate(shorter,ready,active,startup,events,shorter_samples,identity=identity))
  bad=copy.deepcopy(rows);bad[2]['after']['tic']=bad[2]['before']['tic']
  with self.assertRaises(ValueError):validate_clock_gate(bad,ready,active,startup,events,samples,identity=identity)
  wrong_identity=dict(identity,process_digest='other')
  with self.assertRaises(ValueError):validate_clock_gate(rows,ready,active,startup,events,samples,identity=wrong_identity)
  bad=copy.deepcopy(rows);bad[-2]['observed_ns']=next(x['terminal_ns'] for x in events if x.get('event')=='terminal' and x.get('id')=='cover-0')+1
  with self.assertRaises(ValueError):validate_clock_gate(bad,ready,active,startup,events,samples,identity=identity)
  bad=copy.deepcopy(rows);bad[-1]['observed_engine_tic']=bad[5]['last_refresh_tic']
  with self.assertRaises(ValueError):validate_clock_gate(bad,ready,active,startup,events,samples,identity=identity)
  bad=copy.deepcopy(rows);bad[-2]['observed_engine_tic']=870
  with self.assertRaises(ValueError):validate_clock_gate(bad,ready,active,startup,events,samples,identity=identity)
  bad=copy.deepcopy(rows);bad[-1]['observed_engine_tic']=870
  with self.assertRaises(ValueError):validate_clock_gate(bad,ready,active,startup,events,samples,identity=identity)
  bad=copy.deepcopy(rows);cover=bad[-2];cover['observed_engine_tic']=963
  cover_command=next(row for row in events if row.get('event')=='command' and row.get('command',{}).get('id')=='cover-0')
  cover['first_input_clock_deadline_ns']=cover_command['received_ns']-1_000_000+(2100-963)*1_000_000_000//45
  cover['admission_deadline_ns']=min(bad[5]['validated_ns']+2_000_000_000,cover['first_input_clock_deadline_ns'])
  with self.assertRaises(ValueError):validate_clock_gate(bad,ready,active,startup,events,samples,identity=identity)
  bad=copy.deepcopy(rows);bad[-1]['observed_engine_tic']=2624
  with self.assertRaises(ValueError):validate_clock_gate(bad,ready,active,startup,events,samples,identity=identity)
  bad=copy.deepcopy(rows);bad[-2]['admission_deadline_ns']=0
  with self.assertRaises(ValueError):validate_clock_gate(bad,ready,active,startup,events,samples,identity=identity)
  bad=copy.deepcopy(rows);bad[-1]['admission_deadline_ns']=bad[5]['first_input_clock_deadline_ns']+1_000_000_000
  with self.assertRaises(ValueError):validate_clock_gate(bad,ready,active,startup,events,samples,identity=identity)
  bad=copy.deepcopy(rows);bad[-1]['owner_state']['focus']=1
  with self.assertRaises(ValueError):validate_clock_gate(bad,ready,active,startup,events,samples,identity=identity)
 def test_trial_deadline_covers_every_caller_send(self):
  worker={'start_ns':100,'finish_ns':50_000_000_100}
  self.assertIsNone(validate_trial_deadline(worker,[{'phase':'sent','recorded_ns':48_000_000_099}]))
  with self.assertRaises(ValueError):validate_trial_deadline(worker,[{'phase':'sent','recorded_ns':48_000_000_100}])
  with self.assertRaises(ValueError):validate_trial_deadline({'start_ns':100,'finish_ns':100},[{'phase':'sent','recorded_ns':101}])
 def test_score_requires_the_matching_post_finish_event(self):
  score={'event':'post_control_score','map':'MAP01','skill':1,'map_exit':False,'episode_finished':False,'episode_timeout_reached':False,'player_dead':False,'death_count':0,'kill_count':0,'one_life_map_exit':False,'episode_timeout_seconds':75,'scorer_refresh_calls_after_control':0,'wall_control_ns':1}
  events=[{'event':'command','command':{'op':'finish'}},dict(score,emit_ns=3)]
  self.assertIsNone(validate_completion_score(events,score))
  with self.assertRaises(ValueError):validate_completion_score(events[:1],score)
  bad=copy.deepcopy(score);bad['map_exit']=True
  with self.assertRaises(ValueError):validate_completion_score(events,bad)
 def test_private_sample_proves_its_refresh_and_state_order(self):
  sample={'stage':'cover-0','status':'observed','terminal_ns':100,'started_ns':110,'finished_ns':130,'terminal_to_sample_ns':10,'terminal_to_refresh_ns':15,'terminal_to_state_ns':30,'tic_before':5,'getter_before_state':6,'state_tic':6,'getter_after_state':6,'state_number':7,'refresh_count':1,'physical_neutral_before_after':True,'position_x':1,'position_y':2,'angle':3,'health':100,'death_count':0,'kill_count':0,'gap':0,'floor_d':64,'ceiling_d':-64,'sector_index':27,'last_action':[0.0]*9}
  self.assertIsNone(validate_private_samples([sample]))
  second=dict(sample,stage='second',terminal_ns=200,started_ns=210,finished_ns=230,tic_before=5,state_tic=7,getter_before_state=7,getter_after_state=7,state_number=8)
  with self.assertRaises(ValueError):validate_private_samples([sample,second])
  for change in ({'tic_before':6},{'terminal_to_refresh_ns':2_000_000_000},{'terminal_to_state_ns':29}):
   wrong=dict(sample,**change)
   with self.assertRaises(ValueError):validate_private_samples([wrong])
 def test_custody_binds_registration_unit_and_owned_processes(self):
  root=Path('/tmp/trial');unit='map01-east-example.service';group='/user.slice/user-1000.slice/user@1000.service/app.slice/'+unit
  options=['UMask=0077','PrivateTmp=yes','PrivateNetwork=yes','RuntimeMaxSec=60s','TimeoutStopSec=5s','KillMode=control-group'];sha='a'*64
  reg={'unit':unit,'unit_options':options,'python':'/venv/python'}
  claim={'unit':unit,'registration_sha256':sha,'claimed_ns':1,'before':{'stdout':'Id='+unit+'\nLoadState=not-found\n','observed_ns':0,'exit_code':0}}
  argv=['systemd-run','--user','--wait','--pipe','--collect','--unit='+unit]+[x for option in options for x in ('-p',option)]+['/venv/python','-B',str(root/'driver.py'),sha]
  launch={'argv':argv,'started_ns':2};outcome={'unit':unit,'control_group':group,'service_after':{'stdout':'Id='+unit+'\nLoadState=not-found\n','observed_ns':9,'exit_code':0}}
  props={'Id':unit,'ControlGroup':group,'MainPID':'1','InvocationID':'b'*32,'ActiveState':'active','PrivateNetwork':'yes','PrivateTmp':'yes','KillMode':'control-group','RuntimeMaxUSec':'1min','TimeoutStopUSec':'5s','UMask':'0077'}
  service={'uid':1000,'observed_ns':3,'properties':props,'initial_pids':[1]}
  names={'1':'python','2':'python','3':'python','4':'Xvfb','5':'openbox','6':'vizdoom'}
  lineage={pid:{'cgroup':'0::'+group,'ppid':2 if pid=='3' else 1} for pid in names}
  active={'observed_ns':4,'unit_cgroup':group,'absolute_owned_pid_names':names,'process_lineage':lineage}
  startup={'spawn_pid':3,'startup':{'pid':3,'parent_pid':2}}
  self.assertIsNone(validate_custody(root,reg,sha,claim,launch,outcome,service,active,startup))
  bad=copy.deepcopy(service);bad['properties']['PrivateNetwork']='no'
  with self.assertRaises(ValueError):validate_custody(root,reg,sha,claim,launch,outcome,bad,active,startup)
  bad=copy.deepcopy(claim);bad['before']['stdout']='Id=other.service\nLoadState=not-found\n'
  with self.assertRaises(ValueError):validate_custody(root,reg,sha,bad,launch,outcome,service,active,startup)
  bad=copy.deepcopy(startup);bad['spawn_pid']=9
  with self.assertRaises(ValueError):validate_custody(root,reg,sha,claim,launch,outcome,service,active,bad)
  bad=copy.deepcopy(active);bad['process_lineage']['2']['ppid']=99
  with self.assertRaises(ValueError):validate_custody(root,reg,sha,claim,launch,outcome,service,bad,startup)
 def test_submit_deadline_reconstructs_a_fresh_real_decision(self):
  self.assertIsNone(validate_submit_deadline(20_000_000_120,trigger_ns=100,send_ns=130,capture_ns=90))
  with self.assertRaises(ValueError):validate_submit_deadline(2_000_000_130,trigger_ns=100,send_ns=130,capture_ns=90)
  with self.assertRaises(ValueError):validate_submit_deadline(20_000_000_120,trigger_ns=121,send_ns=130,capture_ns=90)
  with self.assertRaises(ValueError):validate_submit_deadline(20_000_000_120,trigger_ns=100,send_ns=130,capture_ns=-2_000_000_000)
 def test_caller_policy_rejects_unknown_health_before_any_send(self):
  from map01_reverse_program import reverse_manifest
  from test_map01_door_driver_protocol import pair
  ready={'event':'ready','fixture':{'manifest_sha256':'d'*64,'save_sha256':'e'*64,'after_load_tic':870,'setup_candidate_evidence':{'evidence_sha256':'f'*64}},'post_load_clock_gate':{'passed':True},'reverse_door_program':reverse_manifest('east-return')}
  typed,_=pair('initial',1,100);typed['signals']['health'].update(status='unknown',value=None)
  events=[ready,typed];driver=[{'phase':'received','event':row['event'],'id':row.get('id'),'emit_ns':None,'recorded_ns':200} for row in events]
  with self.assertRaisesRegex(ValueError,'HUD'):validate_caller_policy(events,driver,manifest_sha='d'*64,save_sha='e'*64,evidence_sha='f'*64,restore_tic=870)
 def test_cli_missing_seal_is_hold_and_nonzero(self):
  with tempfile.TemporaryDirectory() as temp:
   script=Path(__file__).with_name('map01_east_return_audit.py')
   result=subprocess.run([sys.executable,'-B',str(script),temp,'0'*64,'1'*64],capture_output=True,text=True,timeout=10)
   self.assertNotEqual(result.returncode,0)
   output=json.loads(result.stdout);self.assertEqual(output['disposition'],'HOLD');self.assertFalse(output['evidence_verified'])
 def test_missing_seal_can_never_be_a_success(self):
  with tempfile.TemporaryDirectory() as temp:
   result=audit_trial(Path(temp),'0'*64,'1'*64)
   self.assertEqual(result['disposition'],'HOLD')
   self.assertFalse(result['evidence_verified'])
   self.assertNotEqual(result['reason'],'complete sealed audit not yet implemented')
 def test_visual_evidence_is_recomputed_from_sealed_bytes(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);runtime=root/'runtime';runtime.mkdir();image=runtime/'004.png';reference=root/'east-reference.png'
   Image.new('RGB',(1280,800),(20,40,60)).save(image);reference.write_bytes(image.read_bytes())
   def entry(path):return {'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
   seal={'files':{'runtime/004.png':entry(image),'east-reference.png':entry(reference)}}
   with Image.open(image) as im:rgb=hashlib.sha256(im.convert('RGB').tobytes()).hexdigest()
   source={'event':'observation','id':'reverse-cross','step':0,'sequence':4,'capture_ns':100,'image':str(image),'image_reused':False,'frame_rgb_sha256':rgb,'pointer_binding':{'surface':7,'focus':7,'geometry':[321,180,640,480]},'renewal_owner_id':'owner','input_owner_generation':3,'target_process_identity':{'sequence':4,'surface':7,'digest':'proc'},'target_renewal_window_identity':{'sequence':4,'surface':7,'digest':'window'},'input_focus_before':7,'input_focus_after':7,'exact':True,'focus_samples_match':True}
   typed=copy.deepcopy(source);typed['event']='typed_observation';typed.pop('image')
   typed['signals']={name:{'status':'observed','value':value,'sequence':4,'capture_ns':100,'binding':copy.deepcopy(source['pointer_binding']),'signal_id':name} for name,value in (('health',100),('ammo',50))}
   up={'event':'input_release_transition','id':'reverse-cross','owner_sample_after_finished_ns':90,'owner_thread_keyup_receipt':{'server_keyup_verified':True,'owner_keymap_sampled_ns':85}}
   terminal={'event':'terminal','id':'reverse-cross','terminal_ns':150,'status':'completed'}
   settle={'event':'door_settle','operation_id':'reverse-cross','status':'DONE','emit_ns':160}
   command={'event':'command','received_ns':200,'command':{'op':'submit','id':'east-turn-1','expected_sequence':4}}
   events=[up,typed,source,terminal,settle,command]
   def log_rows(rows=None):
    result=[]
    for row in (events if rows is None else rows):
     if row.get('event')=='command':result.append({'phase':'sent','command':copy.deepcopy(row['command']),'recorded_ns':190})
     result.append({'phase':'received','event':row.get('event'),'id':row.get('id'),'emit_ns':row.get('emit_ns'),'recorded_ns':165 if row is settle else 120})
    return result
   receipt={'passed':True,'sequence':4,'capture_ns':100,'frame_rgb_sha256':rgb,'owner_id':'owner','owner_generation':3,'surface':7,'roi':[480,300,800,500],'difference_sum':0,'component_count':192000,'limit_mean':15,'started_ns':170,'finished_ns':180}
   identity={'surface':7,'owner':'owner','generation':3,'process_digest':'proc','window_digest':'window','geometry':[321,180,640,480]}
   self.assertIsNone(validate_visual_evidence(root,seal,events,receipt,driver=log_rows(),stage='reverse-cross',next_stage='east-turn-1',reference_name='east-reference.png',reference_sha256=entry(reference)['sha256'],identity=identity))
   events.insert(events.index(settle),{'event':'door_settle','operation_id':'reverse-cross','status':'WAIT','emit_ns':155})
   self.assertIsNone(validate_visual_evidence(root,seal,events,receipt,driver=log_rows(),stage='reverse-cross',next_stage='east-turn-1',reference_name='east-reference.png',reference_sha256=entry(reference)['sha256'],identity=identity))
   events.insert(events.index(source),{'event':'typed_observation','id':'other','sequence':5})
   with self.assertRaises(ValueError):validate_visual_evidence(root,seal,events,receipt,driver=log_rows(),stage='reverse-cross',next_stage='east-turn-1',reference_name='east-reference.png',reference_sha256=entry(reference)['sha256'],identity=identity)
   events.pop(events.index(source)-1)
   bad_events=copy.deepcopy(events);bad_typed=next(row for row in bad_events if row.get('event')=='typed_observation');bad_typed['signals']['health'].update(status='unknown',value=None)
   with self.assertRaises(ValueError):validate_visual_evidence(root,seal,bad_events,receipt,driver=log_rows(bad_events),stage='reverse-cross',next_stage='east-turn-1',reference_name='east-reference.png',reference_sha256=entry(reference)['sha256'],identity=identity)
   other=runtime/'005.png';other.write_bytes(image.read_bytes());seal['files']['runtime/005.png']=entry(other)
   bad_events=copy.deepcopy(events);next(row for row in bad_events if row.get('event')=='observation')['image']=str(other)
   with self.assertRaises(ValueError):validate_visual_evidence(root,seal,bad_events,receipt,driver=log_rows(bad_events),stage='reverse-cross',next_stage='east-turn-1',reference_name='east-reference.png',reference_sha256=entry(reference)['sha256'],identity=identity)
   bad=copy.deepcopy(receipt);bad['finished_ns']=195
   with self.assertRaises(ValueError):validate_visual_evidence(root,seal,events,bad,driver=log_rows(),stage='reverse-cross',next_stage='east-turn-1',reference_name='east-reference.png',reference_sha256=entry(reference)['sha256'],identity=identity)
   events.insert(events.index(command),{'event':'observation','id':'other','sequence':5})
   with self.assertRaises(ValueError):validate_visual_evidence(root,seal,events,receipt,driver=log_rows(),stage='reverse-cross',next_stage='east-turn-1',reference_name='east-reference.png',reference_sha256=entry(reference)['sha256'],identity=identity)
   events.pop(events.index(command)-1)
   bad=copy.deepcopy(receipt);bad['difference_sum']=1
   with self.assertRaises(ValueError):validate_visual_evidence(root,seal,events,bad,driver=log_rows(),stage='reverse-cross',next_stage='east-turn-1',reference_name='east-reference.png',reference_sha256=entry(reference)['sha256'],identity=identity)
   bad_events=copy.deepcopy(events)
   for row in bad_events:
    if row.get('event') in ('typed_observation','observation'):row['input_owner_generation']=True
   bad_identity=dict(identity,generation=1);bad_receipt=dict(receipt,owner_generation=1)
   with self.assertRaises(ValueError):validate_visual_evidence(root,seal,bad_events,bad_receipt,driver=log_rows(bad_events),stage='reverse-cross',next_stage='east-turn-1',reference_name='east-reference.png',reference_sha256=entry(reference)['sha256'],identity=bad_identity)
   image.write_bytes(b'tampered')
   with self.assertRaises(ValueError):validate_visual_evidence(root,seal,events,receipt,driver=log_rows(),stage='reverse-cross',next_stage='east-turn-1',reference_name='east-reference.png',reference_sha256=entry(reference)['sha256'],identity=identity)
 def test_retirement_requires_observed_service_and_every_display_pid(self):
  service={'properties':{'MainPID':'1','ControlGroup':'/unit'},'initial_pids':[1]}
  active={'absolute_owned_pid_names':{'1':'python','2':'Xvfb','3':'openbox','4':'vizdoom'},'unit_cgroup':'/unit'}
  retired={'pidfds_signaled':{'2':True,'3':True,'4':True},'cgroup_pids_after_runtime':[1],'lock_absent':True,'xauthority_absent':True}
  launch={'exit_code':0,'timed_out':False,'retired':True,'service_retirement_observed':True,'service_after':{'stdout':'LoadState=not-found'}}
  self.assertIsNone(validate_retirement(service,active,retired,launch))
  bad=copy.deepcopy(retired);bad['pidfds_signaled'].pop('4')
  with self.assertRaises(ValueError):validate_retirement(service,active,bad,launch)
  bad=copy.deepcopy(launch);bad['service_retirement_observed']=False
  with self.assertRaises(ValueError):validate_retirement(service,active,retired,bad)
  bad=copy.deepcopy(launch);bad['exit_code']=False
  with self.assertRaises(ValueError):validate_retirement(service,active,retired,bad)
 def test_final_owner_close_must_match_both_service_receipts(self):
  close={'event':'owner_release','reason':'close','verified':True,'keys_down':[],'buttons_down':[],'keys_unknown':[],'key_state_errors':[]}
  startup={'spawn_pid':42,'startup':{'pid':42,'parent_pid':10,'owner_id':'owner','service_id':'svc','display':':1'}}
  identity={'pid':42,'parent_pid':10,'supervisor_pid':10,'owner_id':'owner','service_id':'svc','display':':1'}
  ordinary={'service_id':'svc','verified':True,'owner_thread_stopped':True,'release_records':[copy.deepcopy(close)]}
  core={'verified':True,'service_id':'svc','owner_thread_stopped':True,'release_records':[copy.deepcopy(close)]}
  finish={'verified':True,'owner_thread_stopped':True,'context_exit_success':True,'identity':copy.deepcopy(identity),'startup_sha256':'c'*64}
  recovery={'verified':True,'identity':copy.deepcopy(identity),'startup_sha256':'c'*64,'core':core}
  report={'service_id':'svc','spawn_pid':42,'exit_code':0,'verified':True,'receipt_verified':True,'receipt_error':None,'process_alive':False,'finish':finish,'recovery':recovery}
  service={'service_id':'svc','verified':True,'startup_sha256':'a'*64,'adapter':{'owner_id':'owner','service_id':'svc','errors':[],'obligation':None,'verified':True,'ordinary_close':ordinary,'service_report':report}}
  saved={'receipt_verified':True,'finish':copy.deepcopy(finish),'recovery':copy.deepcopy(recovery)}
  self.assertIsNone(validate_close_receipt([close],service,'a'*64,startup,'owner',saved,'c'*64))
  bad=copy.deepcopy(service);bad['adapter']['service_report']['recovery']['core']['release_records'][-1]['verified']=1
  with self.assertRaises(ValueError):validate_close_receipt([close],bad,'a'*64,startup,'owner',saved,'c'*64)
  bad=copy.deepcopy(service);bad['adapter']['service_report']['process_alive']=True
  with self.assertRaises(ValueError):validate_close_receipt([close],bad,'a'*64,startup,'owner',saved,'c'*64)
  bad=copy.deepcopy(service);bad['adapter']['obligation']={'kind':'attempted_input_unknown'}
  with self.assertRaises(ValueError):validate_close_receipt([close],bad,'a'*64,startup,'owner',saved,'c'*64)
  bad=copy.deepcopy(service);bad['adapter']['errors']=[{'stage':'service_wait'}]
  with self.assertRaises(ValueError):validate_close_receipt([close],bad,'a'*64,startup,'owner',saved,'c'*64)
  bad=copy.deepcopy(service);bad['adapter']['service_report']['receipt_error']='unverified'
  with self.assertRaises(ValueError):validate_close_receipt([close],bad,'a'*64,startup,'owner',saved,'c'*64)
  bad=copy.deepcopy(service);bad['adapter']['ordinary_close']['close_error']='incomplete'
  with self.assertRaises(ValueError):validate_close_receipt([close],bad,'a'*64,startup,'owner',saved,'c'*64)
  bad=copy.deepcopy(service);bad['adapter']['owner_id']='other'
  with self.assertRaises(ValueError):validate_close_receipt([close],bad,'a'*64,startup,'owner',saved,'c'*64)
  bad=copy.deepcopy(service);bad['adapter']['service_report']['finish']['verified']=False
  with self.assertRaises(ValueError):validate_close_receipt([close],bad,'a'*64,startup,'owner',saved,'c'*64)
  bad=copy.deepcopy(service);bad['adapter']['service_report']['spawn_pid']=43
  with self.assertRaises(ValueError):validate_close_receipt([close],bad,'a'*64,startup,'owner',saved,'c'*64)
  bad=copy.deepcopy(service);bad['adapter']['ordinary_close']['service_id']='other'
  with self.assertRaises(ValueError):validate_close_receipt([close],bad,'a'*64,startup,'owner',saved,'c'*64)
  bad=copy.deepcopy(service);bad['adapter']['service_report']['exit_code']=42
  with self.assertRaises(ValueError):validate_close_receipt([close],bad,'a'*64,startup,'owner',saved,'c'*64)
  bad=copy.deepcopy(service);bad['adapter']['service_report']['finish']['startup_sha256']='d'*64;bad['adapter']['service_report']['recovery']['startup_sha256']='d'*64
  with self.assertRaises(ValueError):validate_close_receipt([close],bad,'a'*64,startup,'owner',saved,'c'*64)
  with self.assertRaises(ValueError):validate_close_receipt([close],service,'b'*64,startup,'owner',saved,'c'*64)
 def test_contract_replay_rejects_trace_without_initial_release_evidence(self):
  events,_=trace()
  with self.assertRaisesRegex(ValueError,'cover source'):validate_contract_replay(events)
 def test_each_keyup_is_verified_and_bound_to_its_owner_record(self):
  events,_=trace();events=copy.deepcopy(events);owner=[]
  for stage,steps in expected_program():
   terminal=next(row for row in events if row.get('event')=='terminal' and row.get('id')==stage)
   terminal.update(input_owner_id='owner',input_owner_generation=2,release={'event':'owner_release','reason':'release','intent_token':None,'verified':True,'keys_down':[],'buttons_down':[],'keys_unknown':[],'key_state_errors':[]})
   if steps[0]['op']=='hold':
    key=steps[0]['keys'][0];down=next(row for row in events if row.get('event')=='input_admission' and row.get('id')==stage)
    up=next(row for row in events if row.get('event')=='input_release_transition' and row.get('id')==stage)
    down.update(key=key,owner_id='owner',intent_token='token-'+stage)
    receipt={'event':'owner_explicit_keyup','operation':'up','key':key,'owner_id':'owner','intent_token':'token-'+stage,'server_keyup_verified':True,'server_key_down_after_keyup':False}
    up.update(key=key,owner_id='owner',intent_token='token-'+stage,owner_transition_verified=True,owner_thread_keyup_receipt=receipt)
    terminal['release']['intent_token']='token-'+stage
    owner.append(copy.deepcopy(receipt))
   owner.append(copy.deepcopy(terminal['release']))
  owner.append({'event':'owner_release','reason':'close','verified':True,'keys_down':[],'buttons_down':[],'keys_unknown':[],'key_state_errors':[]})
  self.assertEqual(validate_owner_events(events,owner),16)
  bad=copy.deepcopy(owner);bad.pop()
  with self.assertRaisesRegex(ValueError,'owner keyup'):validate_owner_events(events,bad)
  bad=list(reversed(copy.deepcopy(owner)))
  with self.assertRaisesRegex(ValueError,'owner'):validate_owner_events(events,bad)
  bad=copy.deepcopy(owner);bad.insert(0,{'event':'owner_explicit_keyup','key':'other'})
  with self.assertRaisesRegex(ValueError,'owner'):validate_owner_events(events,bad)
  bad=copy.deepcopy(owner);next(row for row in bad if row.get('event')=='owner_explicit_keyup')['server_keyup_verified']=1
  with self.assertRaisesRegex(ValueError,'owner keyup'):validate_owner_events(events,bad)
  bad=copy.deepcopy(events);next(row for row in bad if row.get('event')=='terminal')['release']['verified']=False
  with self.assertRaisesRegex(ValueError,'terminal release'):validate_owner_events(bad,owner)
  bad=copy.deepcopy(events);next(row for row in bad if row.get('event')=='input_admission')['owner_id']='other'
  with self.assertRaisesRegex(ValueError,'owner'):validate_owner_events(bad,owner)
 def test_image_must_be_the_sealed_runtime_file_not_an_external_path(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'trial';runtime=root/'runtime';runtime.mkdir(parents=True)
   image=runtime/'123.png';image.write_bytes(b'frame')
   entry={'bytes':5,'sha256':hashlib.sha256(b'frame').hexdigest()};seal={'files':{'runtime/123.png':entry}}
   self.assertEqual(sealed_image_bytes(root,seal,str(image)),b'frame')
   outside=Path(tmp)/'outside.png';outside.write_bytes(b'frame')
   with self.assertRaises(ValueError):sealed_image_bytes(root,seal,str(outside))
   image.write_bytes(b'other')
   with self.assertRaises(ValueError):sealed_image_bytes(root,seal,str(image))
 def test_raw_delivery_requires_every_emitted_event_and_command(self):
  events,samples=trace()
  raw=copy.deepcopy(events);raw[0]['stdout_handoff_started_ns']=42
  driver=[]
  for row in events:
   if row.get('event')=='command':driver.append({'phase':'sent','command':copy.deepcopy(row['command'])})
   driver.append({'phase':'received','event':row.get('event'),'id':row.get('id'),'emit_ns':row.get('emit_ns')})
  self.assertIsNone(validate_raw_delivery(events,raw,driver))
  changed=copy.deepcopy(raw);next(row for row in changed if row.get('event')=='command')['received_ns']+=1
  with self.assertRaisesRegex(ValueError,'raw'):validate_raw_delivery(events,changed,driver)
  changed=copy.deepcopy(driver);changed.pop(next(i for i,row in enumerate(changed) if row['phase']=='sent'))
  with self.assertRaisesRegex(ValueError,'command'):validate_raw_delivery(events,raw,changed)
  changed=[row for row in driver if row['phase']!='received']
  with self.assertRaisesRegex(ValueError,'received'):validate_raw_delivery(events,raw,changed)
  changed=copy.deepcopy(driver)
  cover_send=next(i for i,row in enumerate(changed) if row.get('phase')=='sent' and row.get('command',{}).get('id')=='cover-0')
  moved=changed.pop(cover_send);changed.insert(0,moved)
  with self.assertRaisesRegex(ValueError,'initial'):validate_raw_delivery(events,raw,changed)
  changed=copy.deepcopy(driver)
  settle_send=next(i for i,row in enumerate(changed) if row.get('phase')=='sent' and row.get('command',{}).get('op')=='door-settle')
  moved=changed.pop(settle_send)
  cover_send=next(i for i,row in enumerate(changed) if row.get('phase')=='sent' and row.get('command',{}).get('id')=='cover-0')
  changed.insert(cover_send+1,moved)
  with self.assertRaisesRegex(ValueError,'settle'):validate_raw_delivery(events,raw,changed)
  changed=copy.deepcopy(driver)
  next_send=next(i for i,row in enumerate(changed) if row.get('phase')=='sent' and row.get('command',{}).get('id')=='approach-1')
  first_done=next(i for i,row in enumerate(changed) if row.get('phase')=='received' and row.get('event')=='door_settle')
  moved=changed.pop(next_send);changed.insert(first_done,moved)
  with self.assertRaisesRegex(ValueError,'before previous settlement'):validate_raw_delivery(events,raw,changed)
  changed=copy.deepcopy(driver)
  finish=next(i for i,row in enumerate(changed) if row.get('phase')=='sent' and row.get('command',{}).get('op')=='finish')
  last_done=max(i for i,row in enumerate(changed) if row.get('phase')=='received' and row.get('event')=='door_settle')
  moved=changed.pop(finish);changed.insert(last_done,moved)
  with self.assertRaisesRegex(ValueError,'before previous settlement'):validate_raw_delivery(events,raw,changed)
  typed_events=copy.deepcopy(events);typed_raw=copy.deepcopy(raw);typed_events[0]['verified']=True;typed_raw[0]['verified']=1
  with self.assertRaisesRegex(ValueError,'raw'):validate_raw_delivery(typed_events,typed_raw,driver)
  changed=copy.deepcopy(events);changed[1]['emit_ns']=100
  with self.assertRaisesRegex(ValueError,'raw'):validate_raw_delivery(changed,raw,driver)
 def test_bounded_wait_must_be_a_matched_ordered_exchange(self):
  events,samples=trace();idx=next(i for i,row in enumerate(events) if row.get('event')=='command' and row.get('command',{}).get('op')=='door-settle')
  events[idx:idx]=[{'event':'command','received_ns':1032,'command':{'op':'door-settle'}},
                   {'event':'door_settle','operation_id':'cover-0','status':'WAIT','emit_ns':1038}]
  self.assertEqual(validate_trace(events,samples),24)
  wrong=copy.deepcopy(events);wrong[idx+1],wrong[idx+2]=wrong[idx+2],wrong[idx+1]
  with self.assertRaisesRegex(ValueError,'settlement exchange'):validate_trace(wrong,samples)
  wrong=copy.deepcopy(events);wrong[idx+1]['emit_ns']=1041
  with self.assertRaisesRegex(ValueError,'settlement exchange'):validate_trace(wrong,samples)
 def test_full_trace_and_interleaving_are_checked(self):
  events,samples=trace();self.assertEqual(validate_trace(events,samples),24)
  mutations=[]
  first_east=next(i for i,row in enumerate(events) if row.get('event')=='command' and row.get('command',{}).get('id')=='east-turn-1')
  mutations.append((events[:first_east]+events[-1:],samples[:19]))
  first_done=next(i for i,row in enumerate(events) if row.get('event')=='door_settle')
  wrong=copy.deepcopy(events);wrong.insert(first_done,{'event':'command','received_ns':1045,'command':{'op':'load'}});mutations.append((wrong,samples))
  wrong=copy.deepcopy(events);wrong[first_done]['status']='WAIT';mutations.append((wrong,samples))
  second_submit=next(i for i,row in enumerate(events) if row.get('event')=='command' and row.get('command',{}).get('id')=='approach-1')
  wrong=copy.deepcopy(events);wrong[second_submit]['received_ns']=1045;mutations.append((wrong,samples))
  wrong=copy.deepcopy(events);wrong.insert(first_done,{'event':'accepted','id':'intruder','accepted_ns':1045});mutations.append((wrong,samples))
  wrong=copy.deepcopy(events);wrong.insert(first_done,{'event':'input_admission','id':'intruder'});mutations.append((wrong,samples))
  wrong=copy.deepcopy(events);down=next(i for i,row in enumerate(wrong) if row.get('event')=='input_admission');wrong[down],wrong[down+1]=wrong[down+1],wrong[down];mutations.append((wrong,samples))
  wrong=copy.deepcopy(events);wrong.insert(0,{'event':'command','received_ns':1,'command':{'op':'door-settle'}});mutations.append((wrong,samples))
  wrong=copy.deepcopy(events);wrong.insert(0,{'event':'door_settle','operation_id':'intruder','status':'DONE','emit_ns':1});mutations.append((wrong,samples))
  wrong=copy.deepcopy(events);wrong.insert(0,{'event':'input_release_unverified','id':'intruder'});mutations.append((wrong,samples))
  bad=copy.deepcopy(samples);bad[0]['started_ns']=1035;mutations.append((events,bad))
  bad=copy.deepcopy(samples);bad[0]['finished_ns']=1065;mutations.append((events,bad))
  bad=copy.deepcopy(samples);bad[0]['refresh_count']=True;mutations.append((events,bad))
  for es,ss in mutations:
   with self.subTest(events=len(es),samples=len(ss)),self.assertRaises(ValueError):validate_trace(es,ss)
if __name__=='__main__':unittest.main()
