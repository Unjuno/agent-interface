#!/usr/bin/env python3
"""No-allocation constructor tests; does not write candidate or audit outputs."""
import unittest
import run_t0

class ConstructionTests(unittest.TestCase):
    def test_fixed_allocation_and_independent_controls(self):
        self.assertEqual(len(run_t0.CASES),8)
        self.assertEqual(len(run_t0.POLICIES),4)
        self.assertEqual(len(run_t0.CASES)*len(run_t0.POLICIES),32)
        self.assertEqual(len({x['id'] for x in run_t0.CASES}),8)
        self.assertIn('preserve_formula', [c['source_clause'] for c in run_t0.CASES])

    def test_privacy_absence_stale_and_no_answer_fail_closed(self):
        expected={'respondent-absent':'RESPONDENT_ABSENT','privacy-restricted':'PRIVACY_BLOCKED',
                  'no-answer':'NO_ANSWER','stale-question':'STALE_QUESTION'}
        for case in run_t0.CASES:
            if case['id'] in expected:
                self.assertEqual(run_t0.respondent(case,case['scenario'],case['revision'])[0],expected[case['id']])

    def test_source_clause_is_not_new_discovery(self):
        case=next(c for c in run_t0.CASES if c['id']=='explicit-prohibition')
        status,clause=run_t0.respondent(case,case['scenario'],case['revision'])
        self.assertEqual((status,clause),('CONFIRMED_FORBIDDEN','preserve_formula'))
        self.assertEqual(case['source_clause'],clause)

    def test_mismatched_scenario_does_not_create_clause(self):
        case=next(c for c in run_t0.CASES if c['id']=='formula-preserve')
        self.assertEqual(run_t0.respondent(case,'formatting_change',case['revision']),('NO_MATCH',None))

if __name__=='__main__': unittest.main()
