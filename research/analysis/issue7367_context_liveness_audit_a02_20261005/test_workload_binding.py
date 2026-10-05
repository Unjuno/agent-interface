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

            # Retain the failing-v1 reproduction and both self-consistent mutant
            # inputs as frozen construction evidence for the audit-only run.
            dest = ROOT / "construction_mutation"
            dest.mkdir(exist_ok=True)
            for source_name, target_name in (("workload.json", "workload.json"),
                                             ("RAW.json", "RAW.json"),
                                             ("AUDIT.json", "AUDIT_V1.json")):
                shutil.copy2(tmp / source_name, dest / target_name)
            original_graph = json.loads(baseline_workload)
            mutant_graph = mutant_workload_obj
            graph_hash = sha(json.dumps({"nodes": original_graph["nodes"], "edges": original_graph["edges"]},
                                        sort_keys=True, separators=(",", ":")).encode())
            mutant_graph_hash = sha(json.dumps({"nodes": mutant_graph["nodes"], "edges": mutant_graph["edges"]},
                                               sort_keys=True, separators=(",", ":")).encode())
            repro = {
                "schema": "issue7367-a02-construction-mutation-v1",
                "mutant_workload_path": "construction_mutation/workload.json",
                "mutant_raw_path": "construction_mutation/RAW.json",
                "mutant_audit_path": "construction_mutation/AUDIT_V1.json",
                "added_payload_bytes": 8192,
                "original_workload_sha256": sha(baseline_workload),
                "mutated_workload_sha256": sha((tmp / "workload.json").read_bytes()),
                "original_raw_sha256": frozen_raw_sha,
                "mutated_raw_sha256": sha((tmp / "RAW.json").read_bytes()),
                "mutated_record_sha256": mutant_raw_obj["canonical_record_sha256"]["stale-summary"],
                "raw_declares_mutated_workload_sha256": mutant_raw_obj["workload_sha256"] == sha((tmp / "workload.json").read_bytes()),
                "legacy_auditor_passed_mutant": legacy_accepted,
                "legacy_workload_hash_check_passed": json.loads((tmp / "AUDIT.json").read_text())["checks"]["workload_hash_matches"],
                "original_graph_sha256": graph_hash,
                "mutated_graph_sha256": mutant_graph_hash,
            }
            (ROOT / "CONSTRUCTION_REPRO.json").write_text(json.dumps(repro, indent=2, sort_keys=True) + "\n")
            self.assertEqual(graph_hash, mutant_graph_hash)
            self.assertGreater(repro["mutated_workload_sha256"], "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
