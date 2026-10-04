import copy
import json
import unittest
from audit import expected_rows, worker_errors, input_errors


class RawAuditTests(unittest.TestCase):
    def setUp(self):
        self.fixture={'seed':52607026,'replicates_per_cell':2,'payload':'hxy',
            'inter_key_gap_ms':20,'save_delay_after_last_key_ms':250,
            'busy_worker_duration_ms':2200}
        g={'target_root_x':10,'target_root_y':20,'target_width':100,'target_height':20,
           'save_root_x':10,'save_root_y':70,'save_width':80,'save_height':20}
        keys=[{'index':i,'char':char,'keycode':40+i,'request_started_ns':200+i*20_000_001,
               'sync_returned_ns':201+i*20_000_001} for i,char in enumerate('hxy')]
        save_start=keys[-1]['sync_returned_ns']+250_000_000
        self.row={'load':'cpu_busy','ready':{'geometry':g},
            'injection':{'click_widget':'target','x':60,'y':30,'click_started_ns':100,
              'click_sync_returned_ns':150,'gate':{'status':'ADMITTED','ack':None,'state':None,
                   'decided_ns':160,'mode':'NO_ACK_CONTROL'},'key_requests':keys,
              'save_requests':[{'x':50,'y':80,'request_started_ns':save_start,
                                'sync_returned_ns':save_start+1}]},
            'app':{'ended_ns':save_start+100,'events':[]},
            'worker':{'pid':18,'exit':0,'stderr':'','start_ns':50,'end_ns':2_200_000_050,
              'stdout':json.dumps({'start_ns':50,'end_ns':2_200_000_050})}}

    def test_independent_schedule_has_eight_unique_balanced_rows(self):
        rows=expected_rows(self.fixture)
        self.assertEqual(len(rows),8)
        self.assertEqual(len({tuple(sorted(row.items())) for row in rows}),8)
        self.assertEqual(sum(r['instrumentation_mode']=='SYNC_FILE' for r in rows),4)
        self.assertEqual(sum(r['load']=='cpu_busy' for r in rows),4)

    def test_valid_worker_covers_measured_input_phase(self):
        self.assertEqual(worker_errors(self.row,self.fixture),[])

    def test_nonoverlap_zero_length_bool_and_short_worker_rejected(self):
        for start,end in ((1,99),(201,2_200_000_201),(100,100),(True,2_200_000_050),(50,200)):
            row=copy.deepcopy(self.row)
            row['worker'].update(start_ns=start,end_ns=end,
                stdout=json.dumps({'start_ns':start,'end_ns':end}))
            self.assertTrue(worker_errors(row,self.fixture),(start,end))

    def test_idle_worker_and_stdout_binding(self):
        row=copy.deepcopy(self.row);row['load']='idle'
        self.assertTrue(worker_errors(row,self.fixture))
        row['worker']={'pid':None,'exit':None}
        self.assertEqual(worker_errors(row,self.fixture),[])
        row=copy.deepcopy(self.row);row['worker']['stdout']='{}'
        self.assertTrue(worker_errors(row,self.fixture))

    def test_literal_immediate_input_receipts_accept(self):
        self.assertEqual(input_errors(self.row,self.fixture),[])

    def test_ack_wait_replay_bool_key_and_early_save_rejected(self):
        for mutate in (lambda r:r['injection']['gate'].update(mode='ACK_WAIT'),
                       lambda r:r['injection']['key_requests'].append(r['injection']['key_requests'][0]),
                       lambda r:r['injection']['key_requests'][0].update(request_started_ns=True),
                       lambda r:r['injection']['save_requests'][0].update(request_started_ns=300)):
            row=copy.deepcopy(self.row);mutate(row)
            self.assertTrue(input_errors(row,self.fixture))


if __name__=='__main__':unittest.main()
