import copy
import unittest
from audit import trace_errors


class TraceBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.row={'phase':'PUBLISH_DELAY','token':'fresh','writer_pid':17,
            'payload':{'schema':'issue5260-a06-token-v1','token':'fresh','pid':17,'stamp_ns':100},
            'writer':{'stamp_ns':100,'publish_started_ns':100_000_101,
                      'write_finished_ns':100_000_102,'fsync_finished_ns':100_000_103,
                      'replace_started_ns':100_000_104,'replace_finished_ns':100_000_105},
            'reader':{'start_ns':110,'delay_end_ns':111,'first_read_started_ns':100_000_106,
                      'first_read_finished_ns':100_000_107},
            'attempts':[{'start_ns':100_000_106,'end_ns':100_000_107,
                         'status':'READ_OK','sha256':'abc'}],
            'payload_sha256':'abc'}

    def test_valid_publish_delay_trace(self):
        self.assertEqual(trace_errors(self.row,100),[])

    def test_pre_read_delay_is_distinct_but_same_age_failure(self):
        row=copy.deepcopy(self.row);row['phase']='READER_DELAY'
        row['writer'].update(publish_started_ns=101,write_finished_ns=102,
            fsync_finished_ns=103,replace_started_ns=104,replace_finished_ns=105)
        row['reader'].update(delay_end_ns=100_000_111)
        row['reader'].update(first_read_started_ns=100_000_112,first_read_finished_ns=100_000_113)
        row['attempts'][0].update(start_ns=100_000_112,end_ns=100_000_113)
        self.assertEqual(trace_errors(row,100),[])

    def test_typed_identity_clocks_and_hash_controls(self):
        for update in (lambda r:r['payload'].update(pid=18),
                       lambda r:r['writer'].update(stamp_ns=True),
                       lambda r:r['writer'].update(replace_finished_ns=1),
                       lambda r:r['reader'].update(first_read_finished_ns=1),
                       lambda r:r.update(payload_sha256='changed')):
            row=copy.deepcopy(self.row);update(row)
            self.assertTrue(trace_errors(row,100))

    def test_missing_or_short_delayed_phase_rejected(self):
        row=copy.deepcopy(self.row);row['writer']['publish_started_ns']=101
        self.assertTrue(trace_errors(row,100))
        row=copy.deepcopy(self.row);row['attempts']=[]
        self.assertTrue(trace_errors(row,100))


if __name__=='__main__':unittest.main()
