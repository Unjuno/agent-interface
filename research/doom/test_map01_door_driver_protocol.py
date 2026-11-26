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

class ReverseProtocolTests(unittest.TestCase):
 def test_reverse_program_is_driven_only_after_settled_observations(self):
  from map01_reverse_program import reverse_stages
  for arm in ('control','use','calibrate'):
   p=DoorDriverProtocol('use','d'*64,'e'*64,'f'*64,870,traverse=True,reverse_arm=arm)
   from map01_reverse_program import reverse_manifest
   ready={'event':'ready','fixture':{'manifest_sha256':'d'*64,'save_sha256':'e'*64,
      'after_load_tic':870,'setup_candidate_evidence':{'evidence_sha256':'f'*64}},
      'post_load_clock_gate':{'passed':True},'reverse_door_program':reverse_manifest(arm)}
   wrong=dict(ready,reverse_door_program=reverse_manifest('control' if arm!='control' else 'use'))
   with self.assertRaises(ValueError):p.receive(wrong,1_000_000_000)
   p.receive(ready,1_000_000_000)
   for x in pair('initial',1,1_000_000_000):cmd=p.receive(x,1_100_000_000)
   prefix=[('cover-0',[{'op':'coast','duration_ms':200,'sample_ms':100}])]
   prefix += [('approach-'+str(i),[{'op':'hold','keys':['Up'],'duration_ms':600}]) for i in range(1,5)]
   prefix += [('intervention',[{'op':'hold','keys':['e'],'duration_ms':120}]),('traverse-1',[{'op':'hold','keys':['Up'],'duration_ms':300}])]
   program=prefix+reverse_stages(arm)
   for sequence,(identifier,steps) in enumerate(program,2):
    self.assertEqual((cmd['id'],cmd['steps']),(identifier,steps))
    for x in pair(identifier,sequence,1_000_000_000):p.receive(x,1_100_000_000)
    self.assertEqual(p.receive({'event':'terminal','id':identifier,'status':'completed'},1_100_000_000),{'op':'door-settle'})
    cmd=p.receive({'event':'door_settle','operation_id':identifier,'status':'DONE'},1_100_000_000)
   self.assertEqual(cmd,{'op':'finish'});self.assertEqual(p.stage,'finish')
 def test_legacy_driver_rejects_reverse_runtime_before_initial_input(self):
  from map01_reverse_program import reverse_manifest
  p=DoorDriverProtocol('use','d'*64,'e'*64,'f'*64,870,traverse=True)
  ready={'event':'ready','fixture':{'manifest_sha256':'d'*64,'save_sha256':'e'*64,
    'after_load_tic':870,'setup_candidate_evidence':{'evidence_sha256':'f'*64}},
    'post_load_clock_gate':{'passed':True},'reverse_door_program':reverse_manifest('calibrate')}
  with self.assertRaises(ValueError):p.receive(ready,1_000_000_000)
  self.assertFalse(p.ready);self.assertIsNone(p.pending)
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
 def test_final_exit_probe_allows_unknown_hud_without_allowing_more_input(self):
  import inspect
  self.assertIn('exit_arm',inspect.signature(DoorDriverProtocol).parameters)
  for arm in ('control','use'):
   p=DoorDriverProtocol('use','d'*64,'e'*64,'f'*64,870,traverse=True,exit_probe=True,exit_arm=arm)
   p.receive({'event':'ready','fixture':{'manifest_sha256':'d'*64,'save_sha256':'e'*64,'after_load_tic':870,'setup_candidate_evidence':{'evidence_sha256':'f'*64}},'post_load_clock_gate':{'passed':True}},1_000_000_000)
   for row in pair('initial',1,1_000_000_000):p.receive(row,1_100_000_000)
   for seq,identifier in enumerate(('cover-0','approach-1','approach-2','approach-3','approach-4','intervention','traverse-1','exit-probe'),2):
    early,full=pair(identifier,seq,1_000_000_000)
    if identifier=='exit-probe':
     for signal in early['signals'].values():signal.update(status='unknown',value=None)
    p.receive(early,1_100_000_000);p.receive(full,1_100_000_000)
    p.receive({'event':'terminal','id':identifier,'status':'completed'},1_100_000_000)
    command=p.receive({'event':'door_settle','operation_id':identifier,'status':'DONE'},1_100_000_000)
    if identifier=='traverse-1':
     expected=[{'op':'hold','keys':['e'],'duration_ms':120}] if arm=='use' else [{'op':'coast','duration_ms':120,'sample_ms':100}]
     self.assertEqual(command['id'],'exit-probe');self.assertEqual(command['steps'],expected)
    if identifier=='exit-probe':self.assertEqual(command,{'op':'finish'})
   self.assertEqual(p.stage,'finish')
 def test_direct_exit_probe_has_only_cover_and_final(self):
  import inspect
  self.assertIn('direct_exit',inspect.signature(DoorDriverProtocol).parameters)
  p=DoorDriverProtocol('use','d'*64,'e'*64,'f'*64,870,traverse=True,exit_probe=True,exit_arm='use',direct_exit=True)
  p.receive({'event':'ready','fixture':{'manifest_sha256':'d'*64,'save_sha256':'e'*64,'after_load_tic':870,'setup_candidate_evidence':{'evidence_sha256':'f'*64}},'post_load_clock_gate':{'passed':True}},1_000_000_000)
  for row in pair('initial',1,1_000_000_000):p.receive(row,1_100_000_000)
  for seq,identifier in ((2,'cover-0'),(3,'exit-probe')):
   for row in pair(identifier,seq,1_000_000_000):p.receive(row,1_100_000_000)
   p.receive({'event':'terminal','id':identifier,'status':'completed'},1_100_000_000)
   cmd=p.receive({'event':'door_settle','operation_id':identifier,'status':'DONE'},1_100_000_000)
   if identifier=='cover-0':self.assertEqual(cmd['id'],'exit-probe')
   else:self.assertEqual(cmd,{'op':'finish'})
 def test_unknown_hud_before_final_probe_is_rejected(self):
  p=DoorDriverProtocol('use','d'*64,'e'*64,'f'*64,870,traverse=True,exit_probe=True,exit_arm='use')
  p.receive({'event':'ready','fixture':{'manifest_sha256':'d'*64,'save_sha256':'e'*64,'after_load_tic':870,'setup_candidate_evidence':{'evidence_sha256':'f'*64}},'post_load_clock_gate':{'passed':True}},1_000_000_000)
  early,_=pair('initial',1,1_000_000_000)
  early['signals']['health'].update(status='unknown',value=None)
  with self.assertRaises(ValueError):p.receive(early,1_100_000_000)
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
