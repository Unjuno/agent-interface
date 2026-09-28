"""Positive-only guarded presentation contracts; no backend or model required."""
from copy import deepcopy
import unittest
from runtime.cli_v1.guarded_presentation import brief_guarded_report


def normal_report():
    guards=[]
    for index,stage in enumerate(['before_admission','before_focus','before_move','before_press'],1):
        guards.append(dict(stage=stage,observation_sequence=index,eligible=True,status='VALID',
            handle='field',authority='resolution only; ordinary admission remains required',
            reason='exact_region_match',name='field',point=[30,40],observed_box=[18,21,24,38],
            binding_translation=[0,0],local_translation=[0,0],sequence=index,
            valid_until_ns=5000000,patch_sha256='a'*64,reference_kind='session_alias',
            private_registry_id_exposed=False))
    return dict(operation='guarded_input',status='completed',task_success=None,replay_allowed=False,
        result=dict(status='completed',admission='accepted',required_capabilities=['input.keyboard'],
            recovery_required=False,guard_checks=guards,
            execution=dict(started_ns=1,ended_ns=2,emissions=10,program_emissions=10,
                observations=[],releases=[dict(verified=True,keys_down=[],buttons_down=[])],
                waits=[dict(completed=True)],activations=[],completed_ops=list(range(8)))),
        source=dict(sequence=5,observation_id='observation-5'),observation_report={},
        feedback_status='captured',session=dict(error=None,recovery_required=False,review_required=False),
        image_status='image',image=dict(type='image',data='AA==',mimeType='image/png'),
        call_directory='/retained/call',call_id='call-1')


class GuardedPresentationTests(unittest.TestCase):
    def test_only_guard_detail_changes_and_full_retrieval_is_explicit(self):
        full=normal_report();original=deepcopy(full);brief=brief_guarded_report(full)
        self.assertEqual(full,original)
        self.assertEqual(brief['presentation']['returned'],'brief')
        self.assertEqual(brief['image'],full['image'])
        self.assertEqual(brief['presentation']['retrieve'],{'tool':'interface_results',
            'arguments':{'call_id':'call-1','include_image':False,'detail':'full'}})
        restored=deepcopy(brief);restored.pop('presentation');restored['result'].pop('guard_summary')
        restored['result']['guard_checks']=full['result']['guard_checks']
        self.assertEqual(restored,full)

    def test_keyboard_guard_shape_is_supported(self):
        full=normal_report();full['result']['guard_checks']=full['result']['guard_checks'][:2]
        self.assertEqual(brief_guarded_report(full)['presentation']['returned'],'brief')

    def test_critical_or_unknown_evidence_remains_full(self):
        changes=[
            (('status',),'refused'),(('persistence_error',),'disk full'),
            (('image_status',),'missing'),(('feedback_status',),'observation_failed'),
            (('result','status'),'partial'),(('result','recovery_required'),True),
            (('result','execution','error'),'late error'),
            (('result','execution','releases',0,'verified'),False),
            (('result','execution','releases',0,'keys_down'),['CTRL']),
            (('result','execution','releases',0,'buttons_down'),[1]),
            (('result','execution','waits',0,'completed'),False),
            (('result','execution','waits',0,'error'),'late wait'),
            (('result','execution','observations'),[{'image':'extra'}]),
            (('result','guard_checks',0,'status'),'MISSING'),
            (('result','guard_checks',0,'eligible'),False),
            (('result','guard_checks',0,'local_translation'),[1,0]),
            (('result','guard_checks',0,'new_policy'),'unknown'),
            (('session','review_required'),True),
            (('new_outcome',),'unknown'),
        ]
        for path,value in changes:
            with self.subTest(path=path):
                full=normal_report();parent=full
                for key in path[:-1]:parent=parent[key]
                parent[path[-1]]=value
                projected=brief_guarded_report(full)
                self.assertEqual(projected.pop('presentation')['returned'],'full')
                self.assertEqual(projected,full)

    def test_malformed_and_already_projected_reports_are_not_rewritten(self):
        for full in [{}, {'result':None}, {'result':{'execution':None}}, brief_guarded_report(normal_report())]:
            projected=brief_guarded_report(full)
            self.assertEqual(projected['presentation']['returned'],'full')
            for key,value in full.items():
                if key!='presentation':self.assertEqual(projected[key],value)