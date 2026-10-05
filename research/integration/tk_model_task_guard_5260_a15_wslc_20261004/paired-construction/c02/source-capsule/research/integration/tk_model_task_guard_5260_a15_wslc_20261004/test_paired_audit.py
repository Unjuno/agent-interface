"""Audit real saved construction packets, never a mocked GUI/provider."""
import importlib
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
        shutil.copytree(Path(__file__).parent/'paired-construction/c01',self.root)

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


if __name__ == '__main__':
    unittest.main()
