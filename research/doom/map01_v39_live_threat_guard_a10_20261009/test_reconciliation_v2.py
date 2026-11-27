import unittest
from audit_live_reconciliation_v2 import reconcile_cancellation_custody
EMPTY={'event':'owner_release','verified':True,'keys_down':[],'buttons_down':[],'keys_unknown':[]}
def rows():
    owner={**EMPTY,'reason':'cancelled','intent_token':'G'}
    return [{'event':'cancel_requested','id':'guard','matched':True},{'event':'input_released','id':'guard','intent_token':'G','owner_release':owner},{'event':'terminal','id':'guard','status':'cancelled','release':EMPTY,'interruption':{'intent_token':'G','record':owner}},{'event':'cancel_requested','id':'other','matched':True},{'event':'input_admission','id':'other','key':'W','intent_token':'A'},{'event':'terminal','id':'other','status':'cancelled','release':EMPTY,'interruption':{'intent_token':None}}]
def valid_rows():
    result=rows(); owner={**EMPTY,'reason':'cancelled','intent_token':'A'}
    result[-1]['interruption']={'intent_token':'A','record':owner}
    result.append({'event':'input_released','id':'other','intent_token':'A','owner_release':owner})
    return result
class CustodyMutationTests(unittest.TestCase):
    def test_admission_without_token_bound_release_is_unaccounted(self):
        result=reconcile_cancellation_custody(rows(),'guard');self.assertFalse(result['cancel_terminal_releases_empty']);self.assertIn('other',result['unaccounted_cancel_ids'])
    def test_matching_admission_release_is_accounted(self):
        result=reconcile_cancellation_custody(valid_rows(),'guard');self.assertTrue(result['cancel_terminal_releases_empty']);self.assertTrue(result['guard_has_explicit_verified_empty_release'])
    def test_token_mismatch_and_duplicate_releases_fail_closed(self):
        for mutation in ('token','duplicate'):
            events=valid_rows()
            if mutation=='token':events[-1]['intent_token']='wrong'
            else:events.append(dict(events[-1]))
            with self.subTest(mutation=mutation):self.assertIn('other',reconcile_cancellation_custody(events,'guard')['unaccounted_cancel_ids'])
    def test_invalid_identity_is_rejected(self):
        events=valid_rows();events[4]['id']=[]
        with self.assertRaises(ValueError):reconcile_cancellation_custody(events,'guard')
    def test_verified_empty_no_admission_remains_valid(self):
        events=valid_rows();events=[e for e in events if not (e.get('id')=='other' and e['event'] in ('input_admission','input_released'))];events[-1]['interruption']={'intent_token':None}
        self.assertTrue(reconcile_cancellation_custody(events,'guard')['cancel_terminal_releases_empty'])
if __name__=='__main__':unittest.main()
