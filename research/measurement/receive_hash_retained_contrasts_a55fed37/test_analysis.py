"""Construction and corruption tests; never starts an experiment or GUI."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import contrast
import reconstruct
import check_result

HERE = Path(__file__).resolve().parent

class TableTests(unittest.TestCase):
    def setUp(self):
        self.rows = contrast.load_table(HERE / 'cases.csv')

    def test_known_totals_and_hold(self):
        out = contrast.analyze(self.rows)
        self.assertEqual((out['captures'], out['received'], out['case_count'], out['cue_violations']), (9115, 8675, 32, 1))
        self.assertEqual(out['empirical_decision'], 'HOLD_CUE_INTEGRITY')
        self.assertEqual(out['cases_excluded'], 0)

    def test_missing_case(self):
        with self.assertRaises(ValueError): contrast.analyze(self.rows[:-1])

    def test_duplicate_case(self):
        self.rows[-1] = self.rows[0]
        with self.assertRaises(ValueError): contrast.analyze(self.rows)

    def test_boolean_count(self):
        self.rows[0]['samples'] = True
        with self.assertRaises(ValueError): contrast.analyze(self.rows)

    def test_completion_exceeds_delivery(self):
        self.rows[0]['fresh_completions'] = self.rows[0]['received'] + 1
        with self.assertRaises(ValueError): contrast.analyze(self.rows)

    def test_wrong_factor_binding(self):
        self.rows[0]['mode'] = 'batch_whole'
        with self.assertRaises(ValueError): contrast.analyze(self.rows)

    def test_zero_age(self):
        self.rows[0]['median_age_twice_ns'] = 0
        with self.assertRaises(ValueError): contrast.analyze(self.rows)

    def test_csv_byte_change(self):
        with tempfile.TemporaryDirectory() as td:
            file = Path(td) / 'changed.csv'
            file.write_bytes((HERE / 'cases.csv').read_bytes() + b'\n')
            with self.assertRaises(ValueError): contrast.load_table(file)

    def test_independent_matrix_check(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / 'result.json'
            out.write_text(json.dumps(contrast.analyze(self.rows)))
            checked = check_result.check(HERE / 'cases.csv', out)
            self.assertEqual(checked['errors'], [])
            self.assertEqual(checked['numeric_comparisons'], 224)

    def test_result_corruptions(self):
        baseline = contrast.analyze(self.rows)
        def bad_value(r): r['strata']['busy']['contrasts']['combined']['completion_coverage_delta_pp']['per_block'][0] += 1
        def bad_median(r): r['strata']['busy']['contrasts']['batch_at_whole']['median_age_ratio_candidate_over_reference']['median'] += 1
        def bad_interaction(r): r['strata']['idle']['coverage_interaction_pp']['max'] += 1
        def false_pass(r): r['empirical_decision'] = 'PASS'
        def bad_denominator(r): r['strata']['busy']['cells']['single_whole']['samples'] = True
        def false_current(r): r['strata']['busy']['cells']['batch_chunked']['current_delivery_cues'] += 1
        mutations = [bad_value, bad_median, bad_interaction, false_pass, bad_denominator, false_current]
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / 'result.json'
            for mutate in mutations:
                with self.subTest(mutation=mutate.__name__):
                    changed = copy.deepcopy(baseline)
                    mutate(changed)
                    out.write_text(json.dumps(changed))
                    self.assertTrue(check_result.check(HERE / 'cases.csv', out)['errors'])

class PacketTests(unittest.TestCase):
    def build_packet(self, **changes):
        pixels = b'\x10\x10\x10\x00' * 1024
        obj = dict(case_id='construction', seq=1, capture_start_ns=10,
                   capture_end_ns=20, python_return_ns=30, serialize_start_ns=40,
                   pixel_sha256=hashlib.sha256(pixels).hexdigest())
        obj.update(changes)
        header = json.dumps(obj, sort_keys=True).encode()
        return len(header).to_bytes(4, 'big') + header + pixels

    def test_valid_clear(self):
        self.assertEqual(reconstruct.packet(self.build_packet())[1], 0)

    def test_changed_pixel(self):
        value = bytearray(self.build_packet()); value[-1] ^= 1
        with self.assertRaises(ValueError): reconstruct.packet(bytes(value))

    def test_packet_boolean(self):
        with self.assertRaises(ValueError): reconstruct.packet(self.build_packet(seq=True))

    def test_packet_truncated(self):
        with self.assertRaises(ValueError): reconstruct.packet(self.build_packet()[:-1])

    def test_reversed_clock(self):
        with self.assertRaises(ValueError): reconstruct.packet(self.build_packet(capture_start_ns=21))

    def test_archive_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'bad.zip'; path.write_bytes(b'not original')
            with self.assertRaises(ValueError): reconstruct.reconstruct(path)

if __name__ == '__main__':
    unittest.main(verbosity=2)
