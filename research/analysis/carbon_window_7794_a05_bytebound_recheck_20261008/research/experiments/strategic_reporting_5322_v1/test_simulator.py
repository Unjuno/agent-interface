import copy
import random
import unittest

import audit
import audit_gpu_model_pilot
import gpu_model_pilot
import simulator


class ConstructionTests(unittest.TestCase):
    def setUp(self):
        self.rows = simulator.run(seeds=(901337,), n_tasks=2)

    def test_paired_matrix_and_independent_audit(self):
        self.assertEqual(len(self.rows), 280)
        self.assertEqual(audit.audit_rows(self.rows, expected_seeds=(901337,), n_tasks=2), [])

    def test_deterministic_replay(self):
        self.assertEqual(self.rows, simulator.run(seeds=(901337,), n_tasks=2))

    def test_corruption_controls(self):
        mutations = (
            lambda x: x.pop(),
            lambda x: x[0].__setitem__('truth', 1-x[0]['truth']),
            lambda x: x[0]['reports'][0].__setitem__('p', .123),
            lambda x: x[0]['reports'][1].__setitem__('declared_domain', 'forged'),
            lambda x: x[0].__setitem__('audited', [0,0,0]),
        )
        for mutation in mutations:
            rows = copy.deepcopy(self.rows)
            mutation(rows)
            self.assertTrue(audit.audit_rows(rows, expected_seeds=(901337,), n_tasks=2))

    def test_gpu_prompt_and_label_seed_parity(self):
        for arm in gpu_model_pilot.ARMS:
            self.assertEqual(gpu_model_pilot.prompt_for(arm), audit_gpu_model_pilot.expected_prompt(arm))
        rng = random.Random(748219963)
        truths = [int(rng.random() < q) for q in gpu_model_pilot.Q_VALUES]
        self.assertEqual(truths, audit_gpu_model_pilot.expected_truths())


if __name__ == '__main__':
    unittest.main()
