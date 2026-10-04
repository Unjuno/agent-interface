import pathlib,time,json
import runtime.guarded_win32_v1.test_late_state as fixtures
import unittest

class EffectCases(unittest.TestCase):
 def test_integration_variants(self):
  rows=[]
  for mode in ['changed_pixels','unchanged_pixels','capture_error','callback_binding_change','no_verifier']:
   b,o,s,raw,events=fixtures.Cases('test_exact_expiry_consumes_without_capture').fixture();p=s.prepare('button',[1,1]);base_move=b.pointer_move
   def move(*args):
    base_move(*args)
    if mode=='changed_pixels':b._capture_hdc.return_value=bytes([255,0,0,0])*64
    if mode=='capture_error':b._capture_hdc.side_effect=RuntimeError('inert post-action capture error')
   b.pointer_move=move;seen=[]
   def verifier(program,execution,row,image):
    seen.append(row['sequence']);assert row['sequence']==3 and execution['status']=='completed'
    if mode=='callback_binding_change':b.user32.GetForegroundWindow.return_value=43;return True
    return image.getpixel((0,0))==(0,0,255)
   result=s.execute(p['authorization']) if mode=='no_verifier' else s.execute(p['authorization'],verify_effect=verifier,effect_deadline_ns=time.monotonic_ns()+1000000000)
   assert result['status']=='completed' and events==[['move','fixture',3,3],['release']]
   if mode=='changed_pixels':assert result['task_success'] is True and result['effect']['status']=='verified'
   elif mode=='unchanged_pixels':assert result['task_success'] is False
   elif mode=='no_verifier':assert result.get('task_success') is None and not seen
   else:assert result['task_success'] is None and result['effect']['status']=='unknown'
   assert s.execute(p['authorization'])['error']=='AUTHORIZATION_CONSUMED_OR_UNKNOWN'
   assert not s.lock.locked()
   rows.append({'mode':mode,'result':result,'events':events,'verifier_sequences':seen,'capture_calls':b._capture_hdc.call_count})
  pathlib.Path('effect-raw.json').write_text(json.dumps(rows,indent=2),encoding='utf-8');print('PASS five post-action effect-boundary cases; real retained images, controlled native emitters')

if __name__=="__main__":unittest.main()
