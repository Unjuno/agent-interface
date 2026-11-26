import unittest
from map01_door_driver_protocol import DoorDriverProtocol

def pair(identifier,seq,stamp):
 base={'id':identifier,'step':0,'sequence':seq,'capture_ns':stamp,'frame_rgb_sha256':'a'*64,
       'pointer_binding':{'focus':7,'surface':7,'geometry':[0,0,640,480]},
       'renewal_owner_id':'owner','input_owner_generation':0,
       'target_process_identity':{'sequence':seq,'surface':7,'digest':'b'*64},
       'target_renewal_window_identity':{'sequence':seq,'surface':7,'digest':'c'*64}}
 signals={name:{'status':'observed','value':value,'sequence':seq,'capture_ns':stamp,
                'binding':base['pointer_binding'],'signal_id':name} for name,value in (('health',100),('ammo',50))}
 return (dict(base,event='typed_observation',signals=signals),
         dict(base,event='observation',exact=True,focus_samples_match=True,input_focus_before=7,input_focus_after=7))

class ProtocolTests(unittest.TestCase):
 def test_two_arms_advance_only_after_terminal_and_settle(self):
  for arm in ('control','use'):
   p=DoorDriverProtocol(arm,'d'*64,'e'*64,'f'*64,870)
   ready={'event':'ready','fixture':{'manifest_sha256':'d'*64,'save_sha256':'e'*64,
      'after_load_tic':870,'setup_candidate_evidence':{'evidence_sha256':'f'*64}},
      'post_load_clock_gate':{'passed':True}}
   self.assertIsNone(p.receive(ready,1_000_000_000))
   for x in pair('initial',1,1_000_000_000):cmd=p.receive(x,1_100_000_000)
   self.assertEqual(cmd['id'],'cover-0')
   for i,identifier in enumerate(('cover-0','approach-1','approach-2','approach-3','approach-4','intervention'),2):
    for x in pair(identifier,i,1_000_000_000):self.assertIsNone(p.receive(x,1_100_000_000))
    settle=p.receive({'event':'terminal','id':identifier,'status':'completed'},1_100_000_000)
    self.assertEqual(settle,{'op':'door-settle'})
    retry=p.receive({'event':'door_settle','operation_id':identifier,'status':'WAIT'},1_100_000_000)
    self.assertEqual(retry,{'op':'door-settle'})
    next_cmd=p.receive({'event':'door_settle','operation_id':identifier,'status':'DONE'},1_100_000_000)
    if identifier=='intervention':self.assertEqual(next_cmd,{'op':'finish'})
    else:self.assertEqual(next_cmd['id'],'approach-'+str(i-1) if identifier!='approach-4' else 'intervention')
   self.assertEqual(p.stage,'finish')
 def test_opt_in_traversal_requires_seventh_settlement(self):
  import inspect
  self.assertIn('traverse',inspect.signature(DoorDriverProtocol).parameters)
  for arm in ('control','use'):
   p=DoorDriverProtocol(arm,'d'*64,'e'*64,'f'*64,870,traverse=True)
   p.receive({'event':'ready','fixture':{'manifest_sha256':'d'*64,'save_sha256':'e'*64,'after_load_tic':870,'setup_candidate_evidence':{'evidence_sha256':'f'*64}},'post_load_clock_gate':{'passed':True}},1_000_000_000)
   for row in pair('initial',1,1_000_000_000):p.receive(row,1_100_000_000)
   for seq,identifier in enumerate(('cover-0','approach-1','approach-2','approach-3','approach-4','intervention','traverse-1'),2):
    for row in pair(identifier,seq,1_000_000_000):p.receive(row,1_100_000_000)
    p.receive({'event':'terminal','id':identifier,'status':'completed'},1_100_000_000)
    command=p.receive({'event':'door_settle','operation_id':identifier,'status':'DONE'},1_100_000_000)
    if identifier=='intervention':self.assertEqual(command['id'],'traverse-1');self.assertEqual(command['steps'],[{'op':'hold','keys':['Up'],'duration_ms':600}])
    if identifier=='traverse-1':self.assertEqual(command,{'op':'finish'})
 def test_settlement_without_terminal_and_mismatched_observation_stop(self):
  p=DoorDriverProtocol('use','d'*64,'e'*64,'f'*64,870)
  ready={'event':'ready','fixture':{'manifest_sha256':'d'*64,'save_sha256':'e'*64,
    'after_load_tic':870,'setup_candidate_evidence':{'evidence_sha256':'f'*64}},
    'post_load_clock_gate':{'passed':True}}
  p.receive(ready,1_000_000_000)
  early,full=pair('initial',1,1_000_000_000);p.receive(early,1_100_000_000)
  broken=dict(full,sequence=2)
  with self.assertRaises(ValueError):p.receive(broken,1_100_000_000)
  q=DoorDriverProtocol('use','d'*64,'e'*64,'f'*64,870)
  q.receive(ready,1_000_000_000)
  for row in pair('initial',1,1_000_000_000):q.receive(row,1_100_000_000)
  with self.assertRaises(ValueError):q.receive({'event':'door_settle','operation_id':'cover-0','status':'DONE'},1_100_000_000)
 def test_mismatch_or_unverified_input_stops(self):
  p=DoorDriverProtocol('use','d'*64,'e'*64,'f'*64,870)
  with self.assertRaises(ValueError):p.receive({'event':'ready','fixture':{},'post_load_clock_gate':{'passed':True}},1)
  q=DoorDriverProtocol('control','d'*64,'e'*64,'f'*64,870)
  with self.assertRaises(ValueError):q.receive({'event':'input_release_unverified','id':'x'},1)
if __name__=='__main__':unittest.main()
