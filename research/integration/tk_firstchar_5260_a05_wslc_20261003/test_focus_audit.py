import copy
import unittest
from audit import focus_receipt_errors, focus_drift_before_key


class IndependentFocusAuditTests(unittest.TestCase):
    def setUp(self):
        ack={'schema':'issue5260-a05-focus-ack-v1','token':'new:row-0',
             'pid':17,'target_id':42,'widget':'target','focus_get':'target',
             'event_ns':220,'written_ns':230,'sequence':3}
        self.row={'mode':'ACK_TARGET','token':'new:row-0','app_pid':17,
            'ready':{'ready_ns':100,'geometry':{'target_id':42}},
            'app':{'focus_ack':ack,'events':[
                {'kind':'FocusIn','widget':'target','monotonic_ns':220,'sequence':3},
                {'kind':'KeyPress','widget':'target','monotonic_ns':270,'char':'h'}]},
            'injection':{'click_started_ns':200,'click_sync_returned_ns':210,
                'gate':{'status':'ADMITTED','ack':ack,
                    'state':{k:ack[k] for k in ('token','pid','target_id','widget','sequence','event_ns')},
                    'poll_started_ns':211,'seen_ns':240,'decided_ns':245},
                'key_requests':[{'request_started_ns':260}],
                'save_requests':[{}]}}
        self.fixture={'ack_timeout_ms':500,'max_ack_age_ms':50}

    def test_valid_independent_clock_and_event_binding(self):
        self.assertEqual(focus_receipt_errors(self.row,self.fixture),[])
        self.assertFalse(focus_drift_before_key(self.row))

    def test_unchanged_app_copy_cannot_cover_substituted_receipt(self):
        for field,value in [('pid',18),('token','old'),('target_id',43),
                            ('event_ns',199),('written_ns',241),('sequence',True)]:
            row=copy.deepcopy(self.row)
            row['injection']['gate']['ack'][field]=value
            self.assertTrue(focus_receipt_errors(row,self.fixture))

    def test_missing_real_focus_event_rejected(self):
        row=copy.deepcopy(self.row);row['app']['events']=[]
        self.assertTrue(focus_receipt_errors(row,self.fixture))

    def test_focus_out_race_is_scored_not_silently_promoted(self):
        row=copy.deepcopy(self.row)
        row['app']['events'].insert(1,{'kind':'FocusOut','widget':'target',
            'monotonic_ns':250,'sequence':4})
        self.assertTrue(focus_drift_before_key(row))

    def test_wrong_target_must_refuse_keys_and_save(self):
        row=copy.deepcopy(self.row);row['mode']='ACK_WRONG_TARGET'
        self.assertTrue(focus_receipt_errors(row,self.fixture))
        row['injection']['gate']={'status':'REFUSED_NO_FOCUS_ACK','ack':None,
            'state':None,'poll_started_ns':211,'decided_ns':500_000_212,'seen_ns':None}
        row['injection']['key_requests']=[]
        row['injection']['save_requests']=[]
        row['app']['events']=[]
        self.assertEqual(focus_receipt_errors(row,self.fixture),[])


if __name__=='__main__':unittest.main()
