"""Actual caller/core with retained workbook and independent checkpoint (offline)."""
import hashlib, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from research.live_control import integrated_efficiency_compiled_execution_v2 as composition
from research.live_control.calc_checkpoint_effect_v1 import score_checkpoint
from research.live_control.test_compiled_caller_handoff_v2 import cell

class CheckpointCallerTests(unittest.TestCase):
 def test_closed_open_and_unbound_evidence_at_outer_effect_boundary(self):
  directory=Path(__file__).parent
  raw=(directory/'results'/'calc-table-live-01'/'runtime'/'sheet.xlsx').read_bytes()
  self.assertEqual(hashlib.sha256(raw).hexdigest(),'a22e7c71ae8be39aa3114a175f1ed0f2d2ea418d413eff27ecef9e344abb40c5')
  with tempfile.TemporaryDirectory() as tmp, patch.object(sys,'path',[str(directory)]+sys.path):
   from effect_checkpoint_v2 import archived_sample
   from saved_effect import inspect_saved_cells
   root=Path(tmp);source=root/'source.xlsx';source.write_bytes(raw);archive=root/'archive'
   initial=archived_sample(source,{'kind':'saved_cells','expected':{'A1':816,'A2':345}},archive)
   artifact=archive/(initial['artifact_sha256']+'.bin')
   original_core=composition.run_compiled; original_caller=composition.run_caller
   for scenario,outcome in [('closed','TASK_SUCCEEDED'),('open','TASK_NOT_VERIFIED'),('wrong_task','TASK_NOT_VERIFIED'),('before_terminal','TASK_NOT_VERIFIED'),('before_source','TASK_NOT_VERIFIED')]:
    with self.subTest(scenario=scenario):
     terminal=[]
     def core(interface,adapters):
      result=original_core(interface,adapters)
      times=[e['execution_accepted_ns'] for e in result['critical_events'] if e['event']=='action_terminal']
      terminal.append(max(times));return result
     def caller(spec,adapters,**kw):
      adapters=dict(adapters)
      def verify(_):
       source_evidence = initial if scenario == 'before_source' else archived_sample(source,{'kind':'saved_cells','expected':{'A1':816,'A2':345}},archive)
       evidence=inspect_saved_cells(artifact,action_id='inert',expected={'A1':816,'A2':345},observation_closed=scenario!='open')
       evidence['task_id']='other' if scenario=='wrong_task' else 'task-1'
       evidence['source_sampled_ns']=source_evidence['source_sampled_ns']
       evidence['archive_started_ns']=source_evidence['archive_started_ns']
       if scenario=='before_terminal':evidence['sampled_ns']=terminal[0]-1
       return score_checkpoint(archive_dir=archive,evidence=evidence,task_id='task-1',terminal_ns=terminal[0],sheet_name='Sheet',expected_values=(816,345))
      adapters['verify_effect']=verify
      return original_caller(spec,adapters,**kw)
     with patch.object(composition,'run_compiled',side_effect=core),patch.object(composition,'run_caller',side_effect=caller):row=cell()
     self.assertEqual(row['result']['outcome'],outcome)
     self.assertEqual(row['result']['compiled_execution_receipt']['completed_transitions'],2)
     self.assertEqual(row['result']['task_effect'],'succeeded' if scenario=='closed' else 'unavailable')