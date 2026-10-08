"""Data-only regression and corruption controls; no formal GUI/model replay."""
import importlib.util
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from audit import inspect

ROOT = Path(__file__).resolve().parent


def rewrite_manifest(root):
    # Test-only custody corruption helper: do not let a stale outer manifest
    # hide whether independent inner evidence checks actually catch the break.
    entries = sorted(p for p in root.rglob('*') if p.is_file()
                     and p != root / 'SHA256SUMS' and '__pycache__' not in p.parts)
    (root / 'SHA256SUMS').write_text(''.join(
        hashlib.sha256(p.read_bytes()).hexdigest() + '  ' +
        p.relative_to(root).as_posix() + '\n' for p in entries))


class RetainedTests(unittest.TestCase):
    def verifier(self):
        self.assertIsNotNone(importlib.util.find_spec('verify_packet'),
                             'H_FAIL-preserving packet verifier missing')
        from verify_packet import check_packet
        return check_packet

    def test_first_h_fail_cannot_be_promoted_by_packet_success(self):
        result = self.verifier()(ROOT)
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['status'], 'PASS_RETAINED_H_FAIL_ONLY')
        self.assertEqual(result['original_hypothesis'], 'H_FAIL_FINITE_REVIEW_ONLY')
        self.assertEqual(result['exact'], [True, False, True, True])
        self.assertEqual(result['model_requests_retained'], 4)
        self.assertEqual(result['container_gui_model_commands_executed'], 0)
        self.assertEqual(result['usage_column_sums'], {
            'input_tokens': 55132, 'cached_input_tokens': 12032,
            'cache_write_input_tokens': 0, 'output_tokens': 253,
            'reasoning_output_tokens': 118})

    def test_retention_header_is_not_an_unchecked_label(self):
        check = self.verifier()
        for key in ('source_commit', 'allocation'):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / 'packet'; shutil.copytree(ROOT, root)
                path = root / 'RETENTION.json'; value = json.loads(path.read_bytes())
                value[key] = 'wrong'; path.write_text(json.dumps(value))
                rewrite_manifest(root)
                self.assertIn('retention_header', check(root)['errors'])

    def test_coordinated_artifact_and_manifest_edit_cannot_replace_original(self):
        check = self.verifier()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'packet'; shutil.copytree(ROOT, root)
            name = 'review01-candidate-data/row-000/cache/fontconfig/CACHEDIR.TAG'
            path = root / 'retained' / name
            path.write_bytes(path.read_bytes() + b'not original\n')
            retention_path = root / 'RETENTION.json'
            retention = json.loads(retention_path.read_bytes())
            retention['original_files_sha256'][name] = hashlib.sha256(path.read_bytes()).hexdigest()
            retention_path.write_text(json.dumps(retention))
            rewrite_manifest(root)
            self.assertIn('retention_hash', check(root)['errors'])

    def test_delivery_process_joins_catch_binding_argv_and_parallel_calls(self):
        self.verifier()
        import verify_packet
        self.assertTrue(hasattr(verify_packet, 'delivery_join_errors'),
                        'independent delivery process joins missing')
        from verify_packet import delivery_join_errors
        self.assertEqual(delivery_join_errors(ROOT), [])
        controls = [
            ('review01-candidate-launch/attempt.json', 'binding', None, 'candidate:attempt_binding'),
            ('review01-model-launch/attempt.json', 'binding', None, 'model:attempt_binding'),
            ('review01-auditor-launch/attempt.json', 'binding', None, 'auditor:attempt_binding'),
            ('review01-candidate-data/candidate_stdout.json', 'app_argv', 2, 'app_argv'),
            ('review01-model-data/row-001/receipt.json', 'started_utc', None, 'serial_model_order')]
        for name, field, index, error in controls:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / 'packet'; shutil.copytree(ROOT, root)
                path = root / 'retained' / name; value = json.loads(path.read_bytes())
                if field == 'binding':
                    value['binding']['source_commit'] = 'wrong'
                elif field == 'app_argv':
                    value['rows'][index]['app_argv'][2] = '/experiment/foreign.py'
                else:
                    previous = json.loads((root / 'retained/review01-model-data/row-000/receipt.json').read_bytes())
                    value['started_utc'] = previous['started_utc']
                path.write_text(json.dumps(value))
                self.assertIn(error, delivery_join_errors(root))

    def test_missing_original_stream_is_rejected(self):
        check = self.verifier()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'packet'; shutil.copytree(ROOT, root)
            (root / 'retained/review01-model-data/row-003/stderr.bin').unlink()
            rewrite_manifest(root)
            self.assertIn('original_evidence_bytes', check(root)['errors'])

    def test_promoted_first_hypothesis_is_rejected_even_with_new_outer_hashes(self):
        check = self.verifier()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'packet'; shutil.copytree(ROOT, root)
            path = root / 'retained/review01-auditor-launch/stdout.bin'
            value = json.loads(path.read_bytes()); value['hypothesis'] = 'H_PASS_FINITE_REVIEW_ONLY'
            path.write_text(json.dumps(value)); rewrite_manifest(root)
            self.assertIn('first_h_fail_changed', check(root)['errors'])

    def test_model_answer_cannot_grant_input_authority(self):
        check = self.verifier()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'packet'; shutil.copytree(ROOT, root)
            path = root / 'retained/review01-model-data/model_result.json'
            value = json.loads(path.read_bytes()); value['rows'][1]['authority_granted'] = True
            path.write_text(json.dumps(value)); rewrite_manifest(root)
            self.assertIn('first_h_fail_changed', check(root)['errors'])

    def test_all_four_app_clocks_are_independently_traversed(self):
        for index in range(4):
            with self.subTest(index=index), tempfile.TemporaryDirectory() as temporary:
                retained = Path(temporary) / 'retained'; shutil.copytree(ROOT / 'retained', retained)
                path = retained / 'review01-candidate-data/candidate_stdout.json'
                value = json.loads(path.read_bytes())
                value['rows'][index]['click']['completed_ns'] = 0
                path.write_text(json.dumps(value))
                result = inspect(retained, ROOT)
                self.assertEqual(result['status'], 'STOP_AUDIT')
                self.assertIn('app_clock', result['errors'])

    def test_unsafe_duplicate_and_incomplete_manifest_rejected(self):
        self.verifier()
        from verify_packet import manifest_errors
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); path = root / 'proof'; path.write_bytes(b'proof')
            digest = hashlib.sha256(b'proof').hexdigest()
            good = digest + '  proof'
            self.assertEqual(manifest_errors(root, [good]), [])
            self.assertIn('duplicate_manifest', manifest_errors(root, [good, good]))
            self.assertIn('incomplete_manifest', manifest_errors(root, []))
            for name in ('../proof', '/proof', 'C:/proof', 'a\\proof', 'SHA256SUMS'):
                with self.subTest(name=name):
                    self.assertIn('unsafe_manifest', manifest_errors(root, [digest + '  ' + name]))

    def test_nested_file_named_sha256sums_is_not_exempt_from_coverage(self):
        self.verifier()
        from verify_packet import manifest_errors
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); (root / 'nested').mkdir()
            (root / 'nested/SHA256SUMS').write_bytes(b'unlisted data')
            self.assertIn('incomplete_manifest', manifest_errors(root, []))

    def test_required_three_and_each_known_optional_field_in_both_parsers(self):
        from model_contract import parse
        from audit import model_value
        rows = [json.loads(line) for line in
                (ROOT / 'retained/review01-model-data/row-000/stdout.bin').read_bytes().splitlines()]
        for optional in ({}, {'cache_write_input_tokens': 0},
                         {'reasoning_output_tokens': 2},
                         {'cache_write_input_tokens': 0, 'reasoning_output_tokens': 2}):
            usage = {'input_tokens': 30, 'cached_input_tokens': 10, 'output_tokens': 4, **optional}
            changed = json.loads(json.dumps(rows))
            changed[-1]['usage'] = usage
            for parser in (parse, model_value):
                with self.subTest(optional=optional, parser=parser.__name__):
                    self.assertEqual(parser(changed)['usage'], usage)


if __name__ == '__main__':
    unittest.main()
