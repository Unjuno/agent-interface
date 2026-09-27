#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path

import benchmark


class ProceduralControlLabTests(unittest.TestCase):
    def test_episode_generation_is_deterministic(self):
        d = benchmark.Difficulty.from_level(0.42)
        a = benchmark.generate_episode(123456, d)
        b = benchmark.generate_episode(123456, d)
        self.assertEqual(a, b)

    def test_difficulty_moves_expected_frontiers_monotonically(self):
        easy = benchmark.Difficulty.from_level(0.0)
        hard = benchmark.Difficulty.from_level(1.0)
        self.assertGreater(easy.target_size, hard.target_size)
        self.assertLess(easy.target_speed, hard.target_speed)
        self.assertLess(easy.distractors, hard.distractors)
        self.assertGreater(easy.reaction_deadline_ms, hard.reaction_deadline_ms)
        self.assertGreater(easy.move_goal_size, hard.move_goal_size)
        self.assertLess(easy.typing_length, hard.typing_length)

    def test_positive_control_passes_without_violations(self):
        spec = benchmark.generate_episode(11, benchmark.Difficulty.from_level(0.5))
        engine = benchmark.ControlLabEngine(spec)
        benchmark.drive_perfect_headless(engine)
        self.assertTrue(engine.success, engine.result(reveal_private=True))
        self.assertEqual(engine.violations, [])
        self.assertEqual(engine.stage, "DONE")

    def test_input_during_wait_is_retained_as_forbidden_effect(self):
        spec = benchmark.generate_episode(22, benchmark.Difficulty.from_level(0.2))
        engine = benchmark.ControlLabEngine(spec)
        engine.key_down("w")
        self.assertIn("input_during_wait", engine.violations)
        self.assertEqual(engine.metrics.early_actions, 1)

    def test_wrong_click_is_attributed(self):
        spec = benchmark.generate_episode(33, benchmark.Difficulty.from_level(0.3))
        engine = benchmark.ControlLabEngine(spec)
        while engine.stage == "WAIT":
            engine.advance(20)
        # Drive to the goal with the positive control logic up through MOVE.
        while engine.stage == "MOVE" and not engine.finished:
            x1, y1, x2, y2 = spec.goal_rect
            tx, ty = (x1+x2)/2, (y1+y2)/2
            keys = []
            if engine.player_x < tx - 2: keys.append("d")
            elif engine.player_x > tx + 2: keys.append("a")
            if engine.player_y < ty - 2: keys.append("s")
            elif engine.player_y > ty + 2: keys.append("w")
            for k in keys:
                if k not in engine.held_keys: engine.key_down(k)
            for k in list(engine.held_keys):
                if k not in keys: engine.key_up(k)
            engine.advance(10)
        for k in list(engine.held_keys):
            engine.key_up(k)
        self.assertEqual(engine.stage, "CLICK")
        target = next(a for a in engine.actors if a.spec.is_target)
        # Guaranteed far enough from the target to miss.
        x = 1.0 if target.x > benchmark.WIDTH / 2 else benchmark.WIDTH - 1.0
        y = benchmark.ARENA_TOP + 1.0
        engine.click(x, y)
        self.assertEqual(engine.metrics.wrong_clicks, 1)
        self.assertIn("wrong_or_missed_click", engine.violations)

    def test_public_result_does_not_leak_seed_or_oracle(self):
        spec = benchmark.generate_episode(44, benchmark.Difficulty.from_level(0.4))
        engine = benchmark.ControlLabEngine(spec)
        public = json.dumps(engine.result(reveal_private=False))
        self.assertNotIn('"seed"', public)
        self.assertNotIn("typing_code", public)
        self.assertNotIn("target_actor_id", public)


if __name__ == "__main__":
    unittest.main()
