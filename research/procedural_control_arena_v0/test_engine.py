from __future__ import annotations

import json
import unittest

from engine import BenchmarkSession, DifficultyProfile, generate_episode, solve_with_oracle_for_test


class ArenaEngineTest(unittest.TestCase):
    def test_generation_is_seed_deterministic(self):
        a = generate_episode(123456789, 0.42)
        b = generate_episode(123456789, 0.42)
        self.assertEqual(a.canonical_json(), b.canonical_json())
        self.assertEqual(a.public_fingerprint(), b.public_fingerprint())

    def test_fresh_seed_changes_episode(self):
        a = generate_episode(101, 0.42)
        b = generate_episode(102, 0.42)
        self.assertNotEqual(a.canonical_json(), b.canonical_json())

    def test_public_state_does_not_leak_seed_or_oracle_ids(self):
        spec = generate_episode(987654321, 0.5)
        session = BenchmarkSession(spec)
        public = json.dumps(session.public_state(), sort_keys=True)
        self.assertNotIn(str(spec.seed), public)
        for stage in spec.stages:
            for key in ("target_id", "active_id", "prepared_id"):
                if key in stage.payload:
                    self.assertNotIn(str(stage.payload[key]), public)

    def test_difficulty_is_monotone_on_declared_axes(self):
        easy = DifficultyProfile.from_level(0.0)
        hard = DifficultyProfile.from_level(1.0)
        self.assertGreater(easy.target_radius, hard.target_radius)
        self.assertLess(easy.target_speed, hard.target_speed)
        self.assertLess(easy.distractor_count, hard.distractor_count)
        self.assertGreater(easy.target_deadline, hard.target_deadline)
        self.assertGreater(easy.switch_wait, hard.switch_wait)
        self.assertLess(easy.typing_length, hard.typing_length)

    def test_shape_hit_testing_matches_rendered_geometry(self):
        from engine import RuntimeObject
        square = RuntimeObject("x", "blue", "square", 100, 100, 0, 0, 20)
        triangle = RuntimeObject("x", "blue", "triangle", 100, 100, 0, 0, 20)
        diamond = RuntimeObject("x", "blue", "diamond", 100, 100, 0, 0, 20)
        self.assertTrue(BenchmarkSession._contains(square, 119, 119))
        self.assertFalse(BenchmarkSession._contains(triangle, 119, 81))
        self.assertTrue(BenchmarkSession._contains(triangle, 100, 100))
        self.assertTrue(BenchmarkSession._contains(diamond, 110, 110))
        self.assertFalse(BenchmarkSession._contains(diamond, 115, 115))

    def test_oracle_positive_control_passes_many_seeds(self):
        for seed in range(20):
            with self.subTest(seed=seed):
                session = BenchmarkSession(generate_episode(seed, 0.75))
                solve_with_oracle_for_test(session)
                self.assertTrue(session.done)
                self.assertTrue(session.success, session.failure_reason)

    def test_switch_premature_click_fails_closed(self):
        # Search a bounded seed range for a switch-first episode.
        session = None
        for seed in range(1000):
            candidate = BenchmarkSession(generate_episode(seed, 0.5))
            if candidate.stage.kind == "switch":
                session = candidate
                break
        self.assertIsNotNone(session)
        session.click(320, 240)
        self.assertTrue(session.done)
        self.assertFalse(session.success)
        self.assertEqual(session.failure_reason, "premature_action")

    def test_switch_prepared_target_becomes_stale(self):
        session = None
        for seed in range(1000):
            candidate = BenchmarkSession(generate_episode(seed, 0.5))
            if candidate.stage.kind == "switch":
                session = candidate
                break
        self.assertIsNotNone(session)
        p = session.stage.payload
        while session.stage_elapsed < p["wait_seconds"]:
            session.step(1/60)
        prepared = session._object_by_id(p["prepared_id"])
        session.click(prepared.x, prepared.y)
        self.assertTrue(session.done)
        self.assertEqual(session.failure_reason, "stale_action")


if __name__ == "__main__":
    unittest.main(verbosity=2)
