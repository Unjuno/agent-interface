"""Inject the otherwise nondeterministic start-boundary interrupt only."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import runner


class StartInterruptControl(unittest.TestCase):
    def test_unstarted_real_thread_preserves_stop_and_reaps_real_child(self):
        with tempfile.TemporaryDirectory() as name:
            output = Path(name) / 'output'
            # Real Thread, child, pipes, cleanup and filesystem; only start
            # boundary raises the scheduled fault. No mocked cleanup outcome.
            with patch.object(runner.threading.Thread, 'start', side_effect=KeyboardInterrupt):
                try:
                    result = runner.run(output)
                except RuntimeError as error:
                    self.fail('cleanup escaped before STOP retention: ' + str(error))
            self.assertEqual(result, 1)
            self.assertEqual({path.name for path in output.iterdir()}, {'baseline_eof.json', 'SUMMARY.json'})
            summary = json.loads((output / 'SUMMARY.json').read_text())
            self.assertEqual(summary['stop_reason'], 'KeyboardInterrupt')
            self.assertEqual(summary['cases'], ['baseline_eof'])
            row = json.loads((output / 'baseline_eof.json').read_text())
            self.assertIs(row['cleanup_child_alive'], False)
            self.assertIs(row['cleanup_reader_alive'], False)
            self.assertEqual(row['cleanup_faults'], [])
