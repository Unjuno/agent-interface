import json
import os
import unittest
import probe

class ProbeTests(unittest.TestCase):
    def test_first_invalid_row_retained_without_next_measurement(self):
        from test_cell import valid,PLAN
        c=valid();r=c['rows'][0];r['requested_ns']=1
        rows,error=probe.collect_rows(c['start_ns'],123,PLAN,lambda *a,**k:r)
        self.assertEqual(len(rows),1);self.assertIsNotNone(error)
    def test_cleanup_failure_preserves_all_children(self):
        class Child:
            pid=1
            returncode=2
            def kill(self):pass
            def communicate(self,timeout=None):return ('','')
        def stopper(child,ready):raise ValueError('injected-cleanup')
        receipts=probe.cleanup_children([(Child(),{}),(Child(),{})],stopper)
        self.assertEqual(len(receipts),2)
        self.assertTrue(all('error' in r for r in receipts))
    def test_absolute_sleep_brackets_actual_return(self):
        clocks=iter([100,110,510])
        cpus=iter([5,7])
        requests=[]
        snaps=iter([{'mark':'before'},{'mark':'after'}])
        r=probe.measure(500,123,lambda:next(snaps),lambda:next(clocks),requests.append,lambda:next(cpus),0)
        self.assertEqual(requests,[390/1e9])
        self.assertEqual((r['requested_ns'],r['return_ns'],r['cpu_start_ns'],r['cpu_end_ns']),(390,510,5,7))
    def test_past_deadline_not_slept(self):
        clocks=iter([600,610,620]);requests=[];cpus=iter([1,2]);snaps=iter([{},{}])
        r=probe.measure(500,123,lambda:next(snaps),lambda:next(clocks),requests.append,lambda:next(cpus),1)
        self.assertEqual(requests,[]);self.assertEqual(r['requested_ns'],0)
    def test_owned_burner_readiness_and_stop(self):
        child,ready=probe.start_child('method-only')
        try:
            self.assertEqual(ready['pid'],child.pid)
            self.assertEqual(ready['ppid'],os.getpid())
            self.assertEqual(ready['case'],'method-only')
        finally:
            receipt=probe.stop_child(child,ready)
        self.assertEqual(receipt['exit_code'],0)
        self.assertEqual(receipt['finish']['reason'],'parent-stop')
        self.assertFalse(receipt['forced'])

if __name__=='__main__':unittest.main()
