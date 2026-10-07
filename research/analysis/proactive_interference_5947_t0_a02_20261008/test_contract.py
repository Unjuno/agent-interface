"""Construction contract tests; never run after a formal CLI invocation."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from candidate import build_corpus
from auditor import audit_corpus

class ContractTests(unittest.TestCase):
    def test_cardinality_and_complete_strata(self):
        rows = build_corpus()
        self.assertEqual((len(rows), sum(r["kind"] == "matched" for r in rows), sum(r["kind"] == "position_control" for r in rows)), (50, 48, 2))
        self.assertEqual(len({(r["condition"], r["depth"], r["arm"]) for r in rows if r["kind"] == "matched"}), 48)

    def test_matched_identity_prefix_slot_suffix_and_byte_budget(self):
        groups = {}
        for r in build_corpus():
            if r["kind"] == "matched": groups.setdefault((r["condition"], r["depth"]), []).append(r)
        for group in groups.values():
            for key in ("task_bytes", "query_bytes", "baseline_bytes", "baseline_source_id", "current_bytes", "current_source_id", "authority", "prefix_hex", "suffix_hex", "current_cue_offset"):
                self.assertEqual(len({r[key] for r in group}), 1, key)
            lengths = set()
            for r in group:
                raw = bytes.fromhex(r["prefix_hex"]) + bytes.fromhex(r["history_slot_hex"]) + bytes.fromhex(r["suffix_hex"])
                self.assertEqual(raw.hex(), r["serialized_context_hex"])
                self.assertEqual(r["history_slot_start"], len(bytes.fromhex(r["prefix_hex"])))
                self.assertEqual(r["history_slot_end"], r["history_slot_start"] + len(bytes.fromhex(r["history_slot_hex"])))
                lengths.add(len(raw))
            self.assertEqual(len(lengths), 1)

    def test_unsupported_is_explicit_unknown(self):
        rows = [r for r in build_corpus() if r["condition"] == "unsupported"]
        self.assertEqual(len(rows), 16)
        self.assertTrue(all(r["outcome"] == "UNKNOWN_UNSUPPORTED" and r["answer"] is None and r["reason"] == "unsupported_field_without_source_evidence" for r in rows))

    def test_position_pair_only_changes_cue_offset(self):
        a, b = [r for r in build_corpus() if r["kind"] == "position_control"]
        self.assertEqual({k for k in a if a[k] != b[k]}, {"current_cue_offset"})

    def test_independent_auditor_accepts_corpus(self):
        result = audit_corpus(build_corpus())
        self.assertEqual((result["result"], result["matched_rows"], result["position_rows"], result["errors"]), ("PASS", 48, 2, []))

    def test_all_eight_mutations_rejected(self):
        for name in ("final_truth", "baseline_identity", "common_byte", "cue_offset", "lineage", "observed_inference", "unknown_answer", "unsupported_omitted"):
            with self.subTest(mutation=name):
                self.assertEqual(audit_corpus(apply_mutation(build_corpus(), name))["result"], "FAIL")

    def test_cli_pass_fail_and_no_overwrite_contract(self):
        root = Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory(prefix="a02-construction-") as tmp:
            tmp = Path(tmp)
            raw, audit = tmp / "raw.json", tmp / "audit.json"
            candidate_cmd = [sys.executable, str(root / "candidate.py"), str(raw)]
            first = subprocess.run(candidate_cmd, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            parsed = json.loads(raw.read_text(encoding="utf-8"))
            self.assertEqual(len(parsed), 50)
            second = subprocess.run(candidate_cmd, capture_output=True, text=True)
            self.assertNotEqual(second.returncode, 0)
            auditor_cmd = [sys.executable, str(root / "auditor.py"), str(raw), str(audit)]
            checked = subprocess.run(auditor_cmd, capture_output=True, text=True)
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertEqual(json.loads(audit.read_text(encoding="utf-8"))["result"], "PASS")
            changed = apply_mutation(parsed, "final_truth")
            bad_raw, bad_audit = tmp / "bad.json", tmp / "bad-audit.json"
            bad_raw.write_text(json.dumps(changed), encoding="utf-8")
            rejected = subprocess.run([sys.executable, str(root / "auditor.py"), str(bad_raw), str(bad_audit)], capture_output=True, text=True)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertEqual(json.loads(bad_audit.read_text(encoding="utf-8"))["result"], "FAIL")
            for name in ("final_truth", "baseline_identity", "common_byte", "cue_offset", "lineage", "observed_inference", "unknown_answer", "unsupported_omitted"):
                mutation_raw, mutation_audit = tmp / f"{name}.json", tmp / f"{name}-audit.json"
                mutation_raw.write_text(json.dumps(apply_mutation(parsed, name)), encoding="utf-8")
                proc = subprocess.run([sys.executable, str(root / "auditor.py"), str(mutation_raw), str(mutation_audit)], capture_output=True, text=True)
                self.assertNotEqual(proc.returncode, 0, name)
                self.assertEqual(json.loads(mutation_audit.read_text(encoding="utf-8"))["result"], "FAIL", name)
            no_overwrite = subprocess.run(auditor_cmd, capture_output=True, text=True)
            self.assertNotEqual(no_overwrite.returncode, 0)

def apply_mutation(rows, name):
    out = copy.deepcopy(rows)
    target = next(r for r in out if r["kind"] == "matched")
    if name == "final_truth": target["final_truth"] = "forged"
    elif name == "baseline_identity":
        target["baseline_source_id"] = "forged/source"
        target["baseline_bytes"] = json.dumps({"value": "old", "source_id": "forged/source"}, separators=(",", ":")).encode().hex()
    elif name == "common_byte": target["prefix_hex"] = ("00" if target["prefix_hex"][:2] != "00" else "01") + target["prefix_hex"][2:]
    elif name == "cue_offset": target["current_cue_offset"] += 1
    elif name == "lineage":
        target = next(r for r in out if r["kind"] == "matched" and r["depth"] == 1)
        target["lineage"] = []
    elif name == "observed_inference":
        target = next(r for r in out if r["arm"] == "SOURCE_LINKED_DELTA" and r["depth"] > 0)
        target["delta_evidence"] = "OBSERVED"
    elif name == "unknown_answer":
        target = next(r for r in out if r["condition"] == "unsupported")
        target["answer"] = "guessed"
    elif name == "unsupported_omitted": out = [r for r in out if r["condition"] != "unsupported"]
    else: raise ValueError(name)
    return out

if __name__ == "__main__":
    unittest.main()
