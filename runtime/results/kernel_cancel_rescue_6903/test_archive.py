import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / 'research/integration/kernel_cancel_composition_57_01a0ff58'


def module(name):
    spec = importlib.util.spec_from_file_location('archive_' + name, PACKAGE / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class ArchiveTests(unittest.TestCase):
    def test_all_manifest_and_frozen_source_hashes(self):
        lines = (PACKAGE / 'SHA256SUMS.txt').read_bytes().splitlines()
        self.assertEqual(len(lines), 96)
        for line in lines:
            digest, name = line.decode().split(None, 1)
            self.assertEqual(hashlib.sha256((PACKAGE / name).read_bytes()).hexdigest(), digest, name)
        frozen = json.loads((PACKAGE / 'FREEZE.json').read_bytes())
        self.assertEqual(len(frozen['files']), 53)
        for name, digest in frozen['files'].items():
            self.assertEqual(hashlib.sha256((PACKAGE / name).read_bytes()).hexdigest(), digest, name)

    def test_complete_raw_oracle_and_receipt_join(self):
        raw = json.loads((PACKAGE / 'run-01/raw.json').read_bytes())
        errors = module('raw_audit').audit(raw)
        actual = {'errors': errors, 'rows': sum(len(a['rows']) for a in raw['arms']),
                  'scope': '96 sequential typed synthetic histories; no live or full-tree merge claim',
                  'status': 'HOLD' if errors else 'PASS_COMPOSITION_SCOPED'}
        self.assertEqual(actual, json.loads((PACKAGE / 'run-01/audit.json').read_bytes()))
        joined = module('receipt_audit').audit()
        self.assertEqual({'errors': joined, 'status': 'HOLD' if joined else 'PASS_FROZEN_SOURCE_CHILD_RAW_JOIN'},
                         json.loads((PACKAGE / 'run-01/receipt-audit.json').read_bytes()))

    def test_all_eight_retained_corruption_controls(self):
        raw = json.loads((PACKAGE / 'run-01/raw.json').read_bytes())
        audit = module('raw_audit').audit
        mutations = [
            ('missing_arm', lambda r: r['arms'].pop()),
            ('duplicate_arm', lambda r: r['arms'][1].update(arm='000')),
            ('source_hash', lambda r: r['arms'][7]['source_sha256'].update(**{'lifecycle.py': '0' * 64})),
            ('uncertainty_removed', lambda r: r['arms'][7]['rows'][1]['outcome'].update(effect_occurred=False)),
            ('bool_int_alias', lambda r: r['arms'][7]['rows'][1]['outcome'].update(effect_occurred=1)),
            ('equality_rejected', lambda r: r['arms'][7]['rows'][2]['events'][1].update(accepted=False)),
            ('duplicate_begin_hidden', lambda r: r['arms'][7]['rows'][9]['events'].pop(1)),
            ('fresh_stop_hidden', lambda r: r['arms'][7]['rows'][11]['events'].pop()),
        ]
        controls = []
        for name, change in mutations:
            value = copy.deepcopy(raw)
            change(value)
            errors = audit(value)
            controls.append({'case': name, 'errors': errors, 'rejected': bool(errors)})
        result = {'ordinary_post_assay': True, 'control_errors': audit(raw),
                  'controls': controls, 'rejected': sum(c['rejected'] for c in controls)}
        self.assertEqual(result, json.loads((PACKAGE / 'run-01/controls.json').read_bytes()))
        self.assertEqual(result['rejected'], 8)
