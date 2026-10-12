"""Exercise stale initial-cover recovery beside the strict release boundary."""
import ast
import copy
import json
from pathlib import Path
import unittest


DEFAULT_SOURCE = Path(__file__).with_name("map01_overlap_controller_v39.py")
SOURCE = DEFAULT_SOURCE
TREE = ast.parse(SOURCE.read_text(encoding="utf-8"))
NAMES = {
    "terminal_release_is_known_empty",
    "require_cover_terminal",
    "cancel_initial_cover_before_planner",
    "cover_submission_invalidation_receipt",
    "reset_cover_after_preacceptance_rejection",
    "prefer_observation_invalidation",
    "observe_cover_submission_events",
    "recover_pending_observation_backlog",
    "recover_coherent_source_after_observation",
    "recover_stale_cover_submission",
    "submit_initial_cover_with_recovery",
}
FUNCTIONS = [node for node in TREE.body
             if isinstance(node, ast.FunctionDef) and node.name in NAMES]
assert {node.name for node in FUNCTIONS} == NAMES
NAMESPACE = {
    "json": json,
    "RuntimeError": RuntimeError,
    # The controller's bounded backlog implementation is exercised separately;
    # here the fixture supplies one already-settled fresh observation.
    "settle_pending_observation_backlog": None,
}
exec(compile(ast.Module(body=FUNCTIONS, type_ignores=[]), str(SOURCE), "exec"),
     NAMESPACE)


BASE_RELEASE = {
    "verified": True,
    "keys_down": [],
    "buttons_down": [],
    "keys_unknown": [],
    "key_state_errors": [],
}


def terminal(identifier, status="cancelled", release=None):
    return {
        "event": "terminal",
        "id": identifier,
        "status": status,
        "release": copy.deepcopy(BASE_RELEASE if release is None else release),
    }


class ObservationMonitor:
    event_types = {"observation"}

    def __init__(self):
        self.seen = []

    def observe(self, row):
        self.seen.append(row["sequence"])
        return {"event": "paired_signal_invalidation",
                "reason": "health:below_hard_minimum",
                "sequence": row["sequence"]}


class PairObservationMonitor:
    event_types = {"typed_observation"}

    def __init__(self):
        self.last_pair_sequence = 12
        self.seen = []

    def observe(self, row):
        self.seen.append(row["sequence"])
        return {"event": "paired_signal_invalidation",
                "reason": "signal_pair_duplicate_epoch_mismatch",
                "sequence": row["sequence"]}


class Stdin:
    def __init__(self):
        self.writes = []

    def write(self, value):
        self.writes.append(value)

    def flush(self):
        pass


class Process:
    def __init__(self):
        self.stdin = Stdin()


class StaleInitialCoverReleaseCompositionTests(unittest.TestCase):
    def setUp(self):
        self.original_recovery = NAMESPACE["recover_pending_observation_backlog"]
        self.original_settle = NAMESPACE["settle_pending_observation_backlog"]

    def tearDown(self):
        NAMESPACE["recover_pending_observation_backlog"] = self.original_recovery
        NAMESPACE["settle_pending_observation_backlog"] = self.original_settle

    def test_stale_recovery_fails_closed_when_freshness_or_budget_gate_fails(self):
        source = {"event": "observation", "sequence": 11, "image": "old.png"}
        ack = {"event": "rejected", "id": "cover-old",
               "reason": "latest observation sequence required before input"}

        def rejected_submit(_consumed):
            return ack

        NAMESPACE["recover_pending_observation_backlog"] = (
            lambda *_args, **_kwargs: {
                "latest": source, "batches": 4, "exhausted": True})
        with self.assertRaisesRegex(RuntimeError, "recovery budget exhausted"):
            NAMESPACE["submit_initial_cover_with_recovery"](
                rejected_submit, identifier="cover-old",
                latest_reader=lambda: source, incoming=object(),
                wait=lambda *_args, **_kwargs: self.fail("must not wait"),
                observation_monitor=ObservationMonitor())

        NAMESPACE["recover_pending_observation_backlog"] = (
            lambda *_args, **_kwargs: {
                "latest": source, "batches": 1, "exhausted": False})
        with self.assertRaisesRegex(RuntimeError, "requires a newer observation"):
            NAMESPACE["submit_initial_cover_with_recovery"](
                rejected_submit, identifier="cover-old",
                latest_reader=lambda: source, incoming=object(),
                wait=lambda *_args, **_kwargs: self.fail("must not wait"),
                observation_monitor=ObservationMonitor())

    def test_stale_cover_recovers_then_next_cover_requires_known_empty_release(self):
        old = {"event": "observation", "sequence": 11, "image": "old.png"}
        fresh = {"event": "observation", "sequence": 12, "image": "fresh.png"}
        after_fresh = {"event": "observation", "sequence": 14,
                       "image": "after-fresh.png"}
        latest = [old]
        consumed_sequences = []
        monitor = ObservationMonitor()
        pair_monitor = PairObservationMonitor()

        def settle(_incoming, _latest, _identifier, observation_monitor):
            return {"latest": fresh, "batches": 1, "exhausted": False,
                    "invalidation": None}

        NAMESPACE["settle_pending_observation_backlog"] = settle

        def rejected_submit(consumed):
            consumed.append({"event": "observation", "sequence": 12})
            consumed_sequences.append(latest[0]["sequence"])
            return {"event": "rejected", "id": "cover-old",
                    "reason": "latest observation sequence required before input"}

        stale = NAMESPACE["submit_initial_cover_with_recovery"](
            rejected_submit, identifier="cover-old", latest_reader=lambda: latest[0],
            incoming=object(), wait=lambda *_args, **_kwargs: self.fail(
                "the settled fresh observation should satisfy recovery"),
            observation_monitor=monitor)

        built = []
        reset = NAMESPACE["reset_cover_after_preacceptance_rejection"](
            stale,
            build_monitor=lambda source: (built.append(source) or
                                          ("fresh-monitor", {"status": "unadmitted"})),
            select_monitor=lambda guard, admission, commands, iteration:
                (guard, {**admission, "commands": commands,
                         "iteration": iteration}))

        self.assertEqual(consumed_sequences, [11])
        self.assertEqual(monitor.seen, [12])
        self.assertEqual(stale["ack"]["event"], "rejected")
        self.assertEqual(stale["cover_policy"], "discarded_until_fresh_plan")
        self.assertEqual(reset["latest"], fresh)
        self.assertEqual(built, [fresh])
        self.assertEqual(reset["admission"]["commands"], [])
        self.assertEqual(reset["admission"]["iteration"], None)
        self.assertEqual(reset["receipt"]["ack"]["event"], "rejected")
        self.assertIsNone(reset["receipt"]["cover_cancel_terminal"])

        # The next cover is sourced from the recovered observation. If that
        # accepted cover is invalidated while its ACK is in flight, planner
        # handoff still waits for the strict, known-empty terminal receipt.
        latest[0] = fresh

        pair_latest_reads = [0]

        def paired_latest_reader():
            pair_latest_reads[0] += 1
            if pair_latest_reads[0] >= 2:
                latest[0] = after_fresh
                pair_monitor.last_pair_sequence = after_fresh["sequence"]
            return latest[0]

        def accepted_submit(consumed):
            consumed.append({"event": "typed_observation", "sequence": 13})
            consumed_sequences.append(latest[0]["sequence"])
            return {"event": "accepted", "id": "cover-next"}

        accepted = NAMESPACE["submit_initial_cover_with_recovery"](
            accepted_submit, identifier="cover-next", latest_reader=paired_latest_reader,
            incoming=object(), wait=lambda *_args, **_kwargs: self.fail(
                "the already-current coherent pair should satisfy recovery"),
            observation_monitor=pair_monitor)

        process = Process()
        known_empty = terminal("cover-next")
        cancelled = NAMESPACE["cancel_initial_cover_before_planner"](
            process, lambda predicate: known_empty if predicate(known_empty) else None,
            "cover-next")
        receipt = NAMESPACE["cover_submission_invalidation_receipt"](
            accepted, cancelled)

        self.assertEqual(consumed_sequences, [11, 12])
        self.assertEqual(accepted["submitted_sequence"], 12)
        self.assertEqual(accepted["latest"], after_fresh)
        self.assertEqual(accepted["invalidation"]["reason"],
                         "signal_pair_duplicate_epoch_mismatch")
        self.assertEqual(accepted["coherent_source_recovery"], {
            "required_after_sequence": 13,
            "invalidated_sequence": 13,
            "fresh_sequence": 14,
            "additional_invalidations": [],
        })
        self.assertEqual(pair_monitor.seen, [13])
        self.assertEqual(receipt["ack"]["event"], "accepted")
        self.assertEqual(receipt["cover_cancel_terminal"]["id"], "cover-next")
        self.assertEqual(len(process.stdin.writes), 1)

        for field, value in (("keys_unknown", None), ("keys_unknown", ["KEY_W"]),
                             ("key_state_errors", None),
                             ("key_state_errors", [{"source": "keymap_after"}])):
            release = copy.deepcopy(BASE_RELEASE)
            if value is None:
                release.pop(field)
            else:
                release[field] = value
            bad_terminal = terminal("cover-next", release=release)
            with self.subTest(field=field, value=value), self.assertRaises(RuntimeError):
                NAMESPACE["cancel_initial_cover_before_planner"](
                    Process(), lambda predicate: bad_terminal
                    if predicate(bad_terminal) else None, "cover-next")


if __name__ == "__main__":
    unittest.main()
