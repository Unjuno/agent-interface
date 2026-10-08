#!/usr/bin/env python3
"""Zero-optimizer construction checks for the frozen width comparison."""
import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch

import torch

import runner
import audit
import formal


class ConstructionTests(unittest.TestCase):
    def test_formal_allocation_uses_only_fresh_exact_seeds(self):
        self.assertEqual(runner.ALLOCATION, "needle-intent-capacity-4679-v2")
        self.assertEqual(runner.SEEDS, (4153201, 4153203, 4153207))
        self.assertEqual(audit.SEEDS, runner.SEEDS)

    def test_seeded_state_generation_is_repeatable(self):
        self.assertTrue(torch.equal(runner.gen_states(32, 4153201), runner.gen_states(32, 4153201)))
        self.assertFalse(torch.equal(runner.gen_states(32, 4153201), runner.gen_states(32, 4153202)))

    def test_train_and_heldout_partitions_are_disjoint(self):
        train = runner.gen_states(128, 4153201)
        heldout = runner.gen_states(64, 4153202)
        self.assertFalse(set(map(tuple, train.tolist())) & set(map(tuple, heldout.tolist())))

    def test_teacher_counterfactuals_use_same_state_and_different_intents(self):
        state = torch.tensor([0.08, 0.0, 0.06, 0.06, 0.90, 1.0])
        labels = [runner.teacher(state, intent) for intent in runner.INTENTS]
        self.assertGreaterEqual(len(set(labels)), 2)

    def test_expansion_dimensions_and_row_order(self):
        states = runner.gen_states(7, 4153201)
        aware_x, y = runner.expand(states, True)
        plain_x, y0 = runner.expand(states, False)
        self.assertEqual(tuple(aware_x.shape), (28, 10))
        self.assertEqual(tuple(plain_x.shape), (28, 6))
        self.assertTrue(torch.equal(y, y0))
        self.assertEqual(y.tolist(), [label for state in states for label in [runner.teacher(state, intent) for intent in runner.INTENTS]])

    def test_widths_and_parameter_counts(self):
        self.assertEqual(runner.parameter_count(10, 24), 964)
        self.assertEqual(runner.parameter_count(10, 64), 5124)
        self.assertEqual(runner.parameter_count(6, 24), 868)
        self.assertEqual(runner.Net(10, 24)(torch.zeros(4, 10)).shape, (4, 4))
        self.assertEqual(runner.Net(10, 64)(torch.zeros(4, 10)).shape, (4, 4))

    def test_independent_auditor_forward_matches_untrained_architecture(self):
        torch.manual_seed(47)
        model = runner.Net(10, 24)
        state = {name: value.detach().tolist() for name, value in model.state_dict().items()}
        states = runner.gen_states(16, 4153201).tolist()
        with torch.no_grad():
            expected = model(runner.expand(torch.tensor(states), True)[0]).argmax(1)
        actual = audit.forward_state(state, 24, 10, states, True).argmax(1)
        self.assertTrue(torch.equal(expected, actual))

    def test_invalid_intents_fail_closed_without_model_call(self):
        for invalid in runner.INVALID_INTENTS:
            result = runner.resolve_intent(invalid)
            self.assertEqual(result, {"decision": "YIELD", "model_calls": 0})

    def test_valid_intents_are_only_accepted_from_exact_vocabulary(self):
        for intent in runner.INTENTS:
            self.assertEqual(runner.resolve_intent(intent)["decision"], "VALID_INTENT")
        self.assertEqual(runner.resolve_intent("Track")["decision"], "YIELD")

    def test_formal_flag_is_explicit_and_construction_does_not_fit(self):
        self.assertEqual(runner.STEPS, 900)
        self.assertEqual(runner.WIDTH_CANDIDATE, 64)
        self.assertEqual(runner.WIDTH_REFERENCE, 24)
        # No call to fit is made in this suite; optimizer-step count is zero.

    def test_host_container_command_uses_verified_tag_and_offline_readonly_limits(self):
        argv = formal.trainer_argv("src", "out")
        self.assertIn("needle-pilot05:local", argv)
        self.assertIn("--pull=never", argv)
        self.assertIn("--network", argv)
        self.assertIn("none", argv)
        self.assertIn("--read-only", argv)
        self.assertIn("--cpus=1", argv)
        self.assertIn("--security-opt=no-new-privileges", argv)

    def test_host_formal_fails_closed_before_docker_without_a_freeze(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source"
            output = Path(temp) / "output"
            source.mkdir()
            (source / "FREEZE.json").write_text(json.dumps({}), encoding="utf-8")
            with patch.object(formal.subprocess, "run") as run:
                with self.assertRaisesRegex(SystemExit, "STOP_FREEZE_ALLOCATION_OR_BRANCH"):
                    formal.run(source, output)
                run.assert_not_called()
            self.assertFalse(output.exists())

    def test_output_mount_accepts_empty_but_refuses_nonempty_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "mounted-output"
            output.mkdir()
            self.assertEqual(runner.prepare_output(output), output)
            sentinel = output / "preserve.txt"
            sentinel.write_text("do not overwrite", encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "STOP_OUTPUT_NOT_EMPTY"):
                runner.prepare_output(output)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "do not overwrite")


if __name__ == "__main__":
    unittest.main(verbosity=2)
