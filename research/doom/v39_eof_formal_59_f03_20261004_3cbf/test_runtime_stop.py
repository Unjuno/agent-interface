"""Real early-exit child: preserve first failure and do not start later cells."""
import json
from pathlib import Path
import tempfile
import unittest
import runner


class RuntimeStopControl(unittest.TestCase):
    def test_real_early_exit_stops_first_cell_and_reaps_child(self):
        original = runner.sys.executable
        with tempfile.TemporaryDirectory() as name:
            output = Path(name) / 'output'
            try:
                # /usr/bin/false exists on both this macOS host and Ubuntu.
                runner.sys.executable = '/usr/bin/false'
                result = runner.run(output)
            finally:
                runner.sys.executable = original
            self.assertEqual(result, 1)
            self.assertEqual({p.name for p in output.iterdir()}, {'baseline_eof.json', 'SUMMARY.json'})
            summary = json.loads((output / 'SUMMARY.json').read_text())
            self.assertEqual(summary['verdict'], 'STOP_FIRST_UNEXPECTED_CELL')
            self.assertEqual(summary['cases'], ['baseline_eof'])
            row = json.loads((output / 'baseline_eof.json').read_text())
            self.assertIs(row['gate'], False)
            self.assertIs(row.get('cleanup_child_alive'), False)
            self.assertIs(row.get('cleanup_reader_alive'), False)
            self.assertEqual(row['cleanup_exit'], 1)
            self.assertEqual(row['cleanup_faults'], [])
            self.assertGreater(row['child_pid'], 0)
