import unittest

import candidate


class CandidateConstructionTests(unittest.TestCase):
    def test_formal_seed_schedule_is_frozen_and_not_cli_overridable(self):
        self.assertEqual(candidate.FORMAL_SEEDS, (6539101, 6539102, 6539103))

    def test_training_inputs_and_seed_replay_are_deterministic(self):
        a = candidate.make_train_rows(6539101)
        b = candidate.make_train_rows(6539101)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 256)
        self.assertTrue(all(len(row["x"]) == candidate.N_FEATURES for row in a))

    def test_fitted_arms_retain_equal_rows_and_only_frozen_label_change(self):
        base = candidate.make_train_rows(6539101)
        for arm in candidate.ARMS[1:]:
            rows = candidate.transform_rows(base, arm, 6539101)
            self.assertEqual(len(rows), len(base))
            if arm == "authority_effect_loss":
                for row in rows:
                    if row["x"][8] == 0.0 or row["x"][9] == 0.0:
                        self.assertEqual(row["y"], "YIELD")
            else:
                self.assertEqual([row["y"] for row in rows], [row["y"] for row in base])

    def test_test_split_holds_task_and_marks_family_out(self):
        rows = candidate.make_test(6539101, n_per_cell=2)
        ordinary = [r for r in rows if r["task_id"] < 1000]
        self.assertEqual({r["task_id"] for r in ordinary}, set(range(80, 100)))
        self.assertTrue(all(r["split"] == "test" for r in rows))
        self.assertEqual(sum(r["fault_family"] == "marks" for r in ordinary), 40)

    def test_paired_twins_have_identical_input_and_different_authority_truth(self):
        rows = candidate.make_test(6539101, n_per_cell=1)
        twins = [r for r in rows if r["fault_family"] == "paired_twin"]
        self.assertEqual(len(twins), 2)
        self.assertEqual(twins[0]["x"], twins[1]["x"])
        self.assertNotEqual(twins[0]["authorized"], twins[1]["authorized"])
        self.assertEqual({r["required"] for r in twins}, {"CONTINUE", "YIELD"})

    def test_same_model_replays_same_prediction(self):
        rows = candidate.make_train_rows(6539101)
        model_a = candidate.fit(rows, 6539101, epochs=2)
        model_b = candidate.fit(rows, 6539101, epochs=2)
        self.assertEqual(model_a, model_b)
        self.assertEqual(candidate.predict(model_a, rows[0]["x"]),
                         candidate.predict(model_b, rows[0]["x"]))


if __name__ == "__main__":
    unittest.main()
