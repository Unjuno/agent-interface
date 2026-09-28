import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from runtime.cli_v1.public_presentation import brief_public_report
from runtime.cli_v1.receipt_references import expand_receipt

ROOT = Path(__file__).resolve().parents[2]
def fixture():
    reply = json.loads((ROOT / 'runtime/results/paced-brief-intake-01/reply-2.json').read_text())
    return json.loads(next(c['text'] for c in reply['result']['content'] if c['type'] == 'text'))

class PublicBriefTests(unittest.TestCase):
    def test_normal_paced_projection_preserves_decision_fields_and_input(self):
        view = fixture()
        original = copy.deepcopy(view)
        projected = brief_public_report(view)
        self.assertEqual(view, original)
        self.assertEqual(projected['receipt']['schema'], 'agent-interface/receipt-view-paced-brief-v1')
        self.assertNotIn('raw_report', projected['receipt']['source'])
        for key in ('outcome_summary', 'image_reference', 'session'):
            self.assertEqual(projected[key], view[key])
        summary = projected['receipt']['source']['report_projection']['result']['execution']['wait_summary']
        self.assertEqual(summary['count'], 10)
        self.assertEqual(summary['requested_ms_total'], 280)
        self.assertIsNone(summary['update_observed'])
        self.assertEqual(projected['presentation']['retrieve']['arguments']['call_id'], view['call_id'])
        self.assertLess(len(json.dumps(projected)), len(json.dumps(view)))
        with self.assertRaises(ValueError):
            expand_receipt(projected['receipt'])

    def test_abnormal_or_unknown_wait_evidence_remains_full(self):
        for change in ('failure', 'release', 'missing', 'extension', 'negative', 'index',
                       'mapping', 'completed', 'image', 'bool', 'kind', 'update'):
            with self.subTest(change=change):
                view = fixture()
                raw = view['receipt']['source']['raw_report']
                ex = raw['result']['execution']
                if change == 'failure': raw['result']['status'] = 'execution_failed'
                elif change == 'release': ex['releases'][0]['verified'] = False
                elif change == 'missing': ex['waits'].pop()
                elif change == 'extension': ex['waits'][0]['future'] = 'preserve'
                elif change == 'negative': ex['waits'][0]['ended_ns'] = 0
                elif change == 'index': ex['waits'][0]['operation_index'] = 0
                elif change == 'mapping': raw['compilation']['operation_sources'].pop()
                elif change == 'completed': ex['completed_ops'].pop()
                elif change == 'image': view['image_status'] = 'missing'
                elif change == 'bool': ex['waits'][0]['requested_ms'] = True
                elif change == 'kind': ex['waits'][0]['kind'] = 'future'
                elif change == 'update': ex['waits'][0]['update_observed'] = True
                self.assertEqual(brief_public_report(view), view)

class PublicBriefMCPTests(unittest.IsolatedAsyncioTestCase):
    async def test_opt_in_full_retrieval_and_failure_do_not_replay(self):
        from runtime.cli_v1.mcp_server import create_server
        view = fixture()
        raw = view['receipt']['source']['raw_report']
        program = raw['normalization']['source_program']
        args = dict(program=program, current_observation_seq=1, current_binding_revision=1,
                    compact=True, report_refs=True)
        with tempfile.TemporaryDirectory() as td:
            server = create_server({'app': 1}, td)
            with patch('runtime.cli_v1.mcp_server.dispatch', return_value=raw) as dispatch,                  patch('runtime.cli_v1.mcp_server.present_result', side_effect=lambda *a, **k: copy.deepcopy(view)):
                full = json.loads((await server.call_tool('interface_dispatch', args)).content[0].text)
                self.assertEqual(full['receipt']['schema'], 'agent-interface/receipt-view-v3-report-ref')
                brief = json.loads((await server.call_tool('interface_dispatch', dict(args, detail='brief'))).content[0].text)
                self.assertEqual(brief['receipt']['schema'], 'agent-interface/receipt-view-paced-brief-v1')
                call_id = brief['call_id']
                before = Path(td, call_id, 'report.json').read_bytes()
                request = brief['presentation']['retrieve']
                restored = json.loads((await server.call_tool(request['tool'], request['arguments'])).content[0].text)
                self.assertEqual(restored['receipt']['source']['raw_report'], raw)
                self.assertFalse(restored['operation_invoked'])
                self.assertEqual(before, Path(td, call_id, 'report.json').read_bytes())
                self.assertEqual(dispatch.call_count, 2)
                self.assertNotIn('detail', dispatch.call_args.kwargs)
                failed = copy.deepcopy(view)
                failed['outcome_summary']['execution_error'] = 'failed'
                with patch('runtime.cli_v1.mcp_server.present_result', return_value=failed):
                    reply = json.loads((await server.call_tool('interface_results', dict(
                        call_id=call_id, compact=True, report_refs=True, detail='brief'))).content[0].text)
                    self.assertEqual(reply['receipt'], failed['receipt'])
                    self.assertEqual(reply['outcome_summary'], failed['outcome_summary'])
                self.assertEqual(dispatch.call_count, 2)

if __name__ == '__main__':
    unittest.main()
