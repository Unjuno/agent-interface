"""Regression for post-freeze workload mutation accepted by A01 audit."""
import contextlib
import hashlib
import importlib.util
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "issue7367_context_liveness_a01_20261004"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical_sha(value):
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def make_self_consistent_workload_mutation(tmp):
    for name in ("PRE-RUN.json", "run_a01.py", "audit_a01.py", "workload.json"):
        shutil.copy2(SOURCE / name, tmp / name)
    shutil.copy2(SOURCE / "container-out/RAW.json", tmp / "RAW.json")
    workload = json.loads((tmp / "workload.json").read_text())
    raw = json.loads((tmp / "RAW.json").read_text())
    record = next(x for x in workload["records"] if x["id"] == "stale-summary")
    record["audit_padding"] = "x" * 8192
    workload_bytes = (json.dumps(workload, indent=2, sort_keys=True) + "\n").encode()
    (tmp / "workload.json").write_bytes(workload_bytes)
    raw["workload_sha256"] = sha(workload_bytes)
    raw["canonical_record_sha256"]["stale-summary"] = canonical_sha(record)
    for policy in raw["policies"]:
        selected = set(policy["selected_ids"])
        rows = [r for r in workload["records"] if r["id"] in selected]
        policy["visible_bytes"] = len(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode())
    (tmp / "RAW.json").write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")
    return workload, raw


class WorkloadBindingRegression(unittest.TestCase):
    def test_v2_rejects_the_self_consistent_workload_mutation_accepted_by_v1(self):
        with tempfile.TemporaryDirectory() as tmp_name:
            tmp = Path(tmp_name)
            mutant_workload_obj, mutant_raw_obj = make_self_consistent_workload_mutation(tmp)
            spec = importlib.util.spec_from_file_location("legacy_audit", tmp / "audit_a01.py")
            legacy = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(legacy)
            legacy.HERE = tmp
            with contextlib.redirect_stdout(io.StringIO()):
                legacy_accepted = legacy.audit(tmp / "RAW.json", tmp / "AUDIT.json")
            self.assertTrue(legacy_accepted, "mutation no longer reproduces the A01 binding gap")

            spec = importlib.util.spec_from_file_location("audit_a02", ROOT / "audit_a02.py")
            current = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(current)
            prerun = json.loads((SOURCE / "PRE-RUN.json").read_text())
            baseline_workload = (SOURCE / "workload.json").read_bytes()
            baseline_raw = (SOURCE / "container-out/RAW.json").read_bytes()
            frozen_raw_sha = sha(baseline_raw)
            self.assertEqual([], current.binding_errors(baseline_workload, baseline_raw, prerun, frozen_raw_sha))
            errors = current.binding_errors((tmp / "workload.json").read_bytes(),
                                            (tmp / "RAW.json").read_bytes(), prerun, frozen_raw_sha)
            self.assertIn("workload_bytes_match_prerun", errors)
            self.assertIn("raw_artifact_matches_frozen_sha256", errors)

            # Construction evidence is already retained in the package. Keep
            # this regression pure: all mutation inputs and audit output stay
            # inside TemporaryDirectory so a test run cannot overwrite them.
            original_graph = json.loads(baseline_workload)
            mutant_graph = mutant_workload_obj
            graph_hash = sha(json.dumps({"nodes": original_graph["nodes"], "edges": original_graph["edges"]},
                                        sort_keys=True, separators=(",", ":")).encode())
            mutant_graph_hash = sha(json.dumps({"nodes": mutant_graph["nodes"], "edges": mutant_graph["edges"]},
                                               sort_keys=True, separators=(",", ":")).encode())
            mutated_record = next(r for r in mutant_graph["records"]
                                  if r["id"] == "stale-summary")
            self.assertEqual(graph_hash, mutant_graph_hash)
            self.assertEqual(8192, len(mutated_record["audit_padding"]))
            self.assertEqual(mutant_raw_obj["workload_sha256"],
                             sha((tmp / "workload.json").read_bytes()))
            self.assertTrue(json.loads((tmp / "AUDIT.json").read_text())["checks"]["workload_hash_matches"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
