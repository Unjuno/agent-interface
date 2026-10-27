import hashlib,tempfile,unittest
from pathlib import Path
from research.live_control.calc_checkpoint_effect_v1 import score_checkpoint

class CheckpointEffectTests(unittest.TestCase):
 def test_closed_matching_post_terminal_archive_can_be_scored(self):
  raw=(Path(__file__).parent/'results'/'calc-table-live-01'/'runtime'/'sheet.xlsx').read_bytes()
  digest=hashlib.sha256(raw).hexdigest()
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/(digest+'.bin')).write_bytes(raw)
   evidence={'status':'VERIFIED','observation_closed':True,'artifact_sha256':digest,'sampled_ns':201,'task_id':'task-1'}
   args=dict(archive_dir=root,evidence=evidence,task_id='task-1',terminal_ns=200,sheet_name='Sheet',expected_values=(816,345))
   self.assertEqual(score_checkpoint(**args)['status'],'succeeded')
   for key,value in [('observation_closed',False),('sampled_ns',199),('task_id','other'),('artifact_sha256','0'*64)]:
    with self.subTest(key=key):
     bad=dict(evidence);bad[key]=value
     self.assertEqual(score_checkpoint(**dict(args,evidence=bad))['status'],'unavailable')
   (root/(digest+'.bin')).write_bytes(b'changed')
   self.assertEqual(score_checkpoint(**args)['status'],'unavailable')
 def test_real_open_checkpoint_is_not_promoted(self):
  import sys,time
  from unittest.mock import patch
  directory=Path(__file__).parent
  raw=(directory/'results'/'calc-table-live-01'/'runtime'/'sheet.xlsx').read_bytes()
  with tempfile.TemporaryDirectory() as tmp, patch.object(sys,'path',[str(directory)]+sys.path):
   from effect_checkpoint_v2 import archived_sample
   from saved_effect import inspect_saved_cells
   root=Path(tmp);source=root/'workbook.xlsx';source.write_bytes(raw);archive=root/'archive';terminal=time.perf_counter_ns()
   evidence=archived_sample(source,{'kind':'saved_cells','expected':{'A1':816,'A2':345}},archive)
   evidence['task_id']='task-1'
   args=dict(archive_dir=archive,evidence=evidence,task_id='task-1',terminal_ns=terminal,sheet_name='Sheet',expected_values=(816,345))
   self.assertEqual(evidence['status'],'VERIFIED');self.assertFalse(evidence['observation_closed'])
   self.assertEqual(score_checkpoint(**args)['status'],'unavailable')
   closed=inspect_saved_cells(archive/(evidence['artifact_sha256']+'.bin'),action_id='inert',expected={'A1':816,'A2':345},observation_closed=True)
   closed['task_id']='task-1'
   self.assertEqual(score_checkpoint(**dict(args,evidence=closed))['status'],'succeeded')