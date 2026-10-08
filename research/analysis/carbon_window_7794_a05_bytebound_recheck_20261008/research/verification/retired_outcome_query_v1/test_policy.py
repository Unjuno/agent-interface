import copy
import unittest
from policy import classify

Q={'session':'s','resource':'r','epoch':7,'op_id':'a','delta':1}
P={'request':Q,'scope':{'session':'s','resource':'r'},'coverage_epoch':7,'receipt':None,
   'authority':'none','input_dispatched':False}
class PolicyTests(unittest.TestCase):
    def test_current_absent(self):
        for arm in ('LOOKUP_ONLY','COVERAGE_AWARE'):
            self.assertEqual(classify(P,Q,arm)['status'],'NOT_FOUND_CURRENT')
    def test_retired_absent(self):
        p=copy.deepcopy(P);p['coverage_epoch']=8
        self.assertEqual(classify(p,Q,'COVERAGE_AWARE')['status'],'OUTCOME_UNKNOWN_RETIRED')
        self.assertTrue(classify(p,Q,'LOOKUP_ONLY')['submit'])
    def test_retained(self):
        p=copy.deepcopy(P);p['receipt']={'request':Q,'status':'COMPLETED'}
        self.assertEqual(classify(p,Q,'COVERAGE_AWARE')['status'],'COMPLETED')
    def test_retained_conflict(self):
        p=copy.deepcopy(P);p['receipt']={'request':dict(Q,delta=2),'status':'COMPLETED'}
        self.assertEqual(classify(p,Q,'COVERAGE_AWARE')['status'],'CONFLICT_CONTENT')
    def test_invalid_requests(self):
        for key,value in [('epoch',True),('epoch',0),('delta',True),('delta',-1),('op_id',''),('session',None)]:
            with self.subTest(key=key,value=value):
                q=dict(Q);q[key]=value
                self.assertFalse(classify(P,q,'COVERAGE_AWARE')['submit'])
    def test_future_epoch(self):
        q=dict(Q,epoch=8);p=copy.deepcopy(P);p['request']=q
        self.assertEqual(classify(p,q,'COVERAGE_AWARE')['status'],'REFUSE_FUTURE_EPOCH')
    def test_bad_packet(self):
        for k,v in [('coverage_epoch',True),('authority','input'),('input_dispatched',0),('request',dict(Q,delta=2))]:
            with self.subTest(k=k):
                p=copy.deepcopy(P);p[k]=v
                self.assertEqual(classify(p,Q,'COVERAGE_AWARE')['status'],'REFUSE_PACKET')
    def test_wrong_scope(self):
        p=copy.deepcopy(P);p['scope']['resource']='wrong'
        self.assertEqual(classify(p,Q,'COVERAGE_AWARE')['status'],'REFUSE_SCOPE')
    def test_bad_receipt(self):
        for rec in [True,{'status':'COMPLETED'}, {'request':dict(Q,epoch=True),'status':'COMPLETED'},
                    {'request':Q,'status':'RUNNING'}]:
            p=copy.deepcopy(P);p['receipt']=rec
            self.assertEqual(classify(p,Q,'COVERAGE_AWARE')['status'],'REFUSE_RECEIPT')
    def test_no_mutation(self):
        p=copy.deepcopy(P);q=copy.deepcopy(Q);classify(p,q,'COVERAGE_AWARE')
        self.assertEqual(p,P);self.assertEqual(q,Q)
if __name__=='__main__': unittest.main()
