import copy
import json
from pathlib import Path
import unittest
from audit import audit


class SavedBoundaryTests(unittest.TestCase):
    def raw(self):
        return json.loads(Path(__file__).with_name('first-outcome.json').read_text())

    def test_saved_defect_is_not_a_generation_pass(self):
        result = audit(self.raw())
        self.assertFalse(result['generation_contract_satisfied'])
        self.assertEqual(result['stale_admissions'], 2)

    def test_inconsistent_saved_claims_are_rejected(self):
        for change in (
                lambda raw: raw['rows'][1].update(reference_eligible=True),
                lambda raw: raw['rows'][1].update(admission=None),
                lambda raw: raw['rows'][0]['release'].update(verified=False),
                lambda raw: raw['rows'][3].update(error_type=None),
                lambda raw: raw['rows'][2].update(owner_thread_stopped=False),
                lambda raw: raw.update(task_success_verified=True)):
            with self.subTest(change=change):
                raw = copy.deepcopy(self.raw())
                change(raw)
                with self.assertRaises(ValueError):
                    audit(raw)


if __name__ == '__main__':
    unittest.main()
