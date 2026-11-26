import unittest,hashlib,json
from map01_door_task_contract import DoorTaskContract

def command(identifier,steps,sequence=1):
 return {'op':'submit','id':identifier,'steps':steps,'expected_sequence':sequence,'valid_until_ns':25_000_000_000}

def state(seq=1,stamp=1_000_000_000):
 return {'id':'cover-0' if seq==1 else 'approach-'+str(seq-1),'sequence':seq,'capture_ns':stamp,
         'exact':True,'focus_samples_match':True,'input_focus_before':7,'input_focus_after':7,
         'renewal_owner_id':'owner','input_owner_generation':0,
         'pointer_binding':{'focus':7,'surface':7},
         'target_process_identity':{'sequence':seq,'surface':7,'digest':'abc'},
         'target_renewal_window_identity':{'sequence':seq,'surface':7,'digest':'def'}}

def release(identifier,token='token'):
 return {'id':identifier,'status':'completed','input_owner_id':'owner','input_owner_generation':0,
         'release':{'event':'owner_release','intent_token':token,'verified':True,
                    'keys_down':[],'buttons_down':[],'keys_unknown':[],'key_state_errors':[]}}

def accepted(identifier,token='token'):
 return {'id':identifier,'intent_token':token}


def finish(gate,c,mutate=None):
 identifier=c['id'];steps=c['steps'];a=accepted(identifier);a.update(
  event='accepted',accepted_ns=1_150_000_000,steps=len(steps),program_sha256=hashlib.sha256(json.dumps(steps,sort_keys=True,separators=(',',':')).encode()).hexdigest())
 t=release(identifier);t.update(event='terminal',terminal_ns=1_800_000_000,steps_completed=len(steps))
 t['release']['verified_ns']=1_700_000_000
 if steps[0]['op']=='coast':t['release']['intent_token']=None
 rows=[a]
 if steps[0]['op']=='hold':
  key=steps[0]['keys'][0]
  held_ns=1_310_000_000;release_ns=held_ns+steps[0]['duration_ms']*1_000_000
  t['release']['verified_ns']=release_ns+30_000_000;t['terminal_ns']=release_ns+40_000_000
  down={'event':'input_admission','id':identifier,'step':0,'key':key,'keycode':111,
        'owner_id':'owner','intent_token':'token','admitted_ns':1_200_000_000,'input_ack_ns':1_300_000_000,
        'first_press_deadline_ns':2_100_000_000,'first_press_submission_checked_before_deadline':True,
        'valid_until_ns':c['valid_until_ns'],'target_process_identity':[c['expected_sequence'],7,'abc',c['valid_until_ns']]}
  attempt={'attempt':1,'keyrelease_started_ns':release_ns,'sync_returned_ns':release_ns+10_000_000,
           'keymap_sampled_ns':release_ns+20_000_000,'server_key_down_before':True,'server_key_down_after':False}
  up={'event':'owner_explicit_keyup','operation':'up','owner_id':'owner','key':key,'keycode':111,
      'intent_token':'token','valid_until_ns':c['valid_until_ns'],'owner_keyrelease_started_ns':release_ns,
      'owner_sync_returned_ns':release_ns+10_000_000,'owner_keymap_sampled_ns':release_ns+20_000_000,'server_keyup_verified':True,
      'server_keyup_attempt_count':1,'server_keyup_attempts':[attempt],'server_key_down_after_keyup':False,
      'key_state_source':'x11_query_keymap','server_sync_completed':True,'physical_verification_authoritative':False,
      'cancel_requested_after_sync':False,'release_batch_initial_up_count':1,'release_batch_key_order':[key]}
  transition={'event':'input_release_transition','id':identifier,'step':0,'operation':'up','key':key,
   'owner_id':'owner','intent_token':'token','owner_transition_verified':True,'admission_receipt_valid':True,
   'admission_receipt':dict(down,operation='down'),'owner_thread_keyup_receipt':up}
  held={'event':'keys_held','id':identifier,'step':0,'keys':[key],'input_ack_ns':held_ns}
  observed=state(c['expected_sequence']+1,release_ns+25_000_000)
  observed.update(id=identifier,step=0,frame_rgb_sha256='a'*64)
  rows.extend((down,held,transition,dict(observed,event='typed_observation'),
               dict(observed,event='observation'),
               {'event':'step_completed','id':identifier,'step':0,'completed_ns':release_ns+28_000_000}))
 if steps[0]['op']=='coast':
  observed=state(c['expected_sequence']+1,1_400_000_000);observed.update(id=identifier,step=0,frame_rgb_sha256='a'*64)
  rows.extend(({'event':'step_started','id':identifier,'step':0,'operation':'coast','issued_ns':1_200_000_000},
               dict(observed,event='typed_observation'),
               dict(observed,event='observation'),
               {'event':'coast_result','id':identifier,'step':0,'samples':1,'elapsed_ms':float(steps[0]['duration_ms']),'input_admissions':0,'sequence':c['expected_sequence']+1},
               {'event':'step_completed','id':identifier,'step':0,'completed_ns':1_600_000_000}))
 rows.append(t)
 for row in rows:row['emit_ns']=1_700_000_000
 if mutate is not None:mutate(rows)
 gate.completed(identifier,dict(t,emit_ns=1_700_000_000),dict(a,emit_ns=1_100_000_001),rows)

class DoorTaskContractTests(unittest.TestCase):
 def test_initial_cover_requires_fixed_coast_and_proven_completion(self):
  from map01_door_task_contract import validate_initial_cover
  source=state();source['id']='initial'
  c=command('cover-0',[{'op':'coast','duration_ms':200,'sample_ms':100}])
  class Adapter:
   def completed(self,identifier,terminal,accepted,events):
    validate_initial_cover(source,terminal,accepted,events)
  finish(Adapter(),c)
  def no_samples(rows):rows.pop(4)
  with self.assertRaises(ValueError):finish(Adapter(),c,no_samples)
  bad=dict(source,id='wrong')
  class WrongSource:
   def completed(self,identifier,terminal,accepted,events):
    validate_initial_cover(bad,terminal,accepted,events)
  with self.assertRaises(ValueError):finish(WrongSource(),c)
 def test_fixed_control_and_use_sequences(self):
  for arm in ('control','use'):
   gate=DoorTaskContract(arm)
   for i in range(4):
    c=command('approach-'+str(i+1),[{'op':'hold','keys':['Up'],'duration_ms':600}],i+1)
    deadline=gate.authorize(c,state(i+1),1_100_000_000,release('cover-0' if i==0 else 'approach-'+str(i)), accepted('cover-0' if i==0 else 'approach-'+str(i)))
    self.assertEqual(deadline,2_100_000_000)
    finish(gate,c)
   step=([{'op':'hold','keys':['e'],'duration_ms':120}] if arm=='use'
         else [{'op':'coast','duration_ms':120,'sample_ms':100}])
   c=command('intervention',step,5)
   gate.authorize(c,state(5),1_100_000_000,release('approach-4'),accepted('approach-4'));finish(gate,c)
   self.assertTrue(gate.finished)
   with self.assertRaises(ValueError):
    gate.authorize(c,state(6),1_100_000_000,release('intervention'),accepted('intervention'))
 def test_opt_in_traverse_requires_verified_intervention_and_keyup(self):
  import inspect
  self.assertIn('traverse',inspect.signature(DoorTaskContract).parameters)
  for arm in ('control','use'):
   gate=DoorTaskContract(arm,traverse=True)
   for i in range(4):
    c=command('approach-'+str(i+1),[{'op':'hold','keys':['Up'],'duration_ms':600}],i+1)
    gate.authorize(c,state(i+1),1_100_000_000,release('cover-0' if i==0 else 'approach-'+str(i)),accepted('cover-0' if i==0 else 'approach-'+str(i)));finish(gate,c)
   step=[{'op':'hold','keys':['e'],'duration_ms':120}] if arm=='use' else [{'op':'coast','duration_ms':120,'sample_ms':100}]
   c=command('intervention',step,5);gate.authorize(c,state(5),1_100_000_000,release('approach-4'),accepted('approach-4'));finish(gate,c)
   self.assertFalse(gate.finished)
   source=state(6);source['id']='intervention'
   c=command('traverse-1',[{'op':'hold','keys':['Up'],'duration_ms':600}],6)
   with self.assertRaises(ValueError):gate.authorize(c,source,1_100_000_000,release('wrong'),accepted('wrong'))
   prior=release('intervention')
   if arm=='control':prior['release']['intent_token']=None
   gate.authorize(c,source,1_100_000_000,prior,accepted('intervention'))
   with self.assertRaises(ValueError):gate.completed('traverse-1',release('traverse-1'),accepted('traverse-1'),[])
   finish(gate,c);self.assertTrue(gate.finished)
 def test_each_submit_requires_new_source_and_same_target(self):
  gate=DoorTaskContract('use')
  c=command('approach-1',[{'op':'hold','keys':['Up'],'duration_ms':600}])
  gate.authorize(c,state(),1_100_000_000,release('cover-0'),accepted('cover-0'));finish(gate,c)
  c2=command('approach-2',[{'op':'hold','keys':['Up'],'duration_ms':600}],1)
  with self.assertRaises(ValueError):
   gate.authorize(c2,state(1),1_100_000_000,release('approach-1'),accepted('approach-1'))
  altered=state(2);altered['target_process_identity']['digest']='different'
  c2['expected_sequence']=2
  with self.assertRaises(ValueError):
   gate.authorize(c2,altered,1_100_000_000,release('approach-1'),accepted('approach-1'))
 def test_missing_admission_or_keyup_cannot_complete(self):
  gate=DoorTaskContract('use')
  c=command('approach-1',[{'op':'hold','keys':['Up'],'duration_ms':600}])
  gate.authorize(c,state(),1_100_000_000,release('cover-0'),accepted('cover-0'))
  with self.assertRaises(ValueError):
   gate.completed(c['id'],release(c['id']),accepted(c['id']),[])
  self.assertFalse(gate.finished)
 def test_submit_live_passes_deadline_and_refuses_retry_on_submit_failure(self):
  class Gate:
   clock_reserve_deadline_ns=5_000_000_000
   def clock(self):return 1_150_000_000
   def _clock_reserve_deadline(self,engine,started):return 1_900_000_000
   def _owner_and_source(self,backend,source,command,started):
    return 'owner',0,{'sample_started_ns':1_120_000_000,'sample_finished_ns':1_140_000_000},{}
  class Executor:
   active=None
   def __init__(self,fail=False):self.calls=[];self.fail=fail
   def submit(self,*args,**kwargs):
    self.calls.append((args,kwargs))
    if self.fail:raise RuntimeError('submit uncertain')
  c=command('approach-1',[{'op':'hold','keys':['Up'],'duration_ms':600}])
  executor=Executor();gate=DoorTaskContract('use')
  gate.submit_live(c,state(),1_100_000_000,release('cover-0'),accepted('cover-0'),Gate(),True,executor)
  self.assertEqual(executor.calls[0][1],{'admission_deadline_ns':1_900_000_000})
  other=DoorTaskContract('use');failing=Executor(fail=True)
  with self.assertRaises(RuntimeError):
   other.submit_live(c,state(),1_100_000_000,release('cover-0'),accepted('cover-0'),Gate(),True,failing)
  with self.assertRaises(ValueError):
   other.submit_live(c,state(),1_100_000_000,release('cover-0'),accepted('cover-0'),Gate(),True,failing)
  self.assertEqual(len(failing.calls),1)
 def test_live_gate_returns_stricter_deadline_for_executor(self):
  class Gate:
   clock_reserve_deadline_ns=5_000_000_000
   def clock(self):return 1_150_000_000
   def _clock_reserve_deadline(self,engine,started):return 1_900_000_000
   def _owner_and_source(self,backend,source,command,started):
    if not backend:raise ValueError('owner unavailable')
    return 'owner',0,{'sample_started_ns':1_120_000_000,'sample_finished_ns':1_140_000_000},{}
  gate=DoorTaskContract('use');c=command('approach-1',[{'op':'hold','keys':['Up'],'duration_ms':600}])
  deadline=gate.authorize_live(c,state(),1_100_000_000,release('cover-0'),accepted('cover-0'),Gate(),True)
  self.assertEqual(deadline,1_900_000_000)
  self.assertEqual(gate.deadline,deadline)
  other=DoorTaskContract('use')
  with self.assertRaises(ValueError):
   other.authorize_live(c,state(),1_100_000_000,release('cover-0'),accepted('cover-0'),Gate(),False)
  self.assertIsNone(other.inflight)
  class Expired(Gate):
   def clock(self):return 2_100_000_001
  expired=DoorTaskContract('use')
  with self.assertRaises(ValueError):
   expired.authorize_live(c,state(),1_100_000_000,release('cover-0'),accepted('cover-0'),Expired(),True)
  self.assertIsNone(expired.inflight)
 def test_control_coast_requires_real_observation_and_no_held_keys(self):
  gate=DoorTaskContract('control')
  for i in range(4):
   c=command('approach-'+str(i+1),[{'op':'hold','keys':['Up'],'duration_ms':600}],i+1)
   gate.authorize(c,state(i+1),1_100_000_000,release('cover-0' if i==0 else 'approach-'+str(i)),accepted('cover-0' if i==0 else 'approach-'+str(i)))
   finish(gate,c)
  c=command('intervention',[{'op':'coast','duration_ms':120,'sample_ms':100}],5)
  gate.authorize(c,state(5),1_100_000_000,release('approach-4'),accepted('approach-4'))
  def held_keys(rows):rows[4]['keys_held']=['Up']
  with self.assertRaises(ValueError):finish(gate,c,held_keys)
  def no_result(rows):rows.pop(4)
  def held_event(rows):rows.insert(4,{'event':'keys_held','id':'intervention','keys':['Up']})
  with self.assertRaises(ValueError):finish(gate,c,held_event)
  with self.assertRaises(ValueError):finish(gate,c,no_result)
  self.assertFalse(gate.finished)
 def test_stricter_executor_deadline_is_accepted(self):
  gate=DoorTaskContract('use')
  c=command('approach-1',[{'op':'hold','keys':['Up'],'duration_ms':600}])
  gate.authorize(c,state(),1_100_000_000,release('cover-0'),accepted('cover-0'))
  def stricter(rows):
   rows[1]['first_press_deadline_ns']=1_900_000_000
   rows[3]['admission_receipt']['first_press_deadline_ns']=1_900_000_000
  finish(gate,c,stricter)
  self.assertEqual(gate.index,1)
 def test_invalid_key_receipts_do_not_advance(self):
  def missing(rows):rows.pop(1)
  def late(rows):rows[1]['input_ack_ns']=2_100_000_000
  def wrong_release(rows):rows[3]['owner_thread_keyup_receipt']['server_keyup_verified']=False
  def wrong_program(rows):rows[0]['program_sha256']='0'*64
  def wrong_receipt_kind(rows):rows[3]['owner_thread_keyup_receipt'].update(event='owner_release',verified=True)
  def reversed_events(rows):rows[1],rows[3]=rows[3],rows[1]
  def early_terminal(rows):rows[-1]['terminal_ns']=1_550_000_000
  def no_post_release_frame(rows):
   rows[:]=[row for row in rows if row.get('event') not in ('typed_observation','observation')]
  def short_hold(rows):
   up=rows[3]['owner_thread_keyup_receipt'];attempt=up['server_keyup_attempts'][0]
   for key in ('owner_keyrelease_started_ns','owner_sync_returned_ns','owner_keymap_sampled_ns'):up[key]-=1_000_000
   for key in ('keyrelease_started_ns','sync_returned_ns','keymap_sampled_ns'):attempt[key]-=1_000_000
  for mutation in (missing,late,wrong_release,wrong_program,wrong_receipt_kind,reversed_events,early_terminal,short_hold,no_post_release_frame):
   with self.subTest(mutation=mutation.__name__):
    gate=DoorTaskContract('use')
    c=command('approach-1',[{'op':'hold','keys':['Up'],'duration_ms':600}])
    gate.authorize(c,state(),1_100_000_000,release('cover-0'),accepted('cover-0'))
    with self.assertRaises(ValueError):finish(gate,c,mutation)
    self.assertFalse(gate.finished)
    with self.assertRaises(ValueError):
     gate.authorize(c,state(),1_100_000_000,release('cover-0'),accepted('cover-0'))
 def test_unstarted_operation_cannot_finish(self):
  gate=DoorTaskContract('use')
  with self.assertRaises(ValueError):
   gate.completed(None,None,None,[])
  self.assertFalse(gate.finished)

 def test_completion_requires_own_verified_release(self):
  gate=DoorTaskContract('use')
  c=command('approach-1',[{'op':'hold','keys':['Up'],'duration_ms':600}])
  gate.authorize(c,state(),1_100_000_000,release('cover-0'),accepted('cover-0'))
  with self.assertRaises(ValueError):gate.completed(c['id'],None,None,[])
  self.assertFalse(gate.finished)
 def test_no_skip_duplicate_or_extra_key(self):
  gate=DoorTaskContract('use')
  for c in (command('approach-2',[{'op':'hold','keys':['Up'],'duration_ms':600}]),
            command('approach-1',[{'op':'hold','keys':['space'],'duration_ms':600}]),
            command('approach-1',[{'op':'hold','keys':['Up','e'],'duration_ms':600}])):
   with self.subTest(c=c),self.assertRaises(ValueError):gate.authorize(c,state(),1_100_000_000,release('cover-0'),accepted('cover-0'))
 def test_reject_stale_source_and_unverified_previous_release(self):
  gate=DoorTaskContract('use')
  c=command('approach-1',[{'op':'hold','keys':['Up'],'duration_ms':600}])
  with self.assertRaises(ValueError):gate.authorize(c,state(),3_000_000_000,release('cover-0'),accepted('cover-0'))
  gate.authorize(c,state(),1_100_000_000,release('cover-0'),accepted('cover-0'));finish(gate,c)
  c2=command('approach-2',[{'op':'hold','keys':['Up'],'duration_ms':600}],2)
  for bad in (None,dict(release('approach-1'),release=dict(release('approach-1')['release'],verified=False)),
              dict(release('approach-1'),release=dict(release('approach-1')['release'],keys_down=['Up'])),
              dict(release('approach-1'),input_owner_id='other')):
   with self.subTest(bad=bad),self.assertRaises(ValueError):gate.authorize(c2,state(2),1_100_000_000,bad,accepted('approach-1'))
if __name__=='__main__':unittest.main()
