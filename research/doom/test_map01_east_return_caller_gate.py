"""Ordering of post-cross guard and a real simulated caller write."""
import copy
import ast
import io
import json
import time
import hashlib
import os
import selectors
import tempfile
from types import SimpleNamespace
import unittest
from pathlib import Path
from PIL import Image
from map01_east_return_caller_gate import EastReturnCallerGate, require_no_pending_output, require_new_frame

class CallerGateTests(unittest.TestCase):
 def test_guard_requires_the_registered_reverse_arm(self):
  identity={'surface':7,'owner':'owner','generation':3,'process_digest':'proc','window_digest':'window'}
  gate=EastReturnCallerGate(reference='/tmp/ref',reference_sha256='a'*64,runtime_dir='/tmp',identity=identity,arm='east-return-turn75')
  gate.full={'sequence':4}
  command={'op':'submit','id':'east-turn-1','steps':[{'op':'hold','keys':['Right'],'duration_ms':600}],'expected_sequence':4}
  protocol=SimpleNamespace(ready=True,reverse_arm='east-return-turn75',pending='east-turn-1',typed=None,identity=(7,'owner',3,'proc','window'),latest=gate.full)
  self.assertTrue(gate._protocol_matches(protocol,command))
  protocol.reverse_arm='east-return'
  self.assertFalse(gate._protocol_matches(protocol,command))
  with self.assertRaises(ValueError):EastReturnCallerGate(reference='/tmp/ref',reference_sha256='a'*64,runtime_dir='/tmp',identity=identity,arm='unexpected')
 def test_new_frame_gate_rejects_reuse_and_mismatched_image_number(self):
  source={'event':'observation','id':'reverse-cross','sequence':4,'image_reused':False,'image':'/tmp/004.png'}
  self.assertIsNone(require_new_frame(source,'reverse-cross'))
  for wrong in (dict(source,image_reused=True),dict(source,image='/tmp/003.png'),dict(source,id='other')):
   with self.assertRaises(ValueError):require_new_frame(wrong,'reverse-cross')
 def test_buffered_or_readable_stdout_refuses_before_any_write(self):
  read_fd,write_fd=os.pipe()
  try:
   with selectors.DefaultSelector() as selector:
    selector.register(read_fd,selectors.EVENT_READ)
    writes=[]
    def write_if_clear(buffer):
     require_no_pending_output(buffer,selector)
     writes.append('submitted')
    with self.assertRaises(ValueError):write_if_clear(b'{"event":"input_release_unverified"}\n')
    self.assertEqual(writes,[])
    os.write(write_fd,b'{"event":"input_release_unverified"}\n')
    with self.assertRaises(ValueError):write_if_clear(b'')
    self.assertEqual(writes,[])
    os.read(read_fd,4096);write_if_clear(b'');self.assertEqual(writes,['submitted'])
  finally:
   os.close(read_fd);os.close(write_fd)
 def test_driver_does_not_write_after_done_with_buffered_unverified_release(self):
  driver=Path(__file__).with_name('map01_os_east_return_driver.py')
  tree=ast.parse(driver.read_text());functions=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in ('read_stream','send','require','emit')]
  scope={'json':json,'os':os,'time':time,'uptime_ns':time.perf_counter_ns}
  exec(compile(ast.Module(body=functions,type_ignores=[]),str(driver),'exec'),scope)
  runtime_read,runtime_write=os.pipe();input_read,input_write=os.pipe()
  try:
   with selectors.DefaultSelector() as selector:
    selector.register(runtime_read,selectors.EVENT_READ)
    process=SimpleNamespace(stdout=SimpleNamespace(fileno=lambda:runtime_read),stdin=SimpleNamespace(fileno=lambda:input_write))
    first={'event':'door_settle','operation_id':'reverse-cross','status':'DONE'}
    following={'event':'input_release_unverified','id':'reverse-cross'}
    os.write(runtime_write,(json.dumps(first)+'\n'+json.dumps(following)+'\n').encode())
    row,buffer=scope['read_stream'](process,io.BytesIO(),io.StringIO(),b'',selector,time.perf_counter_ns()+1_000_000_000)
    self.assertEqual(row,first);self.assertIn(b'input_release_unverified',buffer)
    command={'op':'submit','id':'east-turn-1','steps':[{'op':'hold','keys':['Right'],'duration_ms':600}]}
    with self.assertRaisesRegex(ValueError,'runtime output pending'):
     scope['send'](process,io.StringIO(),command,before_write=lambda:require_no_pending_output(buffer,selector))
    os.set_blocking(input_read,False)
    with self.assertRaises(BlockingIOError):os.read(input_read,4096)
  finally:
   for fd in (runtime_read,runtime_write,input_read,input_write):os.close(fd)
 def test_guard_binds_settled_last_frame_and_is_consumed_at_write(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);ref=root/'ref.png';frame=root/'004.png'
   Image.new('RGB',(1280,800),(10,20,30)).save(ref);Image.new('RGB',(1280,800),(10,20,30)).save(frame)
   digest=hashlib.sha256(ref.read_bytes()).hexdigest()
   with Image.open(frame) as im:rgb=hashlib.sha256(im.convert('RGB').tobytes()).hexdigest()
   full={'event':'observation','id':'reverse-cross','step':0,'sequence':4,'capture_ns':100,'image':str(frame),'image_reused':False,'frame_rgb_sha256':rgb,
    'pointer_binding':{'surface':7,'focus':7,'geometry':[321,180,640,480]},'input_focus_before':7,'input_focus_after':7,
    'exact':True,'focus_samples_match':True,'renewal_owner_id':'owner','input_owner_generation':3,
    'target_process_identity':{'sequence':4,'surface':7,'digest':'proc'},'target_renewal_window_identity':{'sequence':4,'surface':7,'digest':'window'}}
   typed=copy.deepcopy(full);typed['event']='typed_observation';typed.pop('image')
   transition={'event':'input_release_transition','id':'reverse-cross','operation':'up','key':'Up','owner_id':'owner','intent_token':'token','owner_transition_verified':True,'admission_receipt_valid':True,'release_batch_complete':True,'owner_sample_ordered_after_batch':True,'owner_identity_matches_after_batch':True,'intent_token_matches_after_batch':True,'owned_keycodes_after_batch':[],'owner_thread_keyup_verified_after_batch':True,'owner_sample_after_finished_ns':90,'owner_thread_keyup_receipt':{'server_keyup_verified':True,'owner_keymap_sampled_ns':85,'owner_id':'owner','intent_token':'token','key':'Up'}}
   terminal={'event':'terminal','id':'reverse-cross','status':'completed','terminal_ns':150,'input_owner_id':'owner','input_owner_generation':3,'release':{'verified':True,'keys_down':[],'buttons_down':[],'keys_unknown':[],'key_state_errors':[],'intent_token':'token'}}
   settled={'event':'door_settle','operation_id':'reverse-cross','status':'DONE','emit_ns':160}
   identity={'owner':'owner','generation':3,'surface':7,'process_digest':'proc','window_digest':'window','geometry':[321,180,640,480]}
   command={'op':'submit','id':'east-turn-1','steps':[{'op':'hold','keys':['Right'],'duration_ms':600}],'expected_sequence':4,'valid_until_ns':500}
   protocol=SimpleNamespace(latest=full,pending='east-turn-1',typed=None,ready=True,reverse_arm='east-return',identity=(7,'owner',3,'proc','window'))
   variant=EastReturnCallerGate(reference=ref,reference_sha256=digest,runtime_dir=root,identity=identity,arm='east-return-turn75')
   for event in (transition,typed,full,terminal,settled):variant.receive(event)
   protocol.reverse_arm='east-return-turn75'
   self.assertTrue(variant.prepare(command,protocol,clock=lambda:200)['passed'])
   protocol.reverse_arm='east-return'
   def ready():
    gate=EastReturnCallerGate(reference=ref,reference_sha256=digest,runtime_dir=root,identity=identity)
    for event in (transition,typed,full,terminal,settled):gate.receive(event)
    return gate
   gate=ready();receipt=gate.prepare(command,protocol,clock=lambda:200);self.assertTrue(receipt['passed'])
   writes=[]
   def send(current,cmd,now):
    protocol.latest=current;gate.before_write(cmd,protocol,now=now,absolute_deadline=400);writes.append(cmd)
   stale=copy.deepcopy(full);stale['sequence']=5
   with self.assertRaises(ValueError):send(stale,command,250)
   self.assertEqual(writes,[])
   with self.assertRaises(ValueError):send(full,command,250)
   protocol.latest=full;gate=ready();gate.prepare(command,protocol,clock=lambda:200)
   with self.assertRaises(ValueError):send(full,command,500)
   self.assertEqual(writes,[])
   protocol.latest=full;gate=ready();gate.prepare(command,protocol,clock=lambda:200)
   send(full,command,250);self.assertEqual(len(writes),1)
   with self.assertRaises(ValueError):send(full,command,251)
   self.assertEqual(len(writes),1)
   protocol.latest=full;gate=ready();gate.prepare(command,protocol,clock=lambda:200)
   newer=copy.deepcopy(full);newer['sequence']=5
   with self.assertRaises(ValueError):gate.receive(newer)
   with self.assertRaises(ValueError):gate.before_write(command,protocol,now=250,absolute_deadline=400)
   gate=EastReturnCallerGate(reference=ref,reference_sha256=digest,runtime_dir=root,identity=identity)
   for event in (transition,typed,full,terminal):gate.receive(event)
   with self.assertRaises(ValueError):gate.prepare(command,protocol,clock=lambda:200)
   Image.new('RGB',(1280,800),(240,240,240)).save(frame)
   with Image.open(frame) as im:wrong=hashlib.sha256(im.convert('RGB').tobytes()).hexdigest()
   full['frame_rgb_sha256']=wrong;typed['frame_rgb_sha256']=wrong;protocol.latest=full
   gate=ready()
   with self.assertRaisesRegex(ValueError,'image gate refused'):gate.prepare(command,protocol,clock=lambda:200)
   self.assertFalse(gate.receipt['passed']);self.assertGreater(gate.receipt['difference_sum'],0)
if __name__=='__main__':unittest.main()
