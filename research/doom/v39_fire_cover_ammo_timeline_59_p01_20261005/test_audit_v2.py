import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
P01 = "research/doom/v39_fire_cover_ammo_timeline_59_p01_20261005"


def pinned(name):
    commit = json.loads((ROOT / "AUDIT_V2_FREEZE.json").read_text(encoding="utf-8"))["created_from_commit"]
    return subprocess.check_output(["git", "show", f"{commit}:{P01}/{name}"], cwd=REPO)


def pinned_result():
    return json.loads(pinned("RESULT.json"))


class FullResultAuditTests(unittest.TestCase):
    def run_audit(self, script_name, result):
        with tempfile.TemporaryDirectory(prefix="p01-result-mutation-") as temporary:
            package = Path(temporary)
            candidate = package / "RESULT.json"
            candidate.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
                                 encoding="utf-8")
            output = package / "AUDIT.json"
            command = ["python3", "-B", str(ROOT / script_name)]
            if script_name == "audit_v2.py":
                command.extend(["--candidate-result", str(candidate)])
            else:
                (package / "FREEZE.json").write_bytes(pinned("FREEZE.json"))
                (package / "audit.py").write_bytes(pinned("audit.py"))
                command = ["python3", "-B", str(package / "audit.py")]
            if script_name == "audit_v2.py":
                command.extend(["--output", str(output)])
            return subprocess.run(command, cwd=REPO, capture_output=True,
                                  text=True, check=False)

    def test_unmodified_p01_result_matches_raw_reconstruction(self):
        outcome = self.run_audit("audit_v2.py", pinned_result())
        self.assertEqual(outcome.returncode, 0, outcome.stderr + outcome.stdout)
        self.assertEqual(json.loads(outcome.stdout)["disposition"], "PASS_FULL_RESULT_RECONSTRUCTION")

    def test_rejects_unreconstructed_summary_mutations(self):
        mutations = {
            "event_names": lambda result: result.update(
                event_names=["post_control_score", "per_window_useful_effect"]),
            "totals": lambda result: result.update(
                typed_observations_total=0, runtime_event_rows_total=0),
            "window_count": lambda result: result.update(active_fire_cover_windows=99),
            "cover_actions": lambda result: result["windows"][0].update(cover_actions=[]),
            "model_wait": lambda result: result["windows"][0].update(model_wait_ms=0),
            "invalidation_signal": lambda result: result["windows"][0].update(
                policy_invalidation_signal="ammo"),
            "effect_events": lambda result: result.update(
                event_names=["per_window_useful_effect"],
                per_window_useful_effect_events=1),
            "bool_int_alias": lambda result: result.update(active_fire_cover_windows=True),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                result = pinned_result()
                mutate(result)
                outcome = self.run_audit("audit_v2.py", result)
                self.assertEqual(outcome.returncode, 1, outcome.stderr + outcome.stdout)
                self.assertEqual(json.loads(outcome.stdout)["disposition"], "FAIL_RESULT_MISMATCH")

    def test_reproduces_old_audit_false_pass_and_new_audit_rejects_it(self):
        result = pinned_result()
        result["event_names"] = ["post_control_score", "per_window_useful_effect"]
        legacy = self.run_audit("audit.py", result)
        self.assertEqual(legacy.returncode, 0, legacy.stderr + legacy.stdout)
        self.assertEqual(json.loads(legacy.stdout)["disposition"], "PASS")
        fixed = self.run_audit("audit_v2.py", result)
        self.assertEqual(fixed.returncode, 1, fixed.stderr + fixed.stdout)
        self.assertTrue(any(path.startswith("$.event_names") for path in json.loads(fixed.stdout)["mismatch_paths"]))


if __name__ == "__main__":
    unittest.main()
