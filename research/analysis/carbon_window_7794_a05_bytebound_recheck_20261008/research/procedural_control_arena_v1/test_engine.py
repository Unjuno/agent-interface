from __future__ import annotations

import json
import unittest

from engine import (
    BenchmarkSession,
    DifficultyProfile,
    EpisodeSpec,
    FULL_PRIMITIVES,
    generate_episode,
    solve_with_oracle_for_test,
)


def single_stage(kind: str, seed: int = 1, level: float = 0.5) -> BenchmarkSession:
    spec = generate_episode(seed, level, suite="full")
    stage = next(s for s in spec.stages if s.kind == kind)
    one = EpisodeSpec(spec.schema, spec.seed, spec.suite, spec.difficulty, (stage,))
    return BenchmarkSession(one)


class ArenaV1Test(unittest.TestCase):
    def test_generation_is_deterministic(self):
        a = generate_episode(1234567, 0.42, suite="full")
        b = generate_episode(1234567, 0.42, suite="full")
        self.assertEqual(a.canonical_json(), b.canonical_json())
        self.assertEqual(a.public_fingerprint(), b.public_fingerprint())

    def test_full_suite_contains_all_primitives_once(self):
        spec = generate_episode(99, 0.4, suite="full")
        self.assertEqual(set(s.kind for s in spec.stages), set(FULL_PRIMITIVES))
        self.assertEqual(len(spec.stages), len(FULL_PRIMITIVES))

    def test_public_state_does_not_leak_seed_or_hidden_ids(self):
        spec = generate_episode(998877, 0.5, suite="full")
        session = BenchmarkSession(spec)
        public_state = session.public_state()
        public = json.dumps(public_state, sort_keys=True)
        self.assertEqual(set(public_state), {"schema", "sim_time", "done"})
        self.assertFalse(hasattr(session, "instruction"))
        self.assertNotIn(str(spec.seed), public)
        for stage in spec.stages:
            for key in ("target_id", "active_id", "prepared_id", "recovery_x", "recovery_y"):
                if key in stage.payload:
                    self.assertNotIn(str(stage.payload[key]), public)

    def test_difficulty_moves_declared_axes(self):
        easy = DifficultyProfile.from_level(0.0)
        hard = DifficultyProfile.from_level(1.0)
        self.assertGreater(easy.target_radius, hard.target_radius)
        self.assertLess(easy.target_speed, hard.target_speed)
        self.assertLess(easy.distractor_count, hard.distractor_count)
        self.assertLess(easy.visual_similarity, hard.visual_similarity)
        self.assertGreater(easy.drag_tolerance, hard.drag_tolerance)
        self.assertLess(easy.assembly_pieces, hard.assembly_pieces)
        self.assertGreater(easy.trace_tolerance, hard.trace_tolerance)
        self.assertLess(easy.trace_checkpoints, hard.trace_checkpoints)
        self.assertGreater(easy.objective_sample_radius, hard.objective_sample_radius)

    def test_axis_override_changes_only_requested_axis(self):
        base = DifficultyProfile.from_level(0.5)
        mod = base.with_overrides({"target_speed": 17.5})
        a = base.__dict__.copy(); b = mod.__dict__.copy()
        self.assertNotEqual(a.pop("target_speed"), b.pop("target_speed"))
        self.assertEqual(a, b)

    def test_invalid_axis_overrides_are_rejected(self):
        base = DifficultyProfile.from_level(0.5)
        for overrides in (
            {"visual_similarity": 1.1},
            {"drag_tolerance": 0},
            {"assembly_tolerance": -1},
            {"trace_tolerance": 0},
            {"recovery_displacement": -1},
            {"typing_length": 0},
            {"objective_sample_radius": 2},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    base.with_overrides(overrides)

    def test_oracle_full_suite_passes_across_levels_and_seeds(self):
        for level in (0.0, 0.5, 1.0):
            for seed in range(20):
                with self.subTest(level=level, seed=seed):
                    s = BenchmarkSession(generate_episode(seed, level, suite="full"))
                    solve_with_oracle_for_test(s)
                    self.assertTrue(s.done)
                    self.assertTrue(s.success, (s.failure_reason, s.failure_locus, s.stage.kind if not s.done else None))
                    self.assertEqual(s.metrics.completed_stages, len(FULL_PRIMITIVES))

    def test_switch_premature_click_fails_closed(self):
        s = single_stage("switch", 20)
        s.pointer_down(10, 10)
        self.assertTrue(s.done)
        self.assertEqual(s.failure_reason, "premature_action")
        self.assertEqual(s.failure_locus, "CONTROLLER_DECISION")

    def test_switch_prepared_target_is_stale(self):
        s = single_stage("switch", 21)
        p = s.stage.payload
        while s.stage_elapsed < p["wait_seconds"]:
            s.step(1/60)
        obj = s._object_by_id(p["prepared_id"])
        s.pointer_down(obj.x, obj.y)
        self.assertEqual(s.failure_reason, "stale_action")
        self.assertEqual(s.failure_locus, "STALE_STATE")

    def test_combo_requires_keyboard_and_pointer_overlap(self):
        s = single_stage("combo", 22)
        p = s.stage.payload
        obj = s._object_by_id(p["target_id"])
        s.pointer_down(obj.x, obj.y)
        self.assertTrue(s.done)
        self.assertEqual(s.failure_reason, "missing_chord")

        s = single_stage("combo", 22)
        p = s.stage.payload
        obj = s._object_by_id(p["target_id"])
        s.key_down(p["required_key"])
        s.pointer_down(obj.x, obj.y)
        self.assertTrue(s.success)

    def test_drag_drop_precision_is_scored(self):
        s = single_stage("drag", 23)
        p = s.stage.payload
        obj = s.objects[0]
        s.pointer_down(obj.x, obj.y)
        s.pointer_move(p["slot_x"], p["slot_y"])
        s.pointer_up(p["slot_x"], p["slot_y"])
        self.assertTrue(s.success)

        s = single_stage("drag", 23)
        obj = s.objects[0]
        s.pointer_down(obj.x, obj.y)
        s.pointer_move(20, 20)
        s.pointer_up(20, 20)
        self.assertEqual(s.failure_reason, "drag_drop_miss")
        self.assertEqual(s.failure_locus, "MOTOR")

    def test_trace_requires_ordered_path_coverage(self):
        s = single_stage("trace", 24)
        p = s.stage.payload
        pts = p["points"]
        s.pointer_down(*pts[0])
        for pt in pts[1:]:
            s.pointer_move(*pt)
        s.pointer_up(*pts[-1])
        self.assertTrue(s.success)

        s = single_stage("trace", 24)
        p = s.stage.payload
        pts = p["points"]
        s.pointer_down(*pts[0])
        s.pointer_move(5, 5)
        self.assertTrue(s.done)
        self.assertEqual(s.failure_reason, "trace_deviation")

    def test_recovery_requires_reacquisition_after_interrupt(self):
        s = single_stage("recovery", 25)
        p = s.stage.payload
        obj = s._object_by_id(p["target_id"])
        old = (obj.x, obj.y)
        s.pointer_down(obj.x, obj.y)
        self.assertFalse(s.done)
        self.assertTrue(s.recovery_triggered)
        obj = s._object_by_id(p["target_id"])
        self.assertNotEqual(old, (obj.x, obj.y))
        s.pointer_down(obj.x, obj.y)
        self.assertTrue(s.success)
        self.assertEqual(s.metrics.recovery_events, 1)
        self.assertEqual(s.metrics.recovery_successes, 1)

    def test_mouse_release_does_not_leak_into_next_stage(self):
        spec = generate_episode(123, 0.2, suite="core")
        # Force a target stage first and another stage second.
        target = next(s for s in spec.stages if s.kind == "target")
        typing = next(s for s in spec.stages if s.kind == "typing")
        custom = EpisodeSpec(spec.schema, spec.seed, spec.suite, spec.difficulty, (target, typing))
        s = BenchmarkSession(custom)
        p = s.stage.payload
        obj = s._object_by_id(p["target_id"])
        s.pointer_down(obj.x, obj.y)
        self.assertEqual(s.stage.kind, "typing")
        # Physical release from the same click must not focus/fail the new stage.
        s.pointer_up(obj.x, obj.y)
        self.assertFalse(s.terminal_focused)
        self.assertFalse(s.done)


if __name__ == "__main__":
    unittest.main(verbosity=2)
