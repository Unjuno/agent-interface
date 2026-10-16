"""Failed model attempts keep terminal bookkeeping when optional metadata is invalid."""
import copy, pathlib, runpy, subprocess, sys, tempfile, unittest
from unittest.mock import patch
import adaptive_acquisition_caller_v3 as caller
ROWS = []
CASES = {
    'absent': {}, 'valid': dict(call_id='E05-call', usage={'input_tokens':7}, visible_images_submitted=1, wait_ns=20),
    'usage-list': dict(usage=[]), 'usage-negative': dict(usage={'input_tokens':-1}),
    'wait-negative': dict(wait_ns=-1), 'images-bool': dict(visible_images_submitted=True),
    'usage-empty': dict(usage={}),
}
BAD = {'usage-list','usage-negative','wait-negative','images-bool'}
def cell(name):
    counts = dict(model=0, execute=0, verify=0, terminal=0)
    events = []; tick = 0
    def clock():
        nonlocal tick
        tick += 1
        return tick*10
    def journal(event):
        events.append(copy.deepcopy(event))
        if event['event']=='adaptive_route_finished': counts['terminal'] += 1
    def model(_):
        counts['model'] += 1
        raise caller.ModelFailure('E05 upstream declined', typed_status='DEFERRED_UPSTREAM', **CASES[name])
    def execute(_): counts['execute'] += 1; return {'status':'completed'}
    def verify(_): counts['verify'] += 1; return {'status':'succeeded'}
    spec = dict(target='E05 inert target',route='cold',coarse_origin='model_produced',provided_coarse=None,cached_target=None,local_repair_on=[],repair_on=[],session_id='E05-local')
    result = caller.run(spec,dict(observe_source=lambda _:dict(id='own-source'),coarse_model=model,execute=execute,verify_effect=verify,journal=journal),clock=clock,id_factory=lambda:'E05-attempt')
    row=dict(cell=name,metadata=CASES[name],counts=counts,events=events,result=result,escaped=None)
    ROWS.append(row)
    return row
class FailedAttemptMetadata(unittest.TestCase):
    def test_failed_attempt_is_finalized_before_optional_metadata_validation(self):
        for name in CASES:
            with self.subTest(case=name):
                row=cell(name);r=row['result'];a=r['attempt_ledger'][0]
                self.assertEqual(row['counts'],dict(model=1,execute=0,verify=0,terminal=1))
                self.assertEqual(r['outcome'],'CALLER_FAILED' if name in BAD else 'TASK_DEFERRED')
                self.assertEqual(r['input_authority'],'none');self.assertIsNone(r['delivery'])
                self.assertEqual((a['status'],a['started_ns'],a['completed_ns']),('failed',30,40))
                self.assertEqual(a['error'],"ModelFailure('E05 upstream declined')")
                self.assertEqual(r['stages']['coarse_model'],dict(status='failed',reason=a['error']))
                self.assertEqual(r['phase_timings'][-1],dict(stage='coarse_model',started_ns=30,ended_ns=40,elapsed_ns=10))
                self.assertEqual([x for x in row['events'] if x['event']=='model_attempt_finished'],[dict(event='model_attempt_finished',**copy.deepcopy(a))])
                self.assertEqual(r['accounting']['attempted_calls'],1);self.assertEqual(r['accounting']['completed_calls'],0)
                if name in BAD:
                    self.assertIsNone(a['usage']);self.assertIsNone(a['wait_ns']);self.assertIsNone(a['visible_images_submitted'])
    def test_cli_selects_failed_attempt_guard_once(self):
        source=pathlib.Path(__file__).resolve().parents[2]/'runtime/integration_checks/native.py'
        calls=[]
        class Captured(BaseException): pass
        def capture(argv,**kwargs): calls.append(argv);raise Captured()
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(sys,'argv',[str(source),'--output',str(pathlib.Path(directory)/'fresh')]),patch.object(subprocess,'run',capture):
                with self.assertRaises(Captured):runpy.run_path(str(source),run_name='__main__')
        self.assertEqual(len(calls),1)
        self.assertEqual(calls[0].count('test_adaptive_acquisition_failure_metadata_93c2'),1)
if __name__=='__main__': unittest.main()
