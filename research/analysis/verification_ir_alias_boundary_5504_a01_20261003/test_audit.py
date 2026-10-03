"""Independent construction fixtures; these are not formal producer outputs.

Each corruption names a validation break and must change the raw artifact.
Expected worlds below are hand-declared; no auditor builder supplies them.
The only mocked boundary is a CLI fixture file read, since construction must
not write fixture files outside the authorized raw-stream capture directories.
"""

import copy
import hashlib
import importlib
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch


try:
    AUDITOR = importlib.import_module("audit")
except ModuleNotFoundError as error:
    if error.name != "audit":
        raise
    AUDITOR = None


# Literal, independently checked valuation/label pairs in case-ID order.
WORLDS = (
    ("00000", "FAIL"), ("00001", "FAIL"),
    ("00010", "FAIL"), ("00011", "FAIL"),
    ("00100", "FAIL"), ("00101", "FAIL"),
    ("00110", "FAIL"), ("00111", "FAIL"),
    ("01000", "FAIL"), ("01001", "FAIL"),
    ("01010", "FAIL"), ("01011", "FAIL"),
    ("01100", "FAIL"), ("01101", "FAIL"),
    ("01110", "FAIL"), ("01111", "FAIL"),
    ("10000", "FAIL"), ("10001", "FAIL"),
    ("10010", "FAIL"), ("10011", "FAIL"),
    ("10100", "FAIL"), ("10101", "FAIL"),
    ("10110", "FAIL"), ("10111", "FAIL"),
    ("11000", "FAIL"), ("11001", "FAIL"),
    ("11010", "FAIL"), ("11011", "FAIL"),
    ("11100", "FAIL"), ("11101", "FAIL"),
    ("11110", "FAIL"), ("11111", "PASS"),
)
PREDICATES = [
    "authority", "current", "effect_safe", "dependencies_acyclic", "reversible"
]
REPORT_KEYS = {
    "status", "errors", "rows_checked", "observable_classes_restricted",
    "conflicting_classes", "complete_decisions", "input_sha256",
}


def fixture():
    """Build serialization scaffolding around literal worlds and predictions."""
    rows = [
        {"case_id": f"case_{index:03d}",
         "concrete": [character == "1" for character in vector],
         "required": label}
        for index, (vector, label) in enumerate(WORLDS)
    ]
    return {
        "schema": "verification-ir-alias-boundary-v1",
        "predicates": list(PREDICATES),
        "oracle": "PASS iff all five predicates are true",
        "rows": rows,
        "restricted": {
            "vocabulary": PREDICATES[:4],
            "status": "ONTOLOGY_INSUFFICIENT",
            "observable_class_count": 16,
            "conflicting_classes": [{
                "visible": [True, True, True, True],
                "members": ["case_030", "case_031"],
                "required": ["FAIL", "PASS"],
            }],
            "decisions": None,
        },
        "complete": {
            "vocabulary": list(PREDICATES),
            "status": "EXPRESSIBLE",
            "observable_class_count": 32,
            "conflicting_classes": [],
            "decisions": [
                {"visible": list(row["concrete"]), "required": row["required"]}
                for row in rows
            ],
        },
    }


def encode(document):
    return json.dumps(document, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def replace(path, value):
    def corrupt(document):
        parent = document
        for key in path[:-1]:
            parent = parent[key]
        parent[path[-1]] = copy.deepcopy(value)
    return corrupt


def remove(path):
    def corrupt(document):
        parent = document
        for key in path[:-1]:
            parent = parent[key]
        del parent[path[-1]]
    return corrupt


def append(path, value):
    def corrupt(document):
        target = document
        for key in path:
            target = target[key]
        target.append(copy.deepcopy(value))
    return corrupt


def reverse(path):
    def corrupt(document):
        target = document
        for key in path:
            target = target[key]
        target.reverse()
    return corrupt


# These cases expose accepting approximate structure, coerced types, unretained
# witnesses, forged convergence, and a complete table inconsistent with worlds.
ARTIFACT_CORRUPTIONS = (
    ("schema_label", replace(("schema",), "verification-ir-alias-boundary-v2")),
    ("schema_type", replace(("schema",), 1)),
    ("oracle_label", replace(("oracle",), "PASS iff reversible is true")),
    ("extra_top_key", replace(("converged",), True)),
    ("missing_top_key", remove(("oracle",))),
    ("predicate_order", reverse(("predicates",))),
    ("hidden_id_predicate", append(("predicates",), "case_id")),
    ("missing_predicate", remove(("predicates", 4))),
    ("missing_world", remove(("rows", 7))),
    ("duplicate_world", replace(("rows", 7), fixture()["rows"][6])),
    ("extra_world", append(("rows",), fixture()["rows"][31])),
    ("reordered_worlds", reverse(("rows",))),
    ("rows_object", replace(("rows",), {})),
    ("case_id_type", replace(("rows", 0, "case_id"), 0)),
    ("case_id_padding", replace(("rows", 0, "case_id"), "case_0")),
    ("extra_row_key", replace(("rows", 0, "observed_id"), "case_000")),
    ("missing_row_key", remove(("rows", 0, "required"))),
    ("wrong_concrete_bit", replace(("rows", 0, "concrete", 0), True)),
    ("concrete_bool_int_false", replace(("rows", 0, "concrete", 0), 0)),
    ("concrete_bool_int_true", replace(("rows", 31, "concrete", 4), 1)),
    ("concrete_bool_float", replace(("rows", 0, "concrete", 0), 0.0)),
    ("concrete_bool_string", replace(("rows", 0, "concrete", 0), "false")),
    ("short_concrete", remove(("rows", 0, "concrete", 4))),
    ("long_concrete", append(("rows", 0, "concrete"), False)),
    ("lost_fail_witness_label", replace(("rows", 30, "required"), "PASS")),
    ("lost_pass_witness_label", replace(("rows", 31, "required"), "FAIL")),
    ("unexpected_pass_world", replace(("rows", 0, "required"), "PASS")),
    ("lowercase_label", replace(("rows", 0, "required"), "fail")),
    ("restricted_hidden_id", append(("restricted", "vocabulary"), "case_id")),
    ("restricted_reversible", append(("restricted", "vocabulary"), "reversible")),
    ("restricted_vocabulary_order", reverse(("restricted", "vocabulary"))),
    ("restricted_missing_vocabulary", remove(("restricted", "vocabulary", 2))),
    ("restricted_false_convergence", replace(("restricted", "status"), "EXPRESSIBLE")),
    ("restricted_unknown_status", replace(("restricted", "status"), "CONVERGED")),
    ("restricted_wrong_count", replace(("restricted", "observable_class_count"), 15)),
    ("restricted_float_count", replace(("restricted", "observable_class_count"), 16.0)),
    ("restricted_bool_count", replace(("restricted", "observable_class_count"), True)),
    ("restricted_extra_key", replace(("restricted", "case_id"), "case_031")),
    ("restricted_missing_key", remove(("restricted", "status"))),
    ("lost_conflict", replace(("restricted", "conflicting_classes"), [])),
    ("duplicate_conflict", append(("restricted", "conflicting_classes"), fixture()["restricted"]["conflicting_classes"][0])),
    ("wrong_visible_witness", replace(("restricted", "conflicting_classes", 0, "visible", 0), False)),
    ("visible_bool_int", replace(("restricted", "conflicting_classes", 0, "visible", 0), 1)),
    ("short_visible_witness", remove(("restricted", "conflicting_classes", 0, "visible", 3))),
    ("lost_witness_member", remove(("restricted", "conflicting_classes", 0, "members", 0))),
    ("duplicate_witness_member", replace(("restricted", "conflicting_classes", 0, "members", 1), "case_030")),
    ("witness_member_order", reverse(("restricted", "conflicting_classes", 0, "members"))),
    ("unrelated_witness_member", replace(("restricted", "conflicting_classes", 0, "members", 0), "case_028")),
    ("lost_witness_label", remove(("restricted", "conflicting_classes", 0, "required", 0))),
    ("witness_label_order", reverse(("restricted", "conflicting_classes", 0, "required"))),
    ("duplicate_witness_label", append(("restricted", "conflicting_classes", 0, "required"), "PASS")),
    ("extra_conflict_key", replace(("restricted", "conflicting_classes", 0, "decision"), "PASS")),
    ("missing_conflict_key", remove(("restricted", "conflicting_classes", 0, "members"))),
    ("restricted_empty_decisions", replace(("restricted", "decisions"), [])),
    ("restricted_forged_decisions", replace(("restricted", "decisions"), [{"visible": [True] * 4, "required": "PASS"}])),
    ("complete_missing_predicate", remove(("complete", "vocabulary", 4))),
    ("complete_hidden_id", append(("complete", "vocabulary"), "case_id")),
    ("complete_vocabulary_order", reverse(("complete", "vocabulary"))),
    ("complete_wrong_status", replace(("complete", "status"), "ONTOLOGY_INSUFFICIENT")),
    ("complete_wrong_count", replace(("complete", "observable_class_count"), 31)),
    ("complete_float_count", replace(("complete", "observable_class_count"), 32.0)),
    ("complete_forged_conflict", append(("complete", "conflicting_classes"), fixture()["restricted"]["conflicting_classes"][0])),
    ("complete_extra_key", replace(("complete", "converged"), True)),
    ("complete_missing_key", remove(("complete", "observable_class_count"))),
    ("complete_null_decisions", replace(("complete", "decisions"), None)),
    ("complete_missing_decision", remove(("complete", "decisions", 0))),
    ("complete_duplicate_decision", replace(("complete", "decisions", 1), fixture()["complete"]["decisions"][0])),
    ("complete_extra_decision", append(("complete", "decisions"), fixture()["complete"]["decisions"][31])),
    ("complete_reordered_decisions", reverse(("complete", "decisions"))),
    ("complete_wrong_visible", replace(("complete", "decisions", 0, "visible", 0), True)),
    ("complete_visible_bool_int", replace(("complete", "decisions", 0, "visible", 0), 0)),
    ("complete_wrong_fail_label", replace(("complete", "decisions", 0, "required"), "PASS")),
    ("complete_wrong_pass_label", replace(("complete", "decisions", 31, "required"), "FAIL")),
    ("complete_decision_hidden_id", replace(("complete", "decisions", 0, "case_id"), "case_000")),
    ("complete_decision_missing_key", remove(("complete", "decisions", 0, "required"))),
)


def alter_token(old, new):
    def corrupt(raw):
        if old not in raw:
            raise AssertionError("corruption token is absent")
        return raw.replace(old, new, 1)
    return corrupt


# Keep duplicate keys at multiple depths even when both values are identical.
RAW_CORRUPTIONS = (
    ("duplicate_top_key", alter_token(b'{"schema":', b'{"schema":"verification-ir-alias-boundary-v1","schema":')),
    ("duplicate_row_key", alter_token(b'"case_id":"case_000"', b'"case_id":"case_000","case_id":"case_000"')),
    ("duplicate_control_key", alter_token(b'"observable_class_count":16', b'"observable_class_count":16,"observable_class_count":16')),
    ("duplicate_conflict_key", alter_token(b'"members":["case_030","case_031"]', b'"members":["case_030","case_031"],"members":["case_030","case_031"]')),
    ("duplicate_decision_key", alter_token(b'{"visible":[false,false,false,false,false],"required":"FAIL"}', b'{"visible":[false,false,false,false,false],"required":"FAIL","required":"FAIL"}')),
    ("escaped_duplicate_key", alter_token(b'{"schema":', b'{"\\u0073chema":"verification-ir-alias-boundary-v1","schema":')),
    ("nan_constant", alter_token(b'"observable_class_count":16', b'"observable_class_count":NaN')),
    ("positive_infinity", alter_token(b'"observable_class_count":16', b'"observable_class_count":Infinity')),
    ("negative_infinity", alter_token(b'"observable_class_count":16', b'"observable_class_count":-Infinity')),
    ("float_overflow", alter_token(b'"observable_class_count":16', b'"observable_class_count":1e9999')),
    ("truncated_document", lambda raw: raw[:-1]),
    ("trailing_document", lambda raw: raw + b' {}'),
    ("invalid_utf8", lambda raw: raw + b'\xff'),
    ("root_array", lambda raw: b'[' + raw + b']'),
    ("root_null", lambda raw: b'null'),
    ("empty_bytes", lambda raw: b''),
    ("excessive_nesting", lambda raw: b'[' * 1500 + b'0' + b']' * 1500),
)


class AuditContractTests(unittest.TestCase):
    def setUp(self):
        # RED against an absent implementation is a clear assertion failure,
        # not an import error that could conceal broken fixture setup.
        self.assertIsNotNone(AUDITOR, "audit.py / audit_bytes is not implemented")
        self.assertTrue(callable(getattr(AUDITOR, "audit_bytes", None)))
        self.raw = encode(fixture())

    def assert_report(self, result, raw, status):
        self.assertIs(type(result), dict)
        self.assertEqual(set(result), REPORT_KEYS)
        self.assertEqual(result["status"], status)
        self.assertIs(type(result["errors"]), list)
        self.assertTrue(all(type(message) is str and message for message in result["errors"]))
        self.assertEqual(result["input_sha256"], hashlib.sha256(raw).hexdigest())
        for name, upper in (
            ("rows_checked", 32), ("observable_classes_restricted", 16),
            ("conflicting_classes", 1), ("complete_decisions", 32),
        ):
            self.assertIs(type(result[name]), int)
            self.assertGreaterEqual(result[name], 0)
            self.assertLessEqual(result[name], upper)
        if status == "FAIL":
            self.assertTrue(result["errors"], "FAIL must explain a validation error")

    def test_accepts_independent_fixture_with_exact_schema_metrics(self):
        self.assertEqual(AUDITOR.audit_bytes(self.raw), {
            "status": "PASS", "errors": [], "rows_checked": 32,
            "observable_classes_restricted": 16, "conflicting_classes": 1,
            "complete_decisions": 32,
            "input_sha256": hashlib.sha256(self.raw).hexdigest(),
        })

    def test_accepts_json_whitespace_and_object_key_order(self):
        document = dict(reversed(list(fixture().items())))
        raw = (" \n" + json.dumps(document, indent=2, sort_keys=True) + "\n\t").encode()
        self.assertNotEqual(raw, self.raw)
        result = AUDITOR.audit_bytes(raw)
        self.assert_report(result, raw, "PASS")
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["rows_checked"], 32)

    def test_independent_calls_do_not_reuse_invalid_state(self):
        invalid = self.raw[:-1]
        self.assert_report(AUDITOR.audit_bytes(invalid), invalid, "FAIL")
        self.assert_report(AUDITOR.audit_bytes(self.raw), self.raw, "PASS")

    def test_invalid_input_has_no_verified_model_counts(self):
        result = AUDITOR.audit_bytes(b"{")
        self.assert_report(result, b"{", "FAIL")
        for name in ("rows_checked", "observable_classes_restricted", "conflicting_classes", "complete_decisions"):
            self.assertEqual(result[name], 0)

    def test_cli_fixture_pass_is_json_and_exit_zero(self):
        # Reading bytes is the only external side effect of main. Patch that
        # boundary for the fixture; execute the real parser, auditor and output.
        output = io.StringIO()
        with patch.object(Path, "read_bytes", return_value=self.raw), patch("sys.stdout", output):
            code = AUDITOR.main(["independent-construction-fixture.json"])
        self.assertEqual(code, 0)
        self.assert_report(json.loads(output.getvalue()), self.raw, "PASS")

    def test_cli_fixture_fail_is_json_and_exit_one(self):
        raw = self.raw[:-1]
        output = io.StringIO()
        with patch.object(Path, "read_bytes", return_value=raw), patch("sys.stdout", output):
            code = AUDITOR.main(["independent-construction-fixture.json"])
        self.assertEqual(code, 1)
        self.assert_report(json.loads(output.getvalue()), raw, "FAIL")

    def test_cli_read_error_is_json_and_exit_one(self):
        output = io.StringIO()
        with patch.object(Path, "read_bytes", side_effect=OSError("fixture read unavailable")), patch("sys.stdout", output):
            code = AUDITOR.main(["independent-construction-fixture.json"])
        self.assertEqual(code, 1)
        result = json.loads(output.getvalue())
        self.assertEqual(set(result), REPORT_KEYS)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(result["errors"])
        self.assertIsNone(result["input_sha256"])

    def test_real_cli_reads_source_as_invalid_json_without_modification(self):
        # A Python source file is deliberately not a formal artifact.
        source = Path(__file__).resolve()
        before = source.read_bytes()
        process = subprocess.run(
            [sys.executable, "-B", str(Path(AUDITOR.__file__).resolve()), str(source)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=10,
        )
        self.assertEqual(process.returncode, 1)
        self.assertEqual(process.stderr, b"")
        self.assert_report(json.loads(process.stdout), before, "FAIL")
        self.assertEqual(source.read_bytes(), before)


def artifact_test(corrupt):
    def test(self):
        document = fixture()
        corrupt(document)
        raw = encode(document)
        self.assertNotEqual(raw, self.raw, "corruption must actually change artifact bytes")
        self.assert_report(AUDITOR.audit_bytes(raw), raw, "FAIL")
    return test


def raw_test(corrupt):
    def test(self):
        raw = corrupt(self.raw)
        self.assertNotEqual(raw, self.raw, "corruption must actually change artifact bytes")
        self.assert_report(AUDITOR.audit_bytes(raw), raw, "FAIL")
    return test


for case_name, mutation in ARTIFACT_CORRUPTIONS:
    setattr(AuditContractTests, "test_corruption_" + case_name, artifact_test(mutation))
for case_name, mutation in RAW_CORRUPTIONS:
    setattr(AuditContractTests, "test_corruption_" + case_name, raw_test(mutation))


if __name__ == "__main__":
    unittest.main(verbosity=2)
