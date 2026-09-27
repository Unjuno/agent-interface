"""Small excluded construction checks; no timing-allocation execution."""
import json
import tempfile
import unittest
from audit import expand, expected_view, encoded
from upstream_review.review import review_bytes


class ContractTests(unittest.TestCase):
    def check_report(self, report):
        data = encoded(report)
        with tempfile.TemporaryDirectory() as folder:
            for kw in ({}, {'compact': True}, {'compact': True, 'report_refs': True}):
                out = review_bytes(data, folder, **kw)
                self.assertEqual(encoded(expand(out['receipt'])), encoded(expected_view(data.decode())))
                self.assertEqual(out['authority'], 'none')
        self.assertEqual(data, encoded(report))

    def test_minimal(self):
        self.check_report({'schema': 'agent-interface/runtime-dispatch-result-v1', 'status': 'construction', 'result': {}})

    def test_report_ref(self):
        self.check_report({'schema': 'agent-interface/runtime-dispatch-result-v1', 'status': 'construction', 'note': 'z' * 1024, 'result': {}})

    def test_literal_refs(self):
        self.check_report({'schema': 'agent-interface/runtime-dispatch-result-v1', 'status': 'construction', 'literal': {'event_ref': 0, 'report_ref': '/source/raw_report', 'a~/b': [True, 1]}, 'result': {}})

    def test_critical(self):
        e = {'event': 'unusual_event', 'detail': 'z' * 1024}
        self.check_report({'schema': 'agent-interface/runtime-dispatch-result-v1', 'status': 'construction', 'records': [e], 'repeat': [e, e, e], 'result': {}})

    def test_flags(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                review_bytes(b'{"status":"construction"}', folder, report_refs=True)

    def test_failure_not_erased(self):
        report = {'schema': 'agent-interface/runtime-dispatch-result-v1', 'status': 'runtime_failed', 'result': {'status': 'execution_failed', 'recovery_required': True, 'execution': {'releases': [{'verified': False}, {'verified': True, 'keys_down': [], 'buttons_down': []}]}}}
        with tempfile.TemporaryDirectory() as folder:
            for kw in ({}, {'compact': True}, {'compact': True, 'report_refs': True}):
                out = review_bytes(encoded(report), folder, **kw)
                self.assertIs(out['outcome_summary']['input_release_verified'], False)
                self.assertIs(out['outcome_summary']['recovery_required'], True)


if __name__ == '__main__':
    unittest.main()
