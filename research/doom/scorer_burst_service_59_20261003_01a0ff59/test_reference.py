"""Literal controls for the separate abstract scheduling reference."""
import copy
import unittest
import audit


class ReferenceTests(unittest.TestCase):
    def case(self, arm='original', path='polling', sample=0):
        return {'arm': arm, 'path': path, 'sample_cost_ns': sample,
                'command_cost_ns': audit.P, 'length': 2, 'layout': 'one_chunk'}

    def test_literal_bulk_dispatch_trace(self):
        value = audit.reference(self.case())
        self.assertEqual(value['trace'], [
            ['sample', 0, 0, 0, 0], ['command', 'C000', 0, audit.P],
            ['command', 'C001', audit.P, 2 * audit.P],
            ['command', 'FINISH', 2 * audit.P, 2 * audit.P]])
        self.assertEqual(value['max_command_sample_age_ns'], 2 * audit.P)

    def test_literal_one_command_trace(self):
        value = audit.reference(self.case('one_command'))
        self.assertEqual(value['trace'], [
            ['sample', 0, 0, 0, 0], ['command', 'C000', 0, audit.P],
            ['sample', audit.P, audit.P, audit.P, 0],
            ['command', 'C001', audit.P, 2 * audit.P],
            ['sample', 2 * audit.P, 2 * audit.P, 2 * audit.P, 0],
            ['command', 'FINISH', 2 * audit.P, 2 * audit.P]])

    def test_original_stops_only_at_diagnostic_budget(self):
        for path in ('polling', 'stdin'):
            value = audit.reference(self.case(path=path, sample=audit.P))
            self.assertEqual(value['outcome'], 'diagnostic_budget_stop')
            self.assertEqual(len(value['trace']), 64)
            self.assertTrue(all(e[0] == 'sample' for e in value['trace']))

    def test_one_command_reference_covers_both_services(self):
        count = 0
        for case in audit.deck():
            if case['arm'] != 'one_command':
                continue
            value = audit.reference(case)
            self.assertEqual(value['outcome'], 'complete')
            self.assertLessEqual(value['max_command_sample_age_ns'], audit.P + case['sample_cost_ns'])
            count += 1
        self.assertEqual(count, 256)

    def test_trace_numeric_types_are_distinct(self):
        raw = {'schema': 'scorer-burst-service-v1', 'period_simulated_ns': audit.P,
               'sample_budget': 64, 'rows': [audit.reference(c) for c in audit.deck()]}
        self.assertEqual(audit.inspect(raw)['status'], 'PASS_FINITE_SCHEDULING_REFERENCE')
        corrupt = copy.deepcopy(raw)
        corrupt['rows'][0]['ended_simulated_ns'] = 0.0
        self.assertEqual(audit.inspect(corrupt)['status'], 'FAIL_REFERENCE')


if __name__ == '__main__':
    unittest.main()
