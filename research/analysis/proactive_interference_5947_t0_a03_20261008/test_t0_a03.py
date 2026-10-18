"""CLI contract and frozen-defect regressions for the A03 fixture method."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent
CANDIDATE = ROOT / "candidate.py"
AUDITOR = ROOT / "auditor.py"
CURRENT = b"CURRENT"


def run_cli(script, *args):
    return subprocess.run(
        [sys.executable, "-B", str(script), *(str(arg) for arg in args)],
        capture_output=True,
        text=True,
        timeout=15,
        cwd=script.parent,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": ""},
    )


def make_raw(directory):
    raw_path = directory / "candidate.json"
    result = run_cli(CANDIDATE, raw_path)
    if result.returncode != 0:
        raise AssertionError(f"candidate failed ({result.returncode}): {result.stderr}")
    return raw_path, json.loads(raw_path.read_text(encoding="utf-8"))


def write_mutation(directory, rows, name):
    path = directory / f"{name}.json"
    path.write_text(json.dumps(rows, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return path


class CandidateCliTests(unittest.TestCase):
    def test_emits_fifty_rows_with_exact_seven_byte_position_cues(self):
        with tempfile.TemporaryDirectory() as temp:
            raw_path, rows = make_raw(Path(temp))

            self.assertEqual(len(rows), 50)
            matched = [row for row in rows if row.get("kind") == "matched"]
            positions = [row for row in rows if row.get("kind") == "position_control"]
            self.assertEqual(len(matched), 48)
            self.assertEqual(len(positions), 2)

            groups = {}
            for row in matched:
                groups.setdefault((row["condition"], row["depth"]), []).append(row)
            self.assertEqual(len(groups), 12)
            for group in groups.values():
                self.assertEqual({row["arm"] for row in group}, {
                    "CURRENT_ONLY", "FULL_CONFLICTING_HISTORY",
                    "NONCONFLICTING_HISTORY", "SOURCE_LINKED_DELTA",
                })
                for field in ("task_bytes", "query_bytes", "baseline_bytes", "baseline_source_id",
                              "current_bytes", "current_source_id", "authority", "prefix_hex",
                              "suffix_hex", "current_cue_offset", "cue_byte_length", "final_truth",
                              "outcome", "answer", "reason"):
                    self.assertEqual(len({row.get(field) for row in group}), 1, field)
                self.assertEqual({len(bytes.fromhex(row["history_slot_hex"])) for row in group}, {2048})
                self.assertEqual(len({len(bytes.fromhex(row["serialized_context_hex"])) for row in group}), 1)

            offsets = []
            for row in positions:
                prefix = bytes.fromhex(row["prefix_hex"])
                offset = row["current_cue_offset"]
                length = row["cue_byte_length"]
                self.assertEqual(length, 7)
                self.assertEqual(prefix[offset:offset + length], CURRENT)
                self.assertEqual(row["serialized_context_hex"],
                                 (prefix + bytes.fromhex(row["history_slot_hex"]) +
                                  bytes.fromhex(row["suffix_hex"])).hex())
                offsets.append(offset)
            self.assertEqual(offsets, [9, 26])
            differences = {key for key in set(positions[0]) | set(positions[1])
                           if positions[0].get(key) != positions[1].get(key)}
            self.assertEqual(differences, {"current_cue_offset"})

    def test_candidate_refuses_to_overwrite_existing_output(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "occupied.json"
            original = b"keep-existing-bytes\n"
            output.write_bytes(original)
            result = run_cli(CANDIDATE, output)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(output.read_bytes(), original)


class AuditorCliTests(unittest.TestCase):
    def test_auditor_passes_valid_corpus_and_rejects_all_sixteen_mutations(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            _, valid_rows = make_raw(directory)
            valid_result_path = directory / "valid-audit.json"
            valid = run_cli(AUDITOR, directory / "candidate.json", valid_result_path)
            self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)
            self.assertEqual(json.loads(valid_result_path.read_text(encoding="utf-8"))["result"], "PASS")

            isolated = directory / "auditor-only"
            isolated.mkdir()
            isolated_script = isolated / "auditor.py"
            isolated_script.write_bytes(AUDITOR.read_bytes())
            isolated_raw = isolated / "raw.json"
            isolated_raw.write_bytes((directory / "candidate.json").read_bytes())
            isolated_result = isolated / "result.json"
            isolated_run = run_cli(isolated_script, isolated_raw, isolated_result)
            self.assertEqual(isolated_run.returncode, 0, isolated_run.stdout + isolated_run.stderr)
            self.assertEqual(json.loads(isolated_result.read_text(encoding="utf-8"))["result"], "PASS")

            def first(rows, kind, **match):
                return next(row for row in rows if row.get("kind") == kind and
                            all(row.get(key) == value for key, value in match.items()))

            mutations = []

            rows = copy.deepcopy(valid_rows)
            first(rows, "matched")["final_truth"] = "forged"
            mutations.append(("final-truth", rows))

            rows = copy.deepcopy(valid_rows)
            first(rows, "matched")["baseline_source_id"] = "forged/source"
            mutations.append(("baseline-source", rows))

            rows = copy.deepcopy(valid_rows)
            target = first(rows, "matched")
            prefix = bytearray.fromhex(target["prefix_hex"])
            prefix[0] ^= 1
            target["prefix_hex"] = bytes(prefix).hex()
            mutations.append(("common-prefix-byte", rows))

            rows = copy.deepcopy(valid_rows)
            first(rows, "matched")["current_cue_offset"] += 1
            mutations.append(("matched-cue-offset", rows))

            rows = copy.deepcopy(valid_rows)
            target = first(rows, "matched", depth=1)
            target["lineage"] = []
            mutations.append(("episode-lineage", rows))

            rows = copy.deepcopy(valid_rows)
            target = first(rows, "matched", arm="SOURCE_LINKED_DELTA", depth=1)
            target["delta_evidence"] = "OBSERVED"
            mutations.append(("inferred-as-observed", rows))

            rows = copy.deepcopy(valid_rows)
            target = first(rows, "matched", condition="unsupported")
            target["outcome"] = "SYNTHETIC_SUPPORTED"
            target["answer"] = "guessed-value"
            mutations.append(("unknown-to-concrete", rows))

            rows = [row for row in copy.deepcopy(valid_rows) if row.get("condition") != "unsupported"]
            mutations.append(("omit-unsupported-query", rows))

            rows = copy.deepcopy(valid_rows)
            first(rows, "position_control")["cue_byte_length"] = 9
            mutations.append(("quoted-cue-length", rows))

            rows = copy.deepcopy(valid_rows)
            for target in (row for row in rows if row.get("kind") == "position_control"):
                target["allocation"] = "forged-allocation"
                target["baseline_bytes"] = b"not-json".hex()
                target["current_bytes"] = b"not-json".hex()
                target["authority"] = "input-authority"
                target["serialized_context_hex"] = b"not-the-context".hex()
            mutations.append(("same-invalid-position-rows", rows))

            rows = copy.deepcopy(valid_rows)
            group = [row for row in rows if row.get("kind") == "matched" and
                     row.get("condition") == "current_value" and row.get("depth") == 0]
            for target in group:
                target["current_source_id"] = "forged/current-source"
            mutations.append(("shared-forged-current-source", rows))

            rows = copy.deepcopy(valid_rows)
            for target in rows:
                if target.get("kind") == "matched" and target.get("condition") == "current_value" and target.get("depth") == 1:
                    target["depth"] = True
            mutations.append(("boolean-depth-alias", rows))

            rows = copy.deepcopy(valid_rows)
            for target in rows:
                if target.get("kind") == "matched" and target.get("condition") == "current_value" and target.get("depth") == 1:
                    target["lineage"] = [False]
            mutations.append(("boolean-lineage-alias", rows))

            rows = copy.deepcopy(valid_rows)
            alternate_baseline = b'{"value":"old","source_id":"baseline/source-17"}'.hex()
            alternate_current = b'{"value":"new","source_id":"current/source-22"}'.hex()
            for target in rows:
                target["baseline_bytes"] = alternate_baseline
                target["current_bytes"] = alternate_current
            mutations.append(("semantically-equal-reserialized-objects", rows))

            rows = copy.deepcopy(valid_rows)
            for target in rows:
                target["grants_input_authority"] = True
            mutations.append(("unexpected-authority-field", rows))

            rows = copy.deepcopy(valid_rows)
            first(rows, "matched", condition="current_value").pop("reason")
            mutations.append(("missing-explicit-null-field", rows))

            self.assertEqual(len(mutations), 16)
            for name, rows in mutations:
                with self.subTest(mutation=name):
                    raw_path = write_mutation(directory, rows, name)
                    audit_path = directory / f"{name}-audit.json"
                    result = run_cli(AUDITOR, raw_path, audit_path)
                    self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                    audit = json.loads(audit_path.read_text(encoding="utf-8"))
                    self.assertEqual(audit["result"], "FAIL")
                    self.assertTrue(audit["errors"], name)

            occupied = directory / "valid-audit.json"
            original = occupied.read_bytes()
            second = run_cli(AUDITOR, directory / "candidate.json", occupied)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(occupied.read_bytes(), original)


if __name__ == "__main__":
    unittest.main(verbosity=2)
