import json,pathlib,time
from unittest.mock import Mock
from runtime.backends.win32_v1.backend import Win32Backend
from runtime.guarded_win32_v1.fresh import FreshWin32Reference
from runtime.guarded_win32_v1.bridge import MoveBridge
import unittest

class MoveCases(unittest.TestCase):
 def _backend(self):
  b=object.__new__(Win32Backend);b.targets={'fixture':42};b.emissions=0;b.held_keys={};b.held_buttons=set();b.user32=Mock();b.user32.IsWindow.return_value=True;b.user32.GetForegroundWindow.return_value=42;b.geometry=Mock(return_value={'x':0,'y':0,'width':8,'height':8});b.identity={'thread_id':7,'process_id':11,'process_creation_time_100ns':100};b.target_identity=lambda target:dict(b.identity)
  raw=bytes(v for y in range(8) for x in range(8) for v in (x*20,y*20,255,0));b._capture_hdc=Mock(return_value=raw)
  return b

 def test_process_replacement_invalidates_before_prepare(self):
  b=self._backend();o=FreshWin32Reference(b,'fixture','images/process-before');o.observe([0,0,8,8]);o.mint('button',1,[2,2,4,4]);b.identity['process_id']=12
  bridge=MoveBridge(o,lambda intent:{'lease_id':'inert','expires_at_ns':time.monotonic_ns()+1000000000},lambda:False)
  with self.assertRaisesRegex(ValueError,'association changed'):
   bridge.prepare('button',[1,1])

 def test_process_replacement_refuses_before_input(self):
  b=self._backend();o=FreshWin32Reference(b,'fixture','images/process-after');o.observe([0,0,8,8]);o.mint('button',1,[2,2,4,4]);events=[]
  b.pointer_move=lambda t,f,x,y:events.append(['move',t,x,y]);b.release_all=lambda:{'verified':True,'keys_down':[],'buttons_down':[]}
  bridge=MoveBridge(o,lambda intent:{'lease_id':'inert','expires_at_ns':time.monotonic_ns()+1000000000},lambda:False);permit=bridge.prepare('button',[1,1]);b.identity['process_creation_time_100ns']=101
  result=bridge.execute(permit['authorization'])
  self.assertEqual(result['status'],'refused');self.assertEqual(events,[])

 def test_move_paths(self):
  rows=[]
  for mode in ['valid','pixels','focus','cancel','recovery','authority_missing']:
   b=object.__new__(Win32Backend);b.targets={'fixture':42};b.emissions=0;b.held_keys={};b.held_buttons=set();b.user32=Mock();b.user32.IsWindow.return_value=True;b.user32.GetForegroundWindow.return_value=42;b.geometry=Mock(return_value={'x':0,'y':0,'width':8,'height':8});b.target_identity=Mock(return_value={'thread_id':7,'process_id':11,'process_creation_time_100ns':100})
   raw=bytes(v for y in range(8) for x in range(8) for v in (x*20,y*20,255,0));b._capture_hdc=Mock(return_value=raw);events=[];cancel=[False]
   b.pointer_move=lambda t,f,x,y:events.append(['move',t,x,y])
   def release():events.append(['release']);return {'verified':True,'keys_down':[],'buttons_down':[]}
   b.release_all=release
   o=FreshWin32Reference(b,'fixture','images/'+mode);o.observe([0,0,8,8]);o.mint('button',1,[2,2,4,4])
   intents=[]
   def authorize(intent):
    intents.append(intent)
    return None if mode=='authority_missing' else {'lease_id':'inert-explicit-caller-lease','expires_at_ns':time.monotonic_ns()+1000000000}
   bridge=MoveBridge(o,authorize,lambda:cancel[0])
   if mode=='authority_missing':
    try:bridge.prepare('button',[1,1]);raise AssertionError('missing authority accepted')
    except ValueError as e:assert 'authority unavailable' in str(e)
    assert not events and not bridge.permits;rows.append({'mode':mode,'authority_refused':True,'events':events});continue
   permit=bridge.prepare('button',[1,1]);assert intents[0]['point']==[3,3]
   if mode=='pixels':b._capture_hdc.return_value=bytes([255,0,0,0])*64
   if mode=='focus':b.user32.GetForegroundWindow.return_value=43
   if mode=='cancel':cancel[0]=True
   if mode=='recovery':bridge.session.recovery_required=True
   result=bridge.execute(permit['authorization']);before=list(events);replay=bridge.execute(permit['authorization']);assert replay['error']=='AUTHORIZATION_CONSUMED_OR_UNKNOWN' and events==before
   if mode=='valid':assert result['status']=='completed' and events==[['move','fixture',3,3],['release']]
   else:assert result['status']=='refused' and events==[]
   rows.append({'mode':mode,'permit':permit,'result':result,'replay':replay,'events':events,'capture_calls':b._capture_hdc.call_count})
  pathlib.Path('raw.json').write_text(json.dumps(rows,indent=2),encoding='utf-8');print('PASS six actual fresh-reference/core/session/bound-execution composition cases; native emitters inert')

if __name__=="__main__":unittest.main()
