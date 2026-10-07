import copy
import unittest
from native_brief_review_v1 import brief_native_review
from receipt_references import expand_native_receipt


def fixture():
    action = {'result': {'status':'completed','recovery_required':False,
        'guard_checks':[{'status':'VALID','retained_detail':'x'*1000}],
        'execution':{'observations':[],'completed_ops':[0,1], 'waits':[],
            'releases':[{'verified':True,'keys_down':[],'buttons_down':[]}],
            'program_emissions':2,'unknown_execution':{'keep':True}},
        'unknown_result':{'keep':True}},
        'feedback':{'status':'matched','samples':[{'title':'app'}], 'unknown_feedback':9},
        'window_review':{'status':'reviewed'}, 'unknown_action':'keep'}
    return {'receipt':{'source':{'path':'/receipt','sha256':'a'*64},
        'native_result':{'status':'boundary','stage':2,'decision_sha256':'b'*64,'action':action,
                         'observation':{},'unknown_top':False}},
        'image':{'data':'exact'},'image_status':'image','continuation':{'status':'source_available','stage':3,'source_sequence':7},
        'outcome_summary':{'evaluation_success':None},'unknown_envelope':['keep']}


class BriefReviewTests(unittest.TestCase):
    def test_normal_projection_preserves_decision_fields_unknowns_and_retrieval(self):
        raw=fixture(); before=copy.deepcopy(raw); out=brief_native_review(raw)
        self.assertEqual(raw,before)
        self.assertEqual(out['presentation']['returned'],'brief')
        for key in ('image','continuation','outcome_summary','unknown_envelope'):
            self.assertEqual(out[key],raw[key])
        summary=expand_native_receipt(out['receipt_summary'])['native_result']
        self.assertEqual(summary['action']['result']['execution']['unknown_execution'],{'keep':True})
        self.assertEqual(summary['action']['result']['unknown_result'],{'keep':True})
        self.assertEqual(summary['action']['feedback']['unknown_feedback'],9)
        self.assertEqual(summary['unknown_top'],False)
        self.assertEqual(out['presentation']['retrieve']['arguments'],{
            'stage':2,'decision_sha256':'b'*64,'include_image':False,'detail':'full'})
        self.assertEqual(out['presentation']['omitted_detail_counts']['feedback_samples'],1)

    def test_critical_results_fall_back_to_exact_receipt(self):
        changes=[lambda r:r['action']['result'].update(status='failed'),
                 lambda r:r['action']['result'].update(recovery_required=True),
                 lambda r:r['action']['feedback'].update(status='needs_review',error='BadWindow'),
                 lambda r:r['action']['window_review'].update(status='needs_review'),
                 lambda r:r['action']['result']['execution']['releases'][0].update(verified=False),
                 lambda r:r['observation'].update(review_recovery={'allowed_decisions':['observe','finish']}),
                 lambda r:r.update(target_refusal={'input_dispatched':False}),
                 lambda r:r['action']['result']['execution'].update(observations=[{'error':'capture'}])]
        for change in changes:
            with self.subTest(change=change):
                raw=fixture();change(raw['receipt']['native_result']);out=brief_native_review(raw)
                self.assertEqual(out['presentation']['returned'],'full')
                self.assertEqual(out['receipt'],raw['receipt'])
                self.assertNotIn('receipt_summary',out)

    def test_unrecognized_results_remain_full(self):
        for raw in ({'status':'pending'}, {'receipt':{'native_result':{'status':'finished'}}}):
            out=brief_native_review(raw)
            self.assertEqual(out['presentation']['returned'],'full')
            self.assertEqual({k:v for k,v in out.items() if k!='presentation'},raw)
    def test_small_normal_result_remains_full(self):
        raw = fixture()
        raw['receipt']['native_result']['action']['result']['guard_checks'] = [{'status': 'VALID'}]
        out = brief_native_review(raw)
        self.assertEqual(out['presentation']['reason'], 'not_smaller')
        self.assertEqual(out['receipt'], raw['receipt'])

    def test_broken_reference_keeps_full_evidence(self):
        from receipt_references import NATIVE_REFS
        raw = fixture()
        raw['receipt'].update(schema=NATIVE_REFS, reference_scope='fixture',
            observation_references=['/native_result/action/result/execution/completed_ops/99'])
        out = brief_native_review(raw)
        self.assertEqual(out['presentation']['returned'], 'full')
        self.assertEqual(out['receipt'], raw['receipt'])
