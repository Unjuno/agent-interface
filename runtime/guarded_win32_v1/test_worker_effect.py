import time,json,pathlib
import runtime.guarded_win32_v1.test_late_state as fixtures
from runtime.guarded_win32_v1.worker_effect import PixelEffect
import unittest

class WorkerEffectCases(unittest.TestCase):
 def test_integration_variants(self):
  rows=[]
  for mode in ['matches','differs','expired','invalid_condition']:
   b,o,s,raw,e=fixtures.Cases('test_exact_expiry_consumes_without_capture').fixture();p=s.prepare('button',[1,1]);base=b.pointer_move
   def move(*args):base(*args);b._capture_hdc.return_value=bytes([255,0,0,0])*64
   b.pointer_move=move;deadline=time.monotonic_ns()+2000000000
   conditions=[{'point':[0,0],'rgb':[0,0,255] if mode!='differs' else [255,0,0]}]
   if mode=='invalid_condition':conditions[0]['point']=[100,0]
   effect=PixelEffect(conditions,time.monotonic_ns()-1 if mode=='expired' else deadline)
   result=s.execute(p['authorization'],verify_effect=effect,effect_deadline_ns=deadline)
   expected=True if mode=='matches' else False if mode=='differs' else None
   assert result['status']=='completed' and result['task_success'] is expected and e==[['move','fixture',3,3],['release']]
   assert s.execute(p['authorization'])['error']=='AUTHORIZATION_CONSUMED_OR_UNKNOWN'
   receipt=dict(effect.receipt)
   for stream in ['stdout','stderr']:
    if stream in receipt:receipt[stream]=receipt[stream].decode(errors='replace')
   rows.append({'mode':mode,'task_success':result['task_success'],'effect':result['effect'],'worker':receipt,'events':e})
  pathlib.Path('worker-effect-raw.json').write_text(json.dumps(rows,indent=2),encoding='utf-8');print('PASS four real child-worker/retained effect cases; no native inputs')

if __name__=="__main__":unittest.main()
