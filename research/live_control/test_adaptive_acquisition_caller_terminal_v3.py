import copy
import json
import os
from pathlib import Path
import unittest

import adaptive_acquisition_caller_v3 as caller
ROWS=[]
COMPLETE={'status':'completed'}
UNKNOWN={'status':'safe_yield','reason':'execution_failed','completed_actions':2,'input_dispatched':True}
REFUSED={'status':'safe_yield','reason':'execution_refused','completed_actions':0,'input_dispatched':False}
INVALID={'status':'safe_yield','reason':'cancelled','completed_actions':1,'input_dispatched':False}
FAMILIES=['completed','unknown_mutation','refused_journal','completed_clock','unknown_typed_clock',
          'verify_throws','invalid','execute_throws','pre_stop','effect_unavailable']

def exercise(family,terminal):
    receipt=copy.deepcopy(UNKNOWN if family in {'unknown_mutation','unknown_typed_clock','execute_throws'} else
                          REFUSED if family=='refused_journal' else INVALID if family=='invalid' else COMPLETE)
    state={'execute':0,'verify':0,'terminal':0,'clock':0,'events':[]}
    def clock():
        state['clock']+=1
        if state['clock']==6:
            if family=='completed_clock':raise RuntimeError('I22 execute end clock')
            if family=='unknown_typed_clock':raise caller.ModelFailure('I22 clock deferred',typed_status='DEFERRED_UPSTREAM')
            if family=='unknown_mutation':receipt.clear();receipt.update(COMPLETE)
        return state['clock']
    def journal(event):
        state['events'].append(copy.deepcopy(event))
        if event['event']=='stage_completed' and event.get('stage')=='execute' and family=='refused_journal':
            raise RuntimeError('I22 execute journal')
        if event['event']=='adaptive_route_finished':
            state['terminal']+=1
            if terminal=='persistent' or terminal=='first' and state['terminal']==1:
                raise RuntimeError('I22 final journal')
    def execute(payload):
        state['execute']+=1
        if family=='execute_throws':raise RuntimeError('I22 execute no return')
        return receipt
    def verify(payload):
        state['verify']+=1
        if family=='verify_throws':raise caller.ModelFailure('I22 verifier failed',typed_status='FAILED_OUTPUT')
        return {'status':'unavailable' if family=='effect_unavailable' else 'succeeded'}
    spec={'target':'I22 button','route':'reuse','coarse_origin':'caller_provided','provided_coarse':None,
          'cached_target':{'id':'I22'},'local_repair_on':[],'repair_on':[],'session_id':'I22'}
    result=None;escaped=None
    try:
        result=caller.run(spec,{'reuse_revalidate':lambda p:{'status':'stale' if family=='pre_stop' else 'revalidated'},
                              'final_revalidate':lambda p:{'status':'revalidated'},'execute':execute,
                              'verify_effect':verify,'journal':journal},clock=clock)
    except Exception as error:escaped=repr(error)
    row={'family':family,'terminal_mode':terminal,'result':result,'state':state,'escaped':escaped}
    ROWS.append(copy.deepcopy(row))
    return row

class ComposedTests(unittest.TestCase):
    def test_composed_errors_and_healthy_controls(self):
        for family in FAMILIES:
            for terminal in ['healthy','first','persistent']:
                with self.subTest(family=family,terminal=terminal):
                    row=exercise(family,terminal);r=row['result'];s=row['state']
                    self.assertIsNone(row['escaped'])
                    self.assertIsInstance(r,dict)
                    self.assertEqual(s['terminal'],1)
                    self.assertEqual(s['execute'],int(family!='pre_stop'))
                    self.assertEqual(s['verify'],int(family in {'completed','verify_throws','effect_unavailable'}))
                    base_outcome=('TASK_SUCCEEDED' if family=='completed' else 'EXECUTION_INCOMPLETE' if family=='unknown_mutation' else
                                  'SAFE_STOP' if family=='pre_stop' else 'TASK_NOT_VERIFIED' if family=='effect_unavailable' else 'CALLER_FAILED')
                    self.assertEqual(r['outcome'],base_outcome if terminal=='healthy' else 'CALLER_FAILED')
                    delivery=('confirmed' if family in {'completed','completed_clock','verify_throws','effect_unavailable'} else
                              'delivery_uncertain' if family in {'unknown_mutation','unknown_typed_clock'} else
                              'not_attempted' if family=='refused_journal' else None)
                    self.assertEqual(r['delivery'],delivery)
                    progress=(COMPLETE if family in {'completed','completed_clock','verify_throws'} else
                              UNKNOWN if family in {'unknown_mutation','unknown_typed_clock'} else
                              REFUSED if family=='refused_journal' else
                              COMPLETE if family=='effect_unavailable' else None)
                    self.assertEqual(r['execution_progress'],progress)
                    effect='succeeded' if family=='completed' else 'unavailable' if family=='effect_unavailable' else None
                    self.assertEqual(r['task_effect'],effect)
                    authority='none' if family in {'refused_journal','execute_throws','pre_stop'} else 'consumed_by_recorded_execute_stage'
                    self.assertEqual(r['input_authority'],authority)
                    self.assertEqual(r['accounting']['attempted_calls'],0)
                    execute_stage=('skipped' if family=='pre_stop' else 'started' if family in {'completed_clock','unknown_typed_clock'} else
                                   'failed' if family=='execute_throws' else 'completed')
                    self.assertEqual(r['stages']['execute']['status'],execute_stage)
                    if terminal!='healthy':
                        self.assertEqual(r['reason'],'terminal_journal_unavailable')
                        self.assertEqual(r['finalized_outcome'],base_outcome)
                        self.assertEqual(r['terminal_journal_error'],"RuntimeError('I22 final journal')")
                        self.assertEqual(r['finalized_reason'],s['events'][-1]['reason'])
                    else:
                        self.assertNotIn('finalized_outcome',r)

if __name__=='__main__':
    try:unittest.main()
    finally:
        if os.environ.get('ROWS_OUTPUT'):
            Path(os.environ['ROWS_OUTPUT']).write_text(json.dumps(ROWS,sort_keys=True,indent=2),encoding='utf-8')
