"""Audit real saved construction packets, never a mocked GUI/provider."""
import importlib
from copy import deepcopy
import json
from pathlib import Path
import shutil
import tempfile
import unittest


class PairedAuditTests(unittest.TestCase):
    def setUp(self):
        try:
            self.module = importlib.import_module('paired_audit')
        except ImportError as error:
            self.fail('Independent paired method auditor absent: '+str(error))
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)/'saved'
        shutil.copytree(Path(__file__).parent/'paired-construction'/getattr(self,'fixture','c01'),self.root)

    def test_original_construction_custody_and_quality_without_retroactive_freshness_pass(self):
        result = self.module.audit(self.root)
        self.assertEqual(result['cli_calls'],5)
        self.assertEqual(result['usage']['input_tokens'],15)
        self.assertEqual(result['quality']['guard']['EXACT_FILE'],3)
        self.assertEqual(result['quality']['control']['WRONG_FILE'],1)
        self.assertEqual(result['method_disposition'],'METHOD_INCOMPLETE')
        self.assertTrue(any('DECISION_CLOCK' in value for value in result['gaps']))
        self.assertIs(result['formal_allocation'],False)
        self.assertIs(result['provider_performance_claim'],False)

    def test_changed_source_capsule_cannot_pass_method_audit(self):
        path = next((self.root/'source-capsule').rglob('task_guard.py'))
        path.write_bytes(path.read_bytes()+b'\n# construction tamper\n')
        with self.assertRaisesRegex(ValueError,'SOURCE'):
            self.module.audit(self.root)

    def test_original_host_stdout_tamper_is_not_hidden_by_parsed_answer(self):
        path = self.root/'host/pair-001-first/stdout.bin'
        path.write_bytes(path.read_bytes()+b'\n')
        with self.assertRaisesRegex(ValueError,'PROCESS'):
            self.module.audit(self.root)

    def test_completed_seal_tamper_is_rejected_without_repair(self):
        path = self.root/'exchange/pair-001-first/response/payload.bin'
        path.write_bytes(path.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError,'SEALED'):
            self.module.audit(self.root)

    def test_first_answer_replacement_in_pair_summary_is_rejected(self):
        path = self.root/'candidate/pair-001/paired-result.json'
        value = json.loads(path.read_bytes())
        value['first']['reply']['parsed']['answer']['observed_target'] = 'nr'
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError,'FIRST'):
            self.module.audit(self.root)

    def test_app_reply_nonce_swap_cannot_be_accepted_as_current_state(self):
        path = self.root/'candidate/pair-001/guard/app/reply-000002.json'
        value = json.loads(path.read_bytes())
        value['nonce'] = 'wrong-construction-nonce'
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError,'APP_REPLY'):
            self.module.audit(self.root)

    def test_false_empty_release_in_pair_summary_is_rejected(self):
        path = self.root/'candidate/pair-001/guard-result-02.json'
        value = json.loads(path.read_bytes())
        value['result']['native_calls'][0]['report']['result']['execution']['releases'][0]['keys_down'] = ['v']
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError,'GUARD|NATIVE|RELEASE'):
            self.module.audit(self.root)


class CompletePairedAuditTests(unittest.TestCase):
    fixture = 'c02'
    setUp = PairedAuditTests.setUp

    def test_actual_complete_c02_custody_can_pass_finite_method_without_provider_claim(self):
        result = self.module.audit(self.root)
        self.assertEqual(result['method_disposition'],'METHOD_PASS_FINITE_LOCAL')
        self.assertEqual(result['gaps'],[])
        self.assertEqual(result['cli_calls'],5)
        self.assertIs(result['provider_performance_claim'],False)

    def test_partial_final_local_closure_is_not_complete(self):
        path = self.root/'candidate/study-result.json'
        value = json.loads(path.read_bytes())
        value['local_sources'] = value['local_sources'][:1]
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError,'SOURCE_LOCAL_CLOSURE'):
            self.module.audit(self.root)

    def test_removed_actual_backend_import_cannot_satisfy_runtime_source_gate(self):
        path = self.root/'candidate/study-result.json'
        value = json.loads(path.read_bytes())
        value['runtime_imports']=[row for row in value['runtime_imports']
                                  if row['module']!='runtime.backends.x11_v1.backend']
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError,'SOURCE_RUNTIME_ANCHOR'):
            self.module.audit(self.root)

    def test_changed_retained_native_program_is_not_hidden_by_tail_summary(self):
        directory = self.root/'candidate/pair-001/guard/native'
        for path in directory.glob('guarded-session-*/program-guarded-*.json'):
            value = json.loads(path.read_bytes())
            if any(op['op']=='text' for op in value['ops']):
                for op in value['ops']:
                    if op['op']=='text':
                        op['text']='x'
                path.write_text(json.dumps(value))
                break
        else:
            self.fail('Actual retained prefix program fixture missing')
        with self.assertRaisesRegex(ValueError,'NATIVE_PROGRAM'):
            self.module.audit(self.root)

    def rewrite_call(self,call):
        pair = self.root/'candidate/pair-001'
        (pair/'guard/native/call-0001.json').write_text(json.dumps(call))
        record = json.loads((pair/'guard-result-02.json').read_bytes())
        record['result']['native_calls'][0]=call
        (pair/'guard-result-02.json').write_text(json.dumps(record))
        result = json.loads((pair/'paired-result.json').read_bytes())
        result['guard_final']['native_calls'][0]=call
        (pair/'paired-result.json').write_text(json.dumps(result))

    def test_native_decision_boundary_outside_original_callback_is_rejected(self):
        call = json.loads((self.root/'candidate/pair-001/guard/native/call-0001.json').read_bytes())
        call['checks'][0]['boundary_ns']=call['report']['result']['additional_input_checks'][0]['started_ns']-1
        self.rewrite_call(call)
        with self.assertRaisesRegex(ValueError,'NATIVE_CALLBACK_CLOCK'):
            self.module.audit(self.root)

    def test_lowered_native_minimum_cannot_erase_prior_accepted_snapshot(self):
        call = json.loads((self.root/'candidate/pair-001/guard/native/call-0001.json').read_bytes())
        call['checks'][0]['minimum_sequence']=1
        self.rewrite_call(call)
        with self.assertRaisesRegex(ValueError,'SNAPSHOT_HIGH_WATER'):
            self.module.audit(self.root)

    def test_saved_receipt_before_native_save_is_rejected(self):
        path = self.root/'candidate/pair-001/guard/app/app_result.json'
        value = json.loads(path.read_bytes())
        value['saves'][0]['started_ns']=value['started_ns']+1
        value['saves'][0]['completed_ns']=value['started_ns']+2
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError,'NATIVE_SAVE_CLOCK'):
            self.module.audit(self.root)

    def test_focus_prerequisite_must_follow_original_decision(self):
        path = self.root/'candidate/pair-003/focus-prerequisite.json'
        value = json.loads(path.read_bytes())
        value['boundary_ns']=1
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError,'GUARD_FOCUS_PREREQUISITE_JOIN|SNAPSHOT_CLOCK'):
            self.module.audit(self.root)

    def test_focus_prerequisite_semantics_are_reconstructed_from_current_snapshot(self):
        path = self.root/'candidate/pair-003/focus-prerequisite.json'
        value = json.loads(path.read_bytes())
        value['semantic_consistent']=False
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError,'GUARD_FOCUS_PREREQUISITE_RECONSTRUCTION'):
            self.module.audit(self.root)

    def test_expired_lease_cannot_authorize_execution_start(self):
        program=next((self.root/'candidate/pair-001/guard/native').glob(
            'guarded-session-*/program-guarded-*.json'))
        value=json.loads(program.read_bytes())
        call=json.loads((self.root/'candidate/pair-001/guard/native/call-0001.json').read_bytes())
        value['authority']['expires_at_ns']=call['report']['result']['execution']['started_ns']-1
        program.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError,'NATIVE_PROGRAM_TASK_AFTER_LEASE_EXPIRY'):
            self.module.audit(self.root)

    def test_refusal_result_cannot_be_relabelled_as_success(self):
        path=self.root/'candidate/pair-002/guard-result-01.json'
        value=json.loads(path.read_bytes())
        self.assertEqual(value['review']['decision'],'REFUSE')
        value['result']['status']='SAVE_DISPATCHED'
        path.write_text(json.dumps(value))
        pair=self.root/'candidate/pair-002/paired-result.json'
        summary=json.loads(pair.read_bytes())
        summary['guard_first']['status']='SAVE_DISPATCHED'
        summary['guard_final']['status']='SAVE_DISPATCHED'
        pair.write_text(json.dumps(summary))
        with self.assertRaisesRegex(ValueError,'GUARD_YIELD_RESULT_RECONSTRUCTION'):
            self.module.audit(self.root)

    def test_direct_save_result_cannot_be_relabelled_as_yield(self):
        path=self.root/'candidate/pair-000/guard-result-01.json'
        value=json.loads(path.read_bytes())
        self.assertEqual(value['plan']['status'],'PLAN_SAVE')
        value['result']['status']='YIELD'
        value['result']['reason']='invented refusal'
        path.write_text(json.dumps(value))
        pair=self.root/'candidate/pair-000/paired-result.json'
        summary=json.loads(pair.read_bytes())
        summary['guard_first']=value['result']
        summary['guard_final']=value['result']
        pair.write_text(json.dumps(summary))
        with self.assertRaisesRegex(ValueError,'GUARD_DIRECT_SAVE_OUTCOME'):
            self.module.audit(self.root)

    def test_native_outer_status_must_match_retained_result_status(self):
        record_path=self.root/'candidate/pair-000/guard-result-01.json'
        record=json.loads(record_path.read_bytes())
        record['result']['native_calls'][0]['report']['status']='refused'
        call_path=self.root/'candidate/pair-000/guard/native/call-0001.json'
        call_path.write_text(json.dumps(record['result']['native_calls'][0]))
        record_path.write_text(json.dumps(record))
        pair_path=self.root/'candidate/pair-000/paired-result.json'
        pair=json.loads(pair_path.read_bytes())
        pair['guard_first']=record['result']
        pair['guard_final']=record['result']
        pair_path.write_text(json.dumps(pair))
        with self.assertRaisesRegex(ValueError,'NATIVE_OUTER_STATUS_JOIN'):
            self.module.audit(self.root)

    def test_prefix_plan_cannot_omit_its_required_input_attempt(self):
        record_path=self.root/'candidate/pair-001/guard-result-02.json'
        record=json.loads(record_path.read_bytes())
        self.assertEqual(record['plan']['status'],'PLAN_PREFIX')
        record['result']['native_calls']=[]
        record_path.write_text(json.dumps(record))
        pair_path=self.root/'candidate/pair-001/paired-result.json'
        pair=json.loads(pair_path.read_bytes())
        pair['guard_final']=record['result']
        pair_path.write_text(json.dumps(pair))
        with self.assertRaisesRegex(ValueError,'GUARD_PREFIX_REQUIRED_OPERATION'):
            self.module.audit(self.root)

    def test_control_save_requires_completed_prefix(self):
        answer=json.loads((self.root/'candidate/pair-001/guard-result-02.json').read_bytes())['review']
        self.assertEqual(answer['decision'],'INSERT_PREFIX')
        source=json.loads((self.root/'candidate/pair-001/guard-result-02.json').read_bytes())['result']['native_calls']
        control=dict(native_calls=deepcopy(source))
        self.assertEqual(len(control['native_calls']),2)
        prefix=control['native_calls'][0]['report']
        prefix['status']='partial'
        prefix['result']['status']='partial'
        with self.assertRaisesRegex(ValueError,'CONTROL_PREFIX_BEFORE_SAVE_COMPLETION'):
            self.module.control_prefix_transition(control,answer)


if __name__ == '__main__':
    unittest.main()
