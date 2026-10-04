import copy
import json
from pathlib import Path
import unittest
from sample_custody import sample_errors


def packet():
    return {'mode':'PIPE_ACK_TARGET','pipe':{'reads':[
        {'status':'DATA','started_ns':101,'completed_ns':102},
        {'status':'EAGAIN','started_ns':103,'completed_ns':104},
        {'status':'EAGAIN','started_ns':106,'completed_ns':107},
        {'status':'EOF','started_ns':120,'completed_ns':121}]},
        'injection':{'gate':{'started_ns':100,'decided_ns':108,'samples':[
            {'read_attempts':2,'checked_ns':105}, {'read_attempts':3,'checked_ns':108}]}}}


class SampleTests(unittest.TestCase):
    def test_complete_first_and_last_poll_accept(self):
        self.assertEqual(sample_errors(packet()),[])

    def test_deleted_first_middle_duplicate_or_boolean_poll_refused(self):
        changes=[lambda r:r['injection']['gate']['samples'].pop(0),
            lambda r:r['injection']['gate']['samples'].pop(),
            lambda r:r['injection']['gate']['samples'].append(copy.deepcopy(r['injection']['gate']['samples'][-1])),
            lambda r:r['injection']['gate']['samples'][0].update(read_attempts=True)]
        for index,change in enumerate(changes):
            row=packet();change(row)
            with self.subTest(index=index):self.assertTrue(sample_errors(row))

    def test_original_six_ack_rows_have_no_missing_poll_samples(self):
        root=Path(__file__).resolve().parent
        raw=json.loads((root/'evidence/focus01-candidate-data/candidate_stdout.json').read_bytes())
        rows=[row for row in raw['rows'] if row['mode']!='NOW_TARGET']
        self.assertEqual(len(rows),6)
        for row in rows:self.assertEqual(sample_errors(row),[],row['index'])


if __name__=='__main__':unittest.main()
