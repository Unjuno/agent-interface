import tempfile
import unittest
import json
from pathlib import Path
from unittest.mock import patch
import run_integrated_efficiency_live_v1 as live

class FailStopTests(unittest.TestCase):
    def test_failed_first_task_stops_before_next_and_finishes_evaluation(self):
        seen=[]
        class Client:
            def __init__(self, root, seed):
                self.runtime=Path(root)/'runtime'; self.ready={'goal':{'tasks':[{'task_id':'task-1'},{'task_id':'task-2'}]}}
            def __enter__(self): self.runtime.mkdir(parents=True); return self
            def __exit__(self,*args): pass
            def finish(self, request_id): seen.append('finish'); return {'success':False,'missing':['task-1','task-2']}
        def failed(client, arm, task, index, cached, workspace, model_root, model_call):
            seen.append(task['task_id'])
            row={'task_id':task['task_id'],'typed_outcome':'failed'}
            return row,None,{'source':{'capture_ns':0}}
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with patch.object(live,'OUT',root), patch.object(live,'RuntimeClient',Client), patch.object(live,'run_task',failed):
                rows, evaluation=live.run_arm('persistent',1,root,model_call=lambda *x: None)
            self.assertEqual(seen,['task-1','finish'])
            self.assertEqual(len(rows),1)
            self.assertFalse(evaluation['success'])
            self.assertTrue((root/'arms/persistent/task-details.json').is_file())

    def test_incomplete_arm_stops_later_arms_and_writes_partial_report(self):
        seen=[]
        def run_arm(arm, seed, workspace):
            seen.append(arm)
            return [{'task_id':'task-1', 'typed_outcome':'failed'}], {'success':False}
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'preregistration.json').write_text(json.dumps({'sources':{},'seed':1}))
            with patch.object(live,'OUT',root), patch.object(live,'ARMS',('plain','persistent')), patch.object(live,'preflight_call',return_value={}), patch.object(live,'run_arm',run_arm):
                with self.assertRaisesRegex(RuntimeError,'incomplete'):
                    live.main()
            self.assertEqual(seen,['plain'])
            report=json.loads((root/'incomplete-report.json').read_text())
            self.assertEqual(report['failed_arm'],'plain')
            self.assertFalse(report['independent_evaluations']['plain']['success'])

    def test_last_task_failure_stops_even_if_effect_oracle_reports_success(self):
        seen=[]
        def run_arm(arm, seed, workspace):
            seen.append(arm)
            rows=[{'task_id':f'task-{i}', 'typed_outcome':'completed'} for i in range(1,6)]
            rows.append({'task_id':'task-6','typed_outcome':'failed'})
            return rows, {'success':True}
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'preregistration.json').write_text(json.dumps({'sources':{},'seed':1}))
            with patch.object(live,'OUT',root), patch.object(live,'ARMS',('plain','persistent')), patch.object(live,'preflight_call',return_value={}), patch.object(live,'run_arm',run_arm):
                with self.assertRaisesRegex(RuntimeError,'incomplete'):
                    live.main()
            self.assertEqual(seen,['plain'])

if __name__=='__main__': unittest.main()
