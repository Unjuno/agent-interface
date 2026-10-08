import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from runtime.cli_v1.receipt import receipt_view


class ReceiptTests(unittest.TestCase):
    def view(self, report, **kwargs):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "report.json"
            path.write_text(json.dumps(report), encoding="utf-8")
            original = path.read_bytes()
            value = receipt_view(str(path), **kwargs)
            self.assertEqual(path.read_bytes(), original)
            return value

    def test_latest_observation_keeps_terminal_and_unknown_events(self):
        rows = [{"event": "observation", "sequence": 1}, {"event": "accepted", "id": "a"},
                {"event": "observation", "sequence": 2}, {"event": "terminal", "status": "failed"},
                {"event": "future_critical_event", "detail": "keep me"}]
        value = self.view({"status": "boundary", "records": rows})
        self.assertEqual(value["latest_observations"], [rows[2]])
        self.assertEqual(value["events"], rows[3:])
        self.assertEqual(value["omitted_from_view"], 2)

    def test_transport_uncertainty_and_extensions_survive(self):
        report = {"status": "transport_or_protocol_error", "error": {"message": "timeout"},
                  "recovery": "no automatic resend", "new_field": {"important": True}}
        self.assertEqual(self.view(report)["report"], report)

    def test_conflicting_equal_sequence_observations_remain_visible(self):
        rows = [{"event": "observation", "sequence": 2, "image": "a.png"},
                {"event": "observation", "sequence": 2, "image": "b.png"}]
        self.assertEqual(self.view({"status": "boundary", "records": rows})["latest_observations"], rows)

    def test_raw_view_is_exact_parsed_report(self):
        report = {"status": "closed", "records": [{"event": "command", "command": {"op": "finish"}}]}
        self.assertEqual(self.view(report, raw=True), report)

    def test_malformed_records_refused(self):
        for records in (None, {}, [None], [{"event": "observation", "sequence": True}]):
            with self.subTest(records=records), self.assertRaises(ValueError):
                self.view({"status": "boundary", "records": records})

    def test_cli_reports_failed_task_and_rejects_bad_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'report.json'
            path.write_text(json.dumps({'status': 'transport_or_protocol_error', 'error': 'timeout'}))
            args = [sys.executable, '-m', 'runtime.cli_v1', 'receipt', '--report', str(path)]
            result = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout)['report']['status'], 'transport_or_protocol_error')
            path.write_text('{bad')
            result = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stdout)['status'], 'invalid_receipt')


if __name__ == "__main__":
    unittest.main()
