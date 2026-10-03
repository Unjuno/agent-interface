"""Exact JSON types and trace identity must survive independent raw auditing."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

PACKAGE = Path(__file__).parent
SPEC = importlib.util.spec_from_file_location('sequence_raw_audit_v2', PACKAGE / 'audit_v2.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
BASELINE_SHA = 'a20c7ef88ca3c103a8b2bcea4056e8e714bb4baa41474a4d4bac6c937d3110c7'


class TypedRawAuditTests(unittest.TestCase):
    def setUp(self):
        self.raw = json.loads((PACKAGE / 'after.json').read_text())

    def test_original_evidence_outcomes_are_preserved(self):
        self.assertEqual(MODULE.audit(self.raw)['errors'], [])
        before = json.loads((PACKAGE / 'before.json').read_text())
        self.assertEqual(len(MODULE.audit(before, BASELINE_SHA)['errors']), 11)

    def test_numeric_aliases_never_substitute_for_integer_fields(self):
        for index, original in enumerate(self.raw['rows']):
            paths = [('observation_sequence',)]
            paths += [('calls', field) for field in ('observe', 'execute', 'verify_effect')]
            if original['result'] is not None:
                paths.append(('result', 'completed_transitions'))
            for path in paths:
                value = original
                for field in path:
                    value = value[field]
                aliases = [float(value)]
                if value in (0, 1):
                    aliases.append(bool(value))
                for alias in aliases:
                    with self.subTest(case=original['case_id'], path=path, alias=repr(alias)):
                        raw = copy.deepcopy(self.raw)
                        parent = raw['rows'][index]
                        for field in path[:-1]:
                            parent = parent[field]
                        parent[path[-1]] = alias
                        self.assertTrue(MODULE.audit(raw)['errors'])

    def test_input_label_type_representation_and_source_are_bound(self):
        for field, value in [('admission_type', 'float'), ('admission_repr', 'not-the-input'),
                             ('admission_label', 'true'), ('profile', 'expired')]:
            with self.subTest(field=field):
                raw = copy.deepcopy(self.raw)
                raw['rows'][0][field] = value
                self.assertTrue(MODULE.audit(raw)['errors'])
        for field, value in [('format', 'different'), ('scope', 'live physical input'),
                             ('module_sha256', BASELINE_SHA), ('python', 3), ('platform', None)]:
            with self.subTest(field=field):
                raw = copy.deepcopy(self.raw)
                raw[field] = value
                self.assertTrue(MODULE.audit(raw)['errors'])

    def test_critical_event_type_and_order_corruptions_are_rejected(self):
        index = next(i for i, row in enumerate(self.raw['rows']) if row['case_id'] == '1:equal_int:valid')
        for mutation in ('release_alias', 'transition_alias', 'reverse', 'missing', 'extra'):
            with self.subTest(mutation=mutation):
                raw = copy.deepcopy(self.raw)
                events = raw['rows'][index]['critical_events']
                if mutation == 'release_alias':
                    events[0]['release_verified'] = 1
                elif mutation == 'transition_alias':
                    events[-1]['completed_transitions'] = 1.0
                elif mutation == 'reverse':
                    events.reverse()
                elif mutation == 'missing':
                    events.pop()
                else:
                    events.append(copy.deepcopy(events[0]))
                self.assertTrue(MODULE.audit(raw)['errors'])

    def test_malformed_and_incomplete_shapes_fail_closed(self):
        for mutation in ('null_raw', 'null_rows', 'null_row', 'missing_key', 'extra_key', 'unknown_id', 'duplicate'):
            with self.subTest(mutation=mutation):
                raw = copy.deepcopy(self.raw)
                if mutation == 'null_raw':
                    raw = None
                elif mutation == 'null_rows':
                    raw['rows'] = None
                elif mutation == 'null_row':
                    raw['rows'][0] = None
                elif mutation == 'missing_key':
                    del raw['rows'][0]['calls']
                elif mutation == 'extra_key':
                    raw['rows'][0]['extra'] = False
                elif mutation == 'unknown_id':
                    raw['rows'][0]['case_id'] = 'unexpected'
                else:
                    raw['rows'][1] = copy.deepcopy(raw['rows'][0])
                self.assertTrue(MODULE.audit(raw)['errors'])


if __name__ == '__main__':
    unittest.main()
