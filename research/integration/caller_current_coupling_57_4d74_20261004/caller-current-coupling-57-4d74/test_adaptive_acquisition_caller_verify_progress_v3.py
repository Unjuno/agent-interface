import copy,json,os,unittest
from pathlib import Path
from adaptive_acquisition_caller_v3 import run
ROWS=[]
class ProgressTests(unittest.TestCase):
    def test_unverified_effect_preserves_detached_execute_progress(self):
        for effect in ('failed','unavailable'):
            for journal_fails in (False,True):
                with self.subTest(effect=effect,journal_fails=journal_fails):
                    receipt={'status':'completed'};calls=[];events=[]
                    def execute(payload):calls.append('execute');return receipt
                    def verify(payload):
                        calls.append('verify');receipt['status']='mutated_after_capture'
                        return {'status':effect}
                    def journal(event):
                        events.append(copy.deepcopy(event))
                        if journal_fails and event['event']=='adaptive_route_finished':raise RuntimeError('terminal unavailable')
                    tick=iter(range(100)).__next__
                    result=run({'target':'Save','route':'reuse','coarse_origin':'caller_provided','provided_coarse':None,'cached_target':{'id':'A'},'local_repair_on':[],'repair_on':[],'session_id':'I36'}, {'reuse_revalidate':lambda p:{'status':'revalidated'},'final_revalidate':lambda p:{'status':'revalidated'},'execute':execute,'verify_effect':verify,'journal':journal},clock=tick)
                    ROWS.append({'effect':effect,'journal_fails':journal_fails,'result':copy.deepcopy(result),'calls':calls,'events':events})
                    self.assertEqual(result['execution_progress'],{'status':'completed'})
                    self.assertEqual(result['task_effect'],effect)
                    self.assertEqual(result['delivery'],'confirmed')
                    self.assertEqual(result['outcome'],'CALLER_FAILED' if journal_fails else 'TASK_NOT_VERIFIED')
                    self.assertEqual(result['input_authority'],'consumed_by_recorded_execute_stage')
                    self.assertEqual(calls,['execute','verify'])
                    self.assertEqual(sum(e['event']=='adaptive_route_finished' for e in events),1)
                    self.assertEqual(result['accounting']['attempted_calls'],0)
if __name__=='__main__':
    try:unittest.main()
    finally:
        if os.environ.get('ROWS_OUTPUT'):Path(os.environ['ROWS_OUTPUT']).write_text(json.dumps(ROWS,sort_keys=True,indent=2))
