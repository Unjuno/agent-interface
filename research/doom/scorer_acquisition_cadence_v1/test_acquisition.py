import copy, unittest
from acquisition import acquire, validate_receipt, FinalAcquirer

class Tests(unittest.TestCase):
    def receipt(self):
        return dict(scheduled_ns=10,sample_started_ns=12,sample_finished_ns=20,
                    start_lateness_ns=2,missed_periods_before=0,payload={'sample_ns':16})
    def test_valid(self): validate_receipt(self.receipt())
    def test_before(self):
        r=self.receipt();r['payload']['sample_ns']=11
        with self.assertRaises(ValueError):validate_receipt(r)
    def test_after(self):
        r=self.receipt();r['payload']['sample_ns']=21
        with self.assertRaises(ValueError):validate_receipt(r)
    def test_inverted(self):
        r=self.receipt();r['sample_finished_ns']=9
        with self.assertRaises(ValueError):validate_receipt(r)
    def test_bool_clock(self):
        r=self.receipt();r['sample_started_ns']=True
        with self.assertRaises(ValueError):validate_receipt(r)
    def test_float_clock(self):
        r=self.receipt();r['payload']['sample_ns']=16.0
        with self.assertRaises(ValueError):validate_receipt(r)
    def test_negative(self):
        r=self.receipt();r['scheduled_ns']=-1
        with self.assertRaises(ValueError):validate_receipt(r)
    def test_wrong_lateness(self):
        r=self.receipt();r['start_lateness_ns']=1
        with self.assertRaises(ValueError):validate_receipt(r)
    def test_missing_field(self):
        r=self.receipt();del r['sample_finished_ns']
        with self.assertRaises(KeyError):validate_receipt(r)
    def test_bad_payload(self):
        r=self.receipt();r['payload']=[]
        with self.assertRaises(TypeError):validate_receipt(r)
    def test_boundaries(self):
        for t in (12,20):
            r=self.receipt();r['payload']['sample_ns']=t;validate_receipt(r)
    def test_bad_missed(self):
        r=self.receipt();r['missed_periods_before']=False
        with self.assertRaises(ValueError):validate_receipt(r)
    def test_capture_once(self):
        ticks=iter([100,105,120]);calls=[]
        def sample():calls.append(1);return {'sample_ns':next(ticks)}
        r=acquire(sample,lambda:next(ticks));self.assertEqual(len(calls),1)
        self.assertEqual((r['sample_started_ns'],r['sample_finished_ns']),(100,120))
    def test_final_once(self):
        ticks=iter([100,200]);saved=[];f=FinalAcquirer(lambda:{'sample_ns':150},saved.append,lambda:next(ticks))
        f();self.assertEqual(len(saved),1);self.assertTrue(saved[0]['direct_final_sample'])
        with self.assertRaises(RuntimeError):f()
    def test_failure_not_persisted_or_retried(self):
        saved=[];ticks=iter([100,200]);f=FinalAcquirer(lambda:{'sample_ns':99},saved.append,lambda:next(ticks))
        with self.assertRaises(ValueError):f()
        self.assertEqual(saved,[])
        with self.assertRaises(RuntimeError):f()
    def test_exception_not_persisted(self):
        def bad():raise OSError('provider failed')
        saved=[];f=FinalAcquirer(bad,saved.append,lambda:100)
        with self.assertRaises(OSError):f()
        self.assertEqual(saved,[])
    def test_old_direct_counterexample(self):
        r=dict(scheduled_ns=200,sample_started_ns=200,sample_finished_ns=200,
               start_lateness_ns=0,missed_periods_before=0,payload={'sample_ns':150})
        with self.assertRaises(ValueError):validate_receipt(r)
    def test_exhaustive_order(self):
        for s in range(4):
            for v in range(4):
                for e in range(4):
                    r=dict(scheduled_ns=0,sample_started_ns=s,sample_finished_ns=e,
                           start_lateness_ns=s,missed_periods_before=0,payload={'sample_ns':v})
                    if s<=v<=e:validate_receipt(r)
                    else:
                        with self.assertRaises(ValueError):validate_receipt(r)
if __name__=='__main__':unittest.main()
