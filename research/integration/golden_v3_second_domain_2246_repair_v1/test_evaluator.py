import unittest
from evaluator import evaluate

def done(effect=True, cleanup=True):
    return {'adapter_result': {'status':'completed','dispatch_terminal':True,'release':{'released':True,'cleanup_ok':cleanup}}, 'independent_effect': {'saved':True,'text':'gtk2492'} if effect else {'saved':False}}

class EvaluatorTests(unittest.TestCase):
    def test_positive_and_negative_gates(self):
        cases=[{'kind':'normal',**done()}, {'kind':'stale','adapter_result':{'status':'refused','raw_dispatch':{'result':{'error':'STALE_OBSERVATION'}}},'attempts':[]}, {'kind':'false_effect',**done(False)}, {'kind':'incomplete_release',**done(True,False)}, {'kind':'ambiguous_refusal','adapter_result':{'status':'refused','raw_dispatch':{'result':{'error':'REFUSED'}}},'attempts':[]}]
        result=evaluate(cases)
        self.assertTrue(result['passed'])
        self.assertEqual([r['accepted'] for r in result['rows']], [True,True,False,False,False])
    def test_stale_with_input_is_rejected(self):
        c={'kind':'stale','adapter_result':{'status':'refused','raw_dispatch':{'result':{'error':'STALE_OBSERVATION'}}},'attempts':[{'consequential_input':True}]}
        self.assertFalse(evaluate([c]*5)['passed'])
    def test_unknown_case_is_rejected(self):
        self.assertFalse(evaluate([{'kind':'other'}]*5)['passed'])

if __name__ == '__main__': unittest.main()
