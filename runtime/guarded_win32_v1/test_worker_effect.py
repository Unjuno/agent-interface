import time,json,pathlib
import runtime.guarded_win32_v1.test_late_state as fixtures
from runtime.guarded_win32_v1.worker_effect import PixelEffect
import unittest
import os
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path
from runtime.distribution_v2.build import build

class WorkerEffectCases(unittest.TestCase):
 def test_packaged_archive_worker_resolves_module_outside_source_checkout(self):
  root=Path(__file__).resolve().parents[2]
  with tempfile.TemporaryDirectory() as td:
   temp=Path(td);archive=temp/'runtime.pyz'
   source=temp/'source';source.mkdir();shutil.copytree(root/'runtime',source/'runtime')
   build(source,archive,temp/'manifest.json',temp/'sha256')
   code='''import json,sys,time
sys.path.insert(0,sys.argv[1])
from PIL import Image
from runtime.guarded_win32_v1.worker_effect import PixelEffect
row={"session_scope":"scope","sequence":1,"binding_revision":2,"native":{"artifact":{"sha256":"abc"}}}
effect=PixelEffect([{"point":[0,0],"rgb":[1,2,3]}],time.monotonic_ns()+5000000000)
result=effect({},None,row,Image.new("RGB",(1,1),(1,2,3)))
print(json.dumps({"result":result,"receipt":effect.receipt},default=lambda value:value.decode(errors="replace") if isinstance(value,bytes) else str(value)))'''
   env=os.environ.copy();env.pop('PYTHONPATH',None)
   proc=subprocess.run([sys.executable,'-c',code,str(archive)],cwd=temp,capture_output=True,text=True,timeout=10,env=env)
   self.assertEqual(proc.returncode,0,proc.stderr)
   result=json.loads(proc.stdout)
   self.assertIs(result['result'],True,result)
   self.assertEqual(result['receipt']['status'],'returned',result)

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
