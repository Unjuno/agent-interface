import copy
import unittest
from policy import classify


class PolicyTests(unittest.TestCase):
    def setUp(self):
        identity = dict(epoch='epoch', actuation='action', keycode=74, pid=10, recipient_pid=11, window=12)
        bits = [0]*32
        bits[9] = 4
        first = dict(epoch='epoch', actuation='action', keycode=74, pid=10, kind='sample',
                     request_id='down', seq=2, query_start_ns=100, query_end_ns=110, key_down=True, keymap=bits)
        second = dict(first, seq=4, request_id='post', query_start_ns=200, query_end_ns=220, key_down=False, keymap=[0]*32)
        self.req = dict(identity=identity, before=first, after=second, app_events=[])

    def test_released(self):
        out=classify(self.req)
        self.assertEqual(out['server'],'SERVER_RELEASE_OBSERVED')
        self.assertEqual(out['release_interval_ns'],[100,220])

    def test_held(self):
        self.req['after']['key_down']=True
        self.req['after']['keymap']=self.req['before']['keymap'][:]
        self.assertEqual(classify(self.req)['server'],'STILL_DOWN')

    def test_missing(self):
        for field in ('before','after'):
            r=copy.deepcopy(self.req);r[field]=None
            self.assertEqual(classify(r)['server'],'UNKNOWN')

    def test_foreign(self):
        for field in ('epoch','actuation','pid','keycode'):
            r=copy.deepcopy(self.req);r['after'][field]='foreign'
            self.assertEqual(classify(r)['server'],'UNKNOWN')

    def test_bad_time(self):
        for start,end in ((221,220),(99,220),(True,220)):
            r=copy.deepcopy(self.req);r['after'].update(query_start_ns=start,query_end_ns=end)
            self.assertEqual(classify(r)['server'],'UNKNOWN')

    def test_duplicate_sequence(self):
        self.req['after']['seq']=2
        self.assertEqual(classify(self.req)['server'],'UNKNOWN')

    def test_contradiction(self):
        self.req['after']['key_down']=True
        self.assertEqual(classify(self.req)['server'],'UNKNOWN')

    def test_non_authority(self):
        out=classify(self.req)
        self.assertEqual(out['authority'],'none')
        self.assertIsNone(out['task_success'])
        self.assertEqual(out['app'],'UNKNOWN')

    def test_app_identity(self):
        e=dict(self.req['identity'],pid=11,event_type=2,event_keycode=74,time_ns=120)
        self.req['app_events']=[e,dict(e,event_type=3,time_ns=180)]
        self.assertEqual(classify(self.req)['app'],'APP_RELEASE_OBSERVED')
        self.req['app_events'][1]['pid']=20
        self.assertEqual(classify(self.req)['app'],'UNKNOWN')

    def test_malformed_bitmap(self):
        for bitmap in ([],[0]*31,['0']*32,[False]*32):
            r=copy.deepcopy(self.req);r['after']['keymap']=bitmap
            self.assertEqual(classify(r)['server'],'UNKNOWN')


if __name__ == '__main__':
    unittest.main()
