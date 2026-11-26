"""Portable synthetic two-generation evidence and corruption regressions."""
import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from test_map01_candidate_setup_synthetic import fixture,write,seal,custody,FakeHud
from map01_candidate_setup_evidence_v1 import verify_setup_candidate,EvidenceError,digest_file


def derive(root, retry=False):
 base=root/'base';base.mkdir();parent,proof,wad,pc,pg,ph=fixture(base)
 with patch('doom_hud_signal_v3.DoomStatusNumberReader',FakeHud):
  parent_binding=verify_setup_candidate(parent,proof,digest_file(proof),'1.3.0',digest_file(wad),1,990619,75,wad)[2]
 child_root=root/'child';child_root.mkdir();manifest,child_proof,child_wad,creation,gui,headless=fixture(child_root)
 (creation/'evidence.json').write_bytes(proof.read_bytes())
 candidate=json.loads(manifest.read_text())
 source=candidate['source_observation'];source.update(sequence=5,capture_ns=3_000_000_500)
 source['target_process_identity']['sequence']=5;source['target_renewal_window_identity']['sequence']=5
 check={'before_load_tic':20,'init_started_ns':1,'load_started_ns':2,'load_returned_ns':3,
        'getter_finished_ns':4,'observed_restore_tic':528,'natural_progress_upper_tic':22,
        'assumed_max_tics_per_second':45}
 candidate.update(setup_mode='verified_loaded_fixture_setup_v1',episode_tic=None,
   post_save_refresh_episode_tic=717,restored_episode_tic=None,restored_episode_tic_status='unmeasured',
   parent_fixture={'manifest_sha256':parent_binding['candidate_manifest_sha256'],
    'save_sha256':parent_binding['candidate_save_sha256'],'source_episode_tic':None,
    'loaded_episode_tic':528,'observed_restore_tic':528,'setup_candidate_evidence':parent_binding,
    'candidate_load_check':check})
 manifest.write_text(json.dumps(candidate,sort_keys=True));manifest_sha=digest_file(manifest)
 def pair(seq,identifier,step):
  base={**source,'id':identifier,'step':step,'sequence':seq,'capture_ns':3_000_000_000+seq*100,
   'target_process_identity':{'sequence':seq,'surface':11,'digest':'a'*64},
   'target_renewal_window_identity':{'sequence':seq,'surface':11,'digest':'b'*64}}
  signals={name:{'status':'observed','value':value,'sequence':seq,'capture_ns':3_000_000_000+seq*100,
    'binding':base['pointer_binding'],'signal_id':name} for name,value in (('health',100),('ammo',50))}
  return ({**base,'event':'typed_observation','signals':signals},base)
 empty={'verified':True,'keys_down':[],'buttons_down':[],'keys_unknown':[],'key_state_errors':[]}
 steps=[{'op':'hold','keys':['Up'],'duration_ms':600},{'op':'coast','duration_ms':750,'sample_ms':250}]
 step_sha=hashlib.sha256(json.dumps(steps,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 down={'event':'input_admission','id':'setup-move','step':0,'key':'Up','keycode':111,'owner_id':'owner',
  'intent_token':'move','admitted_ns':3_000_000_245,'input_ack_ns':3_000_000_250,'first_press_deadline_ns':4_000_000_220,
  'first_press_submission_checked_before_deadline':True,'valid_until_ns':3_000_001_000,
  'target_process_identity':[2,11,'a'*64,3_000_001_000]}
 attempt={'attempt':1,'keyrelease_started_ns':3_000_000_350,'sync_returned_ns':3_000_000_360,'keymap_sampled_ns':3_000_000_370,
          'server_key_down_before':True,'server_key_down_after':False}
 up={'event':'owner_explicit_keyup','operation':'up','owner_id':'owner','key':'Up','keycode':111,
   'intent_token':'move','valid_until_ns':3_000_001_000,'owner_keyrelease_started_ns':3_000_000_350,'owner_sync_returned_ns':3_000_000_360,
   'owner_keymap_sampled_ns':3_000_000_370,'server_keyup_verified':True,'server_keyup_attempt_count':1,
   'server_keyup_attempts':[attempt],'server_key_down_after_keyup':False,'key_state_source':'x11_query_keymap',
   'server_sync_completed':True,'physical_verification_authoritative':False,'cancel_requested_after_sync':False,
   'release_batch_initial_up_count':1,'release_batch_key_order':['Up']}
 if retry:
  attempt['server_key_down_after']=True
  up.update(server_keyup_attempt_count=2,owner_sync_returned_ns=3_000_000_375,
            owner_keymap_sampled_ns=3_000_000_380)
  up['server_keyup_attempts'].append({'attempt':2,'keyrelease_started_ns':3_000_000_371,
    'sync_returned_ns':3_000_000_375,'keymap_sampled_ns':3_000_000_380,
    'server_key_down_before':True,'server_key_down_after':False})
 transition={'event':'input_release_transition','id':'setup-move','step':0,'operation':'up','key':'Up',
   'owner_id':'owner','intent_token':'move','owner_transition_verified':True,'owner_thread_keyup_receipt':up,
   'admission_receipt':dict(down,operation='down'),'admission_receipt_valid':True}
 parent_gate_path=pg/'gui-load-clock-gate.jsonl';parent_gate=[json.loads(x) for x in parent_gate_path.read_text().splitlines()]
 last=parent_gate[4]
 reserve=last['start_ns']+(2625-last['after']['tic']-525)*1_000_000_000//45
 parent_gate[-1].update(last_refresh_tic=last['after']['tic'],last_refresh_started_ns=last['start_ns'],
  remaining_game_seconds_required=15,projection_tics_per_second=45,first_input_clock_deadline_ns=reserve)
 ready_gate={k:v for k,v in parent_gate[-1].items() if k!='event'}
 parent_gate.extend([{'event':'submission_gate','id':name,'owner_id':'owner','owner_generation':0,
   'source_sequence':seq,'terminal_id':terminal,'observed_ns':stamp,'observed_engine_tic':last['after']['tic'],
   'admission_deadline_ns':(3_000_000_260 if name=='cover-0' else 4_000_000_220),'first_input_clock_deadline_ns':reserve,
   'owner_state':{'owner_id':'owner','sample_started_ns':stamp-2,'sample_finished_ns':stamp-1,
      'owned_buttons':[],'owned_keycodes':[],'physical_pointer_mask':0,'focus':11,
      'active_lease_deadline_ns':None,'active_lease_time_valid':False,'cancel_requested':False,'release_pending':False},
   'grants_input_authority':False}
   for name,seq,terminal,stamp in [('cover-0',1,None,3_000_000_120),('setup-move',2,'cover-0',3_000_000_230)]])
 release=lambda reason,token,stamp:{'event':'owner_release','reason':reason,'verified':True,
   'buttons_down':[],'keys_down':[],'keys_unknown':[],'key_state_errors':[],
   'verified_ns':stamp,'intent_token':token,'key_state_source':'x11_query_keymap'}
 write(creation,'runtime/owner-events.json',[release('release',None,3_000_000_205),up,
    release('release','move',3_000_000_440),release('close',None,3_000_000_600)])
 (creation/'runtime/post-load-clock-gate.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in parent_gate))
 ready={'event':'ready','fixture':{'setup_candidate_evidence':parent_binding,'candidate_load_check':check,
        'manifest_sha256':parent_binding['candidate_manifest_sha256'],'save_sha256':parent_binding['candidate_save_sha256'],
        'after_load_tic':528},'post_load_clock_gate':ready_gate}
 events=[ready,*pair(1,'initial',0),
  {'event':'command','command':{'op':'submit','id':'cover-0','expected_sequence':1,'steps':[{'op':'coast','duration_ms':200,'sample_ms':100}]}},
  {'event':'accepted','id':'cover-0','intent_token':'cover','accepted_ns':3_000_000_130},*pair(2,'cover-0',0),
  {'event':'terminal','id':'cover-0','status':'completed','steps_completed':1,'release':release('release',None,3_000_000_205),
   'input_owner_id':'owner','input_owner_generation':0,'terminal_ns':3_000_000_210},
  {'event':'command','command':{'op':'submit','id':'setup-move','expected_sequence':2,'steps':steps}},
  {'event':'accepted','id':'setup-move','program_sha256':step_sha,'intent_token':'move',
   'valid_until_ns':3_000_001_000,'accepted_ns':3_000_000_240},down,*pair(3,'setup-move',0),transition,*pair(4,'setup-move',1),
  {'event':'terminal','id':'setup-move','status':'completed','steps_completed':2,
   'release':release('release','move',3_000_000_440),'input_owner_id':'owner','input_owner_generation':0,'terminal_ns':3_000_000_450},
  {'event':'command','command':{'op':'save_fixture'}},*pair(5,'fixture-source',0),
  {'event':'fixture_saved','source_sequence':5,'save_sha256':candidate['save_sha256'],'episode_tic':None,
   'post_save_refresh_episode_tic':717,'restored_episode_tic':None,'restored_episode_tic_status':'unmeasured'}]
 (creation/'runtime/events.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in events))
 registration=json.loads((creation/'registration.json').read_text())
 registration.update(runtime_argv=['--load-fixture-manifest',str(parent)],candidate_evidence_sha256=digest_file(proof),
  parent_manifest_sha256=parent_binding['candidate_manifest_sha256'],parent_save_sha256=parent_binding['candidate_save_sha256'],
  loaded_tic=528,movement_steps=steps,movement_sha256=step_sha,maximum_key_admissions=1,repeat_limit=1,model_calls=0)
 custody(creation,registration,'1min',0)
 out=json.loads((creation/'worker-outcome.json').read_text());out.update(candidate_manifest_sha256=manifest_sha,keyed_commands=1)
 write(creation,'worker-outcome.json',out);creation_sha=seal(creation,True)
 h=json.loads((headless/'worker-outcome.json').read_text());h.update(disposition='PASS',comparison='PASS',expected_tic=715,actual_tic_before_any_refresh=715)
 write(headless,'worker-outcome.json',h);ret=json.loads((headless/'load-returned.json').read_text());ret['actual_tic_before_any_refresh']=715
 write(headless,'load-returned.json',ret)
 hreg=json.loads((headless/'registration.json').read_text());hreg.update(expected_tic=715,
  candidate_manifest_sha256=manifest_sha,candidate_seal_sha256=creation_sha,
  candidate_save_sha256=candidate['save_sha256'],repeat_limit=1,input_commands=0,model_calls=0)
 custody(headless,hreg,'30s',0);headless_sha=seal(headless,True)
 gate_path=gui/'gui-load-clock-gate.jsonl';gate=[json.loads(x) for x in gate_path.read_text().splitlines()]
 for state,index in ((gate[0]['state'],0),):state['tic']=[715,717,718,719,790][index]
 tics=[715,717,718,719,790]
 for i,row in enumerate(gate[1:5]):row['before']['tic']=tics[i];row['after']['tic']=tics[i+1]
 gate_path.write_text(''.join(json.dumps(x)+'\n' for x in gate))
 gout=json.loads((gui/'worker-outcome.json').read_text());gout.update(expected_tic=715,source_post_save_tic=717,actual_tic_before_any_refresh=715)
 write(gui,'worker-outcome.json',gout);ret=json.loads((gui/'load-returned.json').read_text());ret['actual_tic_before_any_refresh']=715
 write(gui,'load-returned.json',ret)
 greg=json.loads((gui/'registration.json').read_text());greg.update(candidate_seal_sha256=creation_sha,candidate_manifest_sha256=manifest_sha,
   expected_tic=715,source_post_save_tic=717,headless_seal_sha256=headless_sha,headless_outcome_sha256=digest_file(headless/'worker-outcome.json'))
 custody(gui,greg,'30s',0);gui_sha=seal(gui,True)
 spec=json.loads(child_proof.read_text());spec.update(creation_seal_sha256=creation_sha,gui_seal_sha256=gui_sha,expected_restore_tic=715)
 child_proof.write_text(json.dumps(spec))
 return manifest,child_proof,wad,creation,gui,headless


class DerivedCandidateTests(unittest.TestCase):
 def test_two_generation_chain_and_resealed_keyup_corruption(self):
  with tempfile.TemporaryDirectory() as temp:
   manifest,proof,wad,creation,gui,headless=derive(Path(temp))
   def verify():return verify_setup_candidate(manifest,proof,digest_file(proof),'1.3.0',digest_file(wad),1,990619,75,wad)
   with patch('doom_hud_signal_v3.DoomStatusNumberReader',FakeHud):
    self.assertEqual(verify()[2]['expected_restore_tic'],715)
    owner=json.loads((creation/'runtime/owner-events.json').read_text());owner[1]['server_keyup_verified']=False
    write(creation,'runtime/owner-events.json',owner);creation_sha=seal(creation,True)
    hreg=json.loads((headless/'registration.json').read_text());hreg['candidate_seal_sha256']=creation_sha
    custody(headless,hreg,'30s',0);headless_sha=seal(headless,True)
    greg=json.loads((gui/'registration.json').read_text())
    greg.update(candidate_seal_sha256=creation_sha,headless_seal_sha256=headless_sha)
    custody(gui,greg,'30s',0);gui_sha=seal(gui,True)
    spec=json.loads(proof.read_text());spec.update(creation_seal_sha256=creation_sha,gui_seal_sha256=gui_sha)
    proof.write_text(json.dumps(spec))
    with self.assertRaises(EvidenceError):verify()


 def test_verified_retry_can_release_the_key(self):
  with tempfile.TemporaryDirectory() as temp:
   manifest,proof,wad,creation,gui,headless=derive(Path(temp),retry=True)
   with patch('doom_hud_signal_v3.DoomStatusNumberReader',FakeHud):
    binding=verify_setup_candidate(manifest,proof,digest_file(proof),'1.3.0',digest_file(wad),1,990619,75,wad)[2]
    self.assertEqual(binding['expected_restore_tic'],715)

 def test_resealed_inconsistent_evidence_is_rejected(self):
  for fault in ('gate_source','gate_owner','gate_after_accept','deadline','wrong_focus','reserve','late_gate','late_tic','reset_tic','stale_source','stale_image','stale_bypass','headless_registration','extra_keyup'):
   with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temp:
    manifest,proof,wad,creation,gui,headless=derive(Path(temp))
    if fault in ('gate_source','gate_owner','gate_after_accept','deadline','wrong_focus','reserve','late_gate','late_tic','reset_tic','stale_source','stale_image','stale_bypass'):
     path=creation/'runtime/post-load-clock-gate.jsonl'
     rows=[json.loads(line) for line in path.read_text().splitlines()]
     gate=rows[-1]
     if fault=='gate_source':gate['source_sequence']=1
     elif fault=='gate_owner':gate['owner_state']['owned_keycodes']=[111]
     elif fault=='gate_after_accept':gate['observed_ns']=3_000_000_241
     elif fault=='wrong_focus':gate['owner_state']['focus']=12
     elif fault=='reserve':gate['first_input_clock_deadline_ns']=10**15
     elif fault=='late_tic':gate['observed_engine_tic']=2100
     elif fault=='reset_tic':gate['observed_engine_tic']=0
     elif fault in ('stale_image','stale_bypass'):
      if fault=='stale_bypass':gate['first_input_clock_deadline_ns']=gate['admission_deadline_ns']
      event_path=creation/'runtime/events.jsonl'
      events=[json.loads(line) for line in event_path.read_text().splitlines()]
      for row in events:
       if row.get('event') in ('typed_observation','observation') and row.get('id') in ('initial','cover-0'):
        row['capture_ns']-=2_000_000_000
        for signal in row.get('signals',{}).values():signal['capture_ns']=row['capture_ns']
      event_path.write_text(''.join(json.dumps(row)+'\n' for row in events))
     elif fault=='stale_source':
      gate['source_sequence']=1
      event_path=creation/'runtime/events.jsonl'
      events=[json.loads(line) for line in event_path.read_text().splitlines()]
      for row in events:
       if row.get('event')=='command' and row['command'].get('id')=='setup-move':
        row['command']['expected_sequence']=1
       if row.get('event')=='input_admission':
        row['target_process_identity'][0]=1
       if row.get('event')=='input_release_transition':
        row['admission_receipt']['target_process_identity'][0]=1
      event_path.write_text(''.join(json.dumps(row)+'\n' for row in events))
     elif fault=='late_gate':
      rows[5]['validated_ns']=3_000_000_251
      event_path=creation/'runtime/events.jsonl'
      events=[json.loads(line) for line in event_path.read_text().splitlines()]
      events[0]['post_load_clock_gate']['validated_ns']=3_000_000_251
      event_path.write_text(''.join(json.dumps(row)+'\n' for row in events))
     else:gate['first_input_clock_deadline_ns']=3_000_000_249
     path.write_text(''.join(json.dumps(row)+'\n' for row in rows))
    elif fault=='extra_keyup':
     path=creation/'runtime/owner-events.json';rows=json.loads(path.read_text())
     rows.insert(2,dict(rows[1],server_key_down_after_keyup=True));write(creation,'runtime/owner-events.json',rows)
    creation_sha=seal(creation,True)
    if fault=='headless_registration':
     reg=json.loads((headless/'registration.json').read_text());reg['expected_tic']=716
     custody(headless,reg,'30s',0)
    elif fault!='extra_keyup' or creation_sha:
     reg=json.loads((headless/'registration.json').read_text());reg['candidate_seal_sha256']=creation_sha
     custody(headless,reg,'30s',0)
    headless_sha=seal(headless,True)
    greg=json.loads((gui/'registration.json').read_text())
    greg.update(candidate_seal_sha256=creation_sha,headless_seal_sha256=headless_sha)
    custody(gui,greg,'30s',0);gui_sha=seal(gui,True)
    spec=json.loads(proof.read_text());spec.update(creation_seal_sha256=creation_sha,gui_seal_sha256=gui_sha)
    proof.write_text(json.dumps(spec))
    with patch('doom_hud_signal_v3.DoomStatusNumberReader',FakeHud):
     reason=('derived headless preregistration differs' if fault=='headless_registration'
       else 'derived owner release journal differs' if fault=='extra_keyup'
       else 'derived movement source or deadline calculation differs' if fault in ('stale_image','stale_bypass')
       else 'derived submission gate chronology or neutral owner differs')
     with self.assertRaisesRegex(EvidenceError,reason):
      verify_setup_candidate(manifest,proof,digest_file(proof),'1.3.0',digest_file(wad),1,990619,75,wad)

if __name__=='__main__':unittest.main()
