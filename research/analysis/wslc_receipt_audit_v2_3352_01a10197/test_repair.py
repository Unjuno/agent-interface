"""Focused enforcement and effective raw-corruption regression tests."""
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import audit_v2
from verify_repair import verify

P = Path(__file__).resolve().parent
OLD = P.parent / 'wslc_dockerfile_build_smoke_t0_20261003'


def matrix():
    result = json.loads((P/'matrix.json').read_text())
    result['rows'].append(json.loads((P/'additional_case.json').read_text()))
    return result


class RepairTests(unittest.TestCase):
    def test_saved_rows_and_pins(self):
        self.assertEqual(verify(P, matrix())['v2_negative_rejections'], 17)

    def test_image_joins_independently_of_hash_gate(self):
        # Construction-only: update the private copy's RUN hash, so each semantic
        # join must reject by itself. Production accepts no caller-supplied pins.
        for case, message in [('image_build', 'RUN build image identity mismatch'), ('image_postrun', 'RUN postrun image identity mismatch')]:
            with self.subTest(case=case):
                modified = (P/'cases'/case/'RUN.json').read_bytes()
                pins = dict(audit_v2.EXPECTED_FILES)
                pins['RUN.json'] = (len(modified), hashlib.sha256(modified).hexdigest())
                with patch.object(audit_v2, 'EXPECTED_FILES', pins):
                    with self.assertRaisesRegex(audit_v2.AuditError, message):
                        audit_v2.audit(P/'cases'/case)

    def test_all_seven_hash_guards(self):
        for name in audit_v2.EXPECTED_FILES:
            with self.subTest(name=name):
                kind = 'source_' if name in ('Dockerfile','payload.txt','probe.py') else 'hash_'
                case = 'hash_run.output_inline' if name == 'run.output.txt' else kind + name
                with self.assertRaisesRegex(audit_v2.AuditError, 'frozen source mismatch: ' + name):
                    audit_v2.audit(P/'cases'/case)

    def test_intact_cli_result_shape(self):
        out = audit_v2.audit(OLD)
        self.assertEqual(out['frozen_inputs_checked'], 7)
        self.assertEqual(out['status'], 'PASS_RETAINED_RECEIPT_V2_ENGINEERING')

    def test_raw_checker_rejects_effective_copies(self):
        controls = []
        m = matrix(); m['rows'].pop(); controls.append(m)
        m = matrix(); m['rows'][1]['inputs']['build.output.txt'] = '0'*64; controls.append(m)
        m = matrix(); m['rows'][1]['audits']['v2']['exit_code'] = 0; controls.append(m)
        m = matrix(); m['rows'][0]['audits']['v2']['exit_code'] = False; controls.append(m)
        m = matrix(); m['rows'][1]['audits']['legacy']['stdout'] = '{}'; controls.append(m)
        m = matrix(); m['rows'][0]['audits']['v2']['stdout'] = m['rows'][0]['audits']['v2']['stdout'].replace('"frozen_inputs_checked":7', '"frozen_inputs_checked":3'); controls.append(m)
        for i,m in enumerate(controls):
            with self.subTest(control=i):
                self.assertNotEqual(json.dumps(m, sort_keys=True), json.dumps(matrix(), sort_keys=True))
                with self.assertRaises((ValueError,KeyError)): verify(P,m)


if __name__ == '__main__':
    unittest.main()
