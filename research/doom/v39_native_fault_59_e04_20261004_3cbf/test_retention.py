"""Delivery checks never rerun the consumed native producer/official auditor."""
from pathlib import Path
import json
import shutil
import tempfile
import unittest
from verify_retention import check_retention


class RetentionControls(unittest.TestCase):
    def test_rejects_same_missing_or_modified_trace_in_both_copies(self):
        for mode in ('missing', 'modified'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / 'root'
                shutil.copytree(Path(__file__).resolve().parent, root)
                for name in ('native', 'export'):
                    path = root / f'raw/{name}/original_fault/native-stdout.jsonl'
                    if mode == 'missing':
                        path.unlink()
                    else:
                        path.write_text('{}\n')
                with self.assertRaisesRegex(ValueError, 'committed native inventory'):
                    check_retention(root)

    def test_rejects_success_alias_and_export_difference(self):
        for mode in ('exit', 'export', 'later', 'summary'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / 'root'
                shutil.copytree(Path(__file__).resolve().parent, root)
                if mode == 'exit':
                    path = root / 'raw/native-container-inspect.json'
                    receipt = json.loads(path.read_text()); receipt[0]['State']['ExitCode'] = 0
                    path.write_text(json.dumps(receipt))
                elif mode == 'export':
                    (root / 'raw/export/extra').write_text('different')
                elif mode == 'later':
                    (root / 'raw/native/candidate_fault').mkdir()
                    (root / 'raw/export/candidate_fault').mkdir()
                else:
                    for name in ('native', 'export'):
                        (root / f'raw/{name}/SUMMARY.json').write_text('{}')
                reason = {'exit': 'failed terminal', 'export': 'export custody',
                          'later': 'later cells', 'summary': 'missing result boundary changed'}[mode]
                with self.assertRaisesRegex(ValueError, reason):
                    check_retention(root)

    def test_preserves_failed_producer_and_auditor_without_science_pass(self):
        result = check_retention(Path(__file__).resolve().parent)
        self.assertEqual(result['disposition'], 'STOP_RESULT_RETENTION_X11_CLOSE')
        self.assertIs(result['scientific_pass'], False)
        self.assertEqual(result['formal_runs'], 1)
        self.assertEqual(result['official_auditor_runs'], 1)
        self.assertEqual(result['later_cells'], 0)
        self.assertEqual(result['producer_reruns'], 0)


if __name__ == '__main__':
    unittest.main()
