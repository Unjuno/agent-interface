import json, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXP = ROOT / 'experiment.py'
AUD = ROOT / 'audit.py'


class ContractTests(unittest.TestCase):
    def runone(self, scenario):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            plan = root / 'plan.json'
            out = root / 'out'
            plan.write_text(json.dumps({'cases': [{'id': 'x', 'scenario': scenario}]}))
            subprocess.run([sys.executable, str(EXP), str(plan), str(out)], check=True)
            row = json.loads((out / 'x' / 'result.json').read_text())
            audit = json.loads(subprocess.check_output([sys.executable, str(AUD), str(out)], text=True))
            return row, audit

    def test_correct(self):
        row, audit = self.runone('correct')
        self.assertEqual(row['outcome'], 'EFFECT_VERIFIED')
        self.assertTrue(audit['all_pass'])

    def test_clean_compensation(self):
        row, audit = self.runone('wrong_compensated_clean')
        self.assertTrue(row['full_restoration'])
        self.assertEqual(row['outcome'], 'EFFECT_CONTRADICTED_COMPENSATED')
        self.assertTrue(audit['all_pass'])

    def test_collateral_damage_is_partial(self):
        row, audit = self.runone('wrong_compensated_collateral')
        self.assertTrue(row['primary_restored'])
        self.assertFalse(row['collateral_preserved'])
        self.assertFalse(row['full_restoration'])
        self.assertEqual(row['outcome'], 'EFFECT_CONTRADICTED_COMPENSATION_PARTIAL')
        self.assertTrue(audit['all_pass'])

    def test_primary_only_mislabels_collateral_damage(self):
        row, audit = self.runone('wrong_compensated_collateral')
        self.assertEqual(row['primary_only_outcome'], 'COMPENSATED')
        self.assertEqual(audit['primary_only_truthful_count'], 0)

    def test_uncompensated(self):
        row, audit = self.runone('wrong_uncompensated')
        self.assertEqual(row['final_primary'], 'wrong')
        self.assertEqual(row['outcome'], 'EFFECT_CONTRADICTED_UNCOMPENSATED')
        self.assertTrue(audit['all_pass'])

    def test_wrong_effect_history_retained(self):
        row, _ = self.runone('wrong_compensated_collateral')
        self.assertEqual(row['events'][0]['kind'], 'effect')
        self.assertEqual(row['events'][0]['primary'], 'wrong')


if __name__ == '__main__':
    unittest.main()
