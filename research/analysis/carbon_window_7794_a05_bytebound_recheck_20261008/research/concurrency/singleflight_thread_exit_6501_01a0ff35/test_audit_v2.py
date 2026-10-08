"""Retained-raw review regression controls; imports no runner or mechanism."""
import copy
import json
from pathlib import Path
import unittest
from audit_v2 import verify

HERE = Path(__file__).resolve().parent
RAW = json.loads((HERE/'evidence/raw.json').read_bytes())
FREEZE = (HERE/'FREEZE.json').read_bytes()

def renumber(row):
    for i,event in enumerate(row['events']):
        event['sequence'] = i

def witness(name):
    value = copy.deepcopy(RAW)
    if name in ('outside-wrapper-row0','outside-wrapper-row4'):
        row = value['rows'][0 if name.endswith('0') else 4]
        index = next(i for i,e in enumerate(row['events']) if e['event']=='wrapper_terminal' and e['status']=='completed')
        event = row['events'].pop(index)
        index = next(i for i,e in enumerate(row['events']) if e['event']=='cleanup')
        row['events'].insert(index,event)
    elif name == 'committee-deliver-before-wrapper':
        row = value['rows'][0]
        index = next(i for i,e in enumerate(row['events']) if e['event']=='caller_deliver')
        event = row['events'].pop(index)
        index = next(i for i,e in enumerate(row['events']) if e['event']=='wrapper_terminal' and e['status']=='completed')
        row['events'].insert(index,event)
    elif name == 'committee-submit-before-request':
        row = value['rows'][0]
        index = next(i for i,e in enumerate(row['events']) if e['event']=='producer_submitted')
        row['events'].insert(0,row['events'].pop(index))
    elif name == 'committee-wrong-caller-role':
        row = value['rows'][1]
        for event in row['events']:
            if event['event'] in ('caller_cancelled','caller_deliver','detach') and event['caller'] in ('first','second'):
                event['caller'] = 'second' if event['caller']=='first' else 'first'
    else:
        raise ValueError('unknown review witness')
    renumber(row)
    return value

class AuditV2Tests(unittest.TestCase):
    def test_original_retained_data_passes(self):
        self.assertEqual(verify(RAW,FREEZE)['errors'],[])

    def test_outside_wrapper_row0_refuses(self):
        self.assertTrue(verify(witness('outside-wrapper-row0'),FREEZE)['errors'])

    def test_outside_wrapper_row4_refuses(self):
        self.assertTrue(verify(witness('outside-wrapper-row4'),FREEZE)['errors'])

    def test_delivery_requires_completed_wrapper(self):
        self.assertTrue(verify(witness('committee-deliver-before-wrapper'),FREEZE)['errors'])

    def test_submission_requires_pending_request(self):
        self.assertTrue(verify(witness('committee-submit-before-request'),FREEZE)['errors'])

    def test_each_schedule_requires_named_caller_roles(self):
        self.assertTrue(verify(witness('committee-wrong-caller-role'),FREEZE)['errors'])

    def test_UTC_bounds_join_original_command(self):
        altered = copy.deepcopy(RAW)
        altered['start_utc'] = altered['end_utc']
        altered['end_utc'] = RAW['start_utc']
        self.assertTrue(verify(altered,FREEZE)['errors'])

    def test_platform_joins_original_source_freeze(self):
        altered = copy.deepcopy(RAW)
        altered['platform'] = 'unrecorded platform'
        self.assertTrue(verify(altered,FREEZE)['errors'])

if __name__ == '__main__':
    unittest.main()
