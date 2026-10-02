import json
import tempfile
import unittest
from pathlib import Path

from auditor import audit_arm, mutation_controls


STATE_ROWS = (
    ("A", "separable"), ("B", "separable"),
    ("C", "action_equivalent"), ("D", "action_equivalent"),
    ("E", "impossible"), ("F", "impossible"),
    ("G", "stale"), ("H", "stale"),
    ("I", "convergent"), ("J", "convergent"),
)


def signal_after(state, probes):
    if not probes or probes == ["P"]:
        return "READY"
    return {
        "A": "LEFT", "B": "RIGHT", "C": "READY", "D": "READY",
        "E": "UNKNOWN", "F": "UNKNOWN", "G": "EXPIRED_LEFT", "H": "EXPIRED_RIGHT",
        "I": "BOTH", "J": "BOTH",
    }[state]


def fixture_rows(arm):
    candidate = []
    oracle = []
    for index, (state, family) in enumerate(STATE_ROWS):
        if family == "action_equivalent":
            probes = ["P"] if arm == "one_step" else []
            choice, effect = "ACT_COMMON", "EFFECT_OK"
        elif family == "convergent" and arm == "adaptive":
            probes, choice, effect = ["P", "Q"], "ACT_COMMON", "EFFECT_OK"
        elif arm == "no_probe":
            probes, choice, effect = [], "YIELD", None
        elif arm == "one_step":
            probes, choice, effect = ["P"], "YIELD", None
        elif family == "separable":
            probes = ["P", "Q"]
            choice = "ACT_LEFT" if state == "A" else "ACT_RIGHT"
            effect = "EFFECT_OK"
        else:
            probes, choice, effect = ["P", "Q"], "YIELD", None
        observations = ["READY"]
        prefix = []
        for probe in probes:
            prefix.append(probe)
            observations.append(signal_after(state, prefix))
        candidate.append({
            "trial_index": index, "family": family,
            "arm": arm, "observations": observations, "probes": probes,
            "choice": choice, "effect_signal": effect,
        })
        oracle.append({"event": "CASE_START", "trial_index": index, "family": family,
                       "state_id": state, "generation": 0})
        for probe in probes:
            oracle.append({"event": "SAFE_PROBE", "trial_index": index, "probe": probe,
                           "generation": 0 if probe == "P" else 1})
        actions = []
        terminal = "Z" if state in ("I", "J") and "Q" in probes else (
            "TARGET_EXPIRED_LEFT" if state == "G" and "Q" in probes else
            "TARGET_EXPIRED_RIGHT" if state == "H" and "Q" in probes else
            f"{state}{len(probes)}"
        )
        if choice.startswith("ACT_"):
            action = choice.removeprefix("ACT_")
            actions = [action]
            allowed = ["COMMON"] if state in ("C", "D") or terminal == "Z" else [action]
            oracle.append({"event": "ACTION", "trial_index": index, "action": action,
                           "allowed": allowed, "outcome": "VERIFIED_EFFECT",
                           "generation": int("Q" in probes), "terminal_state": terminal})
        oracle.append({"event": "CASE_END", "trial_index": index, "state_id": state,
                       "terminal_state": terminal, "probes": probes,
                       "actions": actions, "unsafe_probe_count": 0})
    oracle.append({"event": "FIXTURE_END", "rows": 8})
    return candidate, oracle


class AuditorContractTests(unittest.TestCase):
    def test_independent_replay_accepts_all_three_policy_arms(self):
        for arm in ("adaptive", "no_probe", "one_step"):
            with self.subTest(arm=arm):
                errors, metrics = audit_arm(*fixture_rows(arm), arm)
                self.assertEqual(errors, [])
                self.assertEqual(metrics["rows"], 10)

    def test_missing_case_and_wrong_pixel_branch_are_rejected(self):
        candidate, oracle = fixture_rows("adaptive")
        errors, _ = audit_arm(candidate[:-1], oracle, "adaptive")
        self.assertTrue(any("candidate_row_count" in error for error in errors))

        candidate, oracle = fixture_rows("adaptive")
        right_index = next(i for i, row in enumerate(candidate) if row["choice"] == "ACT_RIGHT")
        candidate[right_index]["observations"][-1] = "LEFT"
        errors, _ = audit_arm(candidate, oracle, "adaptive")
        self.assertTrue(any("pixel_observation_mismatch" in error for error in errors))

    def test_unexpected_click_and_bad_generation_are_rejected(self):
        candidate, oracle = fixture_rows("adaptive")
        oracle.append({"event": "PROBE_ORDER_ERROR", "trial_index": 0, "probe": "Q"})
        errors, _ = audit_arm(candidate, oracle, "adaptive")
        self.assertTrue(any("invalid_gui_interaction" in error for error in errors))

        candidate, oracle = fixture_rows("adaptive")
        event = next(row for row in oracle if row.get("event") == "SAFE_PROBE" and row.get("probe") == "Q")
        event["generation"] = 7
        errors, _ = audit_arm(candidate, oracle, "adaptive")
        self.assertTrue(any("probe_generation" in error for error in errors))

    def test_all_five_frozen_raw_mutations_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for arm in ("adaptive", "no_probe", "one_step"):
                candidate, oracle = fixture_rows(arm)
                arm_dir = root / arm
                arm_dir.mkdir()
                (arm_dir / "candidate.jsonl").write_text(
                    "".join(json.dumps(row) + "\n" for row in candidate), encoding="utf-8"
                )
                (arm_dir / "oracle.jsonl").write_text(
                    "".join(json.dumps(row) + "\n" for row in oracle), encoding="utf-8"
                )
            controls = mutation_controls(root)
            self.assertEqual(len(controls), 5)
            self.assertTrue(all(controls.values()), controls)


if __name__ == "__main__":
    unittest.main()
