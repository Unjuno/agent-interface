"""Offline replay of the retained V39 health crossing and paired recovery."""
import ast
import hashlib
import json
from pathlib import Path
import time
import unittest


ROOT = Path(__file__).resolve().parents[3]
TRACE = Path(__import__("os").environ.get(
    "V39_TRACE_DIR", ROOT / "research/doom/results/map01-v39-coast-liveness-live-01"))
CONTROLLER = Path(__import__("os").environ.get(
    "V39_CONTROLLER_SOURCE", ROOT / "research/doom/map01_overlap_controller_v39.py"))
GUARD = Path(__import__("os").environ.get(
    "V39_GUARD_SOURCE", ROOT / "research/live_control/observable_signal_guard_v2.py"))


def load_production_classes():
    tree = ast.parse(CONTROLLER.read_bytes(), filename=str(CONTROLLER))
    names = {"_typed_json_equal", "_signal_pair_matches",
             "_signal_pair_content_matches", "DoomCoverSignalPairMonitor",
             "DeferredObservationMonitor", "recover_coherent_source_after_observation"}
    nodes = [node for node in tree.body
             if getattr(node, "name", None) in names]
    found = {node.name for node in nodes}
    if found != names:
        raise AssertionError(f"missing production recovery symbols: {names-found}")
    namespace = {"time": time}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,
                                                      type_ignores=[])),
                 str(CONTROLLER), "exec"), namespace)

    guard_tree = ast.parse(GUARD.read_bytes(), filename=str(GUARD))
    guard_nodes = [node for node in guard_tree.body
                   if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name)
                           and target.id == "FIELDS" for target in node.targets)] + [
                   node for node in guard_tree.body
                   if getattr(node, "name", None) in {"binding_key", "validate"}
                   or (isinstance(node, ast.ClassDef)
                       and node.name == "ObservableSignalGuard")]
    found_guard = {getattr(node, "name", None) or
                   (node.targets[0].id if isinstance(node, ast.Assign)
                    and isinstance(node.targets[0], ast.Name) else None)
                   for node in guard_nodes}
    if found_guard != {"FIELDS", "binding_key", "validate", "ObservableSignalGuard"}:
        raise AssertionError("pinned ObservableSignalGuard dependencies missing")
    guard_ns = {"json": json}
    exec(compile(ast.fix_missing_locations(ast.Module(body=guard_nodes,
                                                      type_ignores=[])),
                 str(GUARD), "exec"), guard_ns)
    namespace.update(guard_ns)
    return namespace


def signal(signal_id, value, sequence, capture_ns, binding):
    return {"status": "observed", "signal_id": signal_id,
            "value": value, "sequence": sequence,
            "capture_ns": capture_ns, "binding": binding}


class Reader:
    def read(self, observation):
        return observation["replay_signals"]["health"]


class AmmoReader:
    def read(self, observation):
        return observation["replay_signals"]["ammo"]


class LiveTracePairRecoveryTests(unittest.TestCase):
    def test_retained_health_crossing_reconciles_then_requires_new_pair(self):
        raw_bytes = (TRACE / "runtime/events.jsonl").read_bytes()
        self.assertEqual(hashlib.sha256(raw_bytes).hexdigest(),
                         "2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381")
        events = [json.loads(line) for line in raw_bytes.splitlines()]
        source = next(row for row in events
                      if row.get("event") == "typed_observation"
                      and row.get("sequence") == 166)
        typed = next(row for row in events
                     if row.get("event") == "typed_observation"
                     and row.get("sequence") == 218)
        full = next(row for row in events
                    if row.get("event") == "observation"
                    and row.get("sequence") == 218)
        report = json.loads((TRACE / "report.json").read_text(encoding="utf-8"))
        decision = next(row for row in report["decisions"]
                        if row.get("iteration") == 5)
        admitted = decision["cover_validity_admission"]
        self.assertEqual(admitted["effective"]["hard_minimum"], 51)
        health_source = admitted["source_signal"]
        binding = source["pointer_binding"]
        self.assertEqual(health_source["value"], 61)
        self.assertEqual(health_source["sequence"], 166)
        self.assertEqual(typed["signals"]["health"]["value"], 48)
        self.assertEqual(typed["signals"]["ammo"]["value"], 37)
        self.assertEqual(typed["frame_rgb_sha256"], full["frame_rgb_sha256"])
        self.assertEqual(typed["pointer_binding"], full["pointer_binding"])
        self.assertEqual(typed["signals"]["health"]["value"], 48)
        self.assertEqual(typed["signals"]["ammo"]["value"], 37)

        api = load_production_classes()
        guard_type = api["ObservableSignalGuard"]
        def make_guard(name, source_signal, floor):
            spec = {"op": "observable_signal_guard", "guard_id": name,
                    "source_sequence": source_signal["sequence"],
                    "signal_id": name.split("-")[-1],
                    "source_value": source_signal["value"],
                    "hard_minimum": floor, "max_source_age_ms": 30000,
                    "on_soft_change": "preserve_existing_policy",
                    "on_hard_change": "needs_decision",
                    "on_unknown": "needs_decision"}
            return guard_type(spec, source_signal, source_signal["binding"])

        ammo_source = {"status": "observed", "signal_id": "ammo", "value": 40,
                       "sequence": 166, "capture_ns": source["capture_ns"],
                       "binding": binding}
        monitor = api["DoomCoverSignalPairMonitor"](
            {"health": make_guard("map01-health", health_source, 51),
             "ammo": make_guard("map01-ammo", ammo_source, 1)},
            Reader(), AmmoReader())
        invalidation = monitor.observe(typed)
        self.assertEqual(invalidation["reason"], "health:below_hard_minimum")
        self.assertEqual(invalidation["sequence"], 218)
        self.assertFalse(invalidation["grants_input_authority"])
        self.assertEqual(monitor.last_pair_sequence, 166,
                         "typed-only hard crossing must not claim a coherent pair")
        full_with_replay_signals = dict(full, replay_signals=typed["signals"])
        self.assertIsNone(monitor.observe(full_with_replay_signals),
                          "matching artifact row reconciles the invalidated epoch")
        self.assertEqual(monitor.last_pair_sequence, 218)

        stale = {"reason": "signal_pair_hard_invalidation", "sequence": 218}
        latest = [dict(full_with_replay_signals, sequence=218, signals={
            "health": dict(typed["signals"]["health"]),
            "ammo": dict(typed["signals"]["ammo"])})]
        with self.assertRaisesRegex(RuntimeError, "did not produce a coherent frame"):
            api["recover_coherent_source_after_observation"](
                166, stale, latest_reader=lambda: latest[0],
                wait=lambda predicate, observation_monitor: None,
                observation_monitor=monitor)

        fresh_capture = full["capture_ns"] + 1_000_000
        fresh_binding = dict(binding)
        fresh_signals = {
            "health": signal("health", 51, 219, fresh_capture, fresh_binding),
            "ammo": signal("ammo", 37, 219, fresh_capture, fresh_binding),
        }
        fresh = {"event": "observation", "sequence": 219,
                 "capture_ns": fresh_capture,
                 "pointer_binding": fresh_binding,
                 "frame_rgb_sha256": "a" * 64,
                 "signals": fresh_signals,
                 "replay_signals": fresh_signals}
        fresh_result = monitor.observe(fresh)
        self.assertIsNone(fresh_result, repr(fresh_result))
        latest[0] = fresh
        self.assertEqual(monitor.last_pair_sequence, 219,
                         f"monitor last={monitor.last_sequence} event={monitor.last_event_kind}; "
                         f"signals={fresh_signals!r}")
        recovered, receipt = api["recover_coherent_source_after_observation"](
            218, stale, latest_reader=lambda: latest[0],
            wait=lambda predicate, observation_monitor: self.fail(
                "already-coherent fresh pair must recover without waiting"),
            observation_monitor=monitor)
        self.assertEqual(recovered["sequence"], 219)
        self.assertEqual(receipt["required_after_sequence"], 218)
        self.assertEqual(receipt["fresh_sequence"], 219)
        self.assertEqual(receipt["additional_invalidations"], [])


if __name__ == "__main__":
    unittest.main()
