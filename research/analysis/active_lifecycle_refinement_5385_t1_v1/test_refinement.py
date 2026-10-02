import itertools
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
ALPHABET = (
    "invalidate",
    "trip",
    "start_comp",
    "refresh",
    "effect",
    "retry",
    "compensate",
)


def run_candidate(path):
    return subprocess.run(
        [sys.executable, str(HERE / "experiment.py"), "--output", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def run_auditor(raw_path, audit_path):
    return subprocess.run(
        [
            sys.executable,
            str(HERE / "audit.py"),
            "--raw",
            str(raw_path),
            "--output",
            str(audit_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


class AlternatingRefinementExperimentTests(unittest.TestCase):
    def test_depth_four_agreement_does_not_hide_longer_unsafe_input_sequence(self):
        with tempfile.TemporaryDirectory() as temp:
            raw_path = Path(temp) / "raw.jsonl"
            completed = run_candidate(raw_path)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            records = read_jsonl(raw_path)
        summary = {r["candidate"]: r for r in records if r.get("kind") == "summary"}

        self.assertEqual(set(summary), {"safe", "unsafe_output", "missing_refusal"})
        for candidate in summary.values():
            self.assertTrue(candidate["manual_suite_equal"])
            self.assertEqual(candidate["bounded_depth"], 4)
            self.assertEqual(candidate["bounded_word_count"], 2801)
            self.assertTrue(candidate["bounded_equivalent"])

        unsafe = summary["unsafe_output"]
        self.assertEqual(unsafe["refinement"], "COUNTEREXAMPLE")
        self.assertEqual(
            unsafe["counterexample_inputs"],
            ["invalidate", "retry", "retry", "retry", "effect"],
        )
        self.assertEqual(unsafe["counterexample_kind"], "OUTPUT_OUTSIDE_GUARANTEE")

        silent = summary["missing_refusal"]
        self.assertEqual(silent["refinement"], "COUNTEREXAMPLE")
        self.assertEqual(
            silent["counterexample_inputs"],
            ["invalidate", "retry", "retry", "retry", "retry"],
        )
        self.assertEqual(silent["counterexample_kind"], "MISSING_EXPLICIT_REFUSAL")
        self.assertEqual(summary["safe"]["refinement"], "REFINES")

    def test_candidate_records_every_word_in_the_fixed_depth_four_domain(self):
        expected_words = {
            word
            for size in range(5)
            for word in itertools.product(ALPHABET, repeat=size)
        }
        with tempfile.TemporaryDirectory() as temp:
            raw_path = Path(temp) / "raw.jsonl"
            completed = run_candidate(raw_path)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            records = read_jsonl(raw_path)

        traces = [r for r in records if r.get("kind") == "trace"]
        for candidate in ("safe", "unsafe_output", "missing_refusal"):
            actual = {
                tuple(r["input"])
                for r in traces
                if r["candidate"] == candidate
            }
            self.assertEqual(actual, expected_words)

    def test_independent_auditor_accepts_the_candidate_and_rejects_raw_corruption(self):
        with tempfile.TemporaryDirectory() as temp:
            raw_path = Path(temp) / "raw.jsonl"
            audit_path = Path(temp) / "audit.json"
            generated = run_candidate(raw_path)
            self.assertEqual(generated.returncode, 0, generated.stderr)

            audited = run_auditor(raw_path, audit_path)
            self.assertEqual(audited.returncode, 0, audited.stderr)
            result = json.loads(audit_path.read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "PASS_BOUNDED_ALTERNATING_REFINEMENT")
            self.assertEqual(result["candidate_count"], 3)
            self.assertEqual(result["bounded_words_per_candidate"], 2801)
            self.assertTrue(all(result["mutation_controls"].values()))

            records = read_jsonl(raw_path)
            corrupted = next(
                r for r in records
                if r.get("kind") == "trace"
                and r.get("candidate") == "safe"
                and r.get("input") == ["effect"]
            )
            corrupted["candidate_outputs"] = [["REFUSED"]]
            raw_path.write_text(
                "".join(json.dumps(r, sort_keys=True) + "\n" for r in records),
                encoding="utf-8",
            )
            rejected = run_auditor(raw_path, audit_path)
            self.assertEqual(rejected.returncode, 1)
            failed = json.loads(audit_path.read_text(encoding="utf-8"))
            self.assertEqual(failed["status"], "FAIL_OR_STOP")
            self.assertTrue(failed["errors"])


if __name__ == "__main__":
    unittest.main()
