import copy
import hashlib
import json
from pathlib import Path


SRC = Path("/src")
EVIDENCE = Path("/evidence")
OUT = Path("/audit/AUDIT.json")
AUDIT = Path("/audit")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def parse_inventory(prefix):
    if prefix == "postflight":
        base, stem = EVIDENCE / "postflight", "preflight"
    else:
        base, stem = EVIDENCE, prefix
    receipt = load_json(base / f"{stem}-list.capture.json")
    raw = (base / f"{stem}-list.stdout.bin").read_bytes()
    stderr = (base / f"{stem}-list.stderr.bin").read_bytes()
    assert receipt["exit_code"] == 0
    assert receipt["stdout_bytes"] == len(raw)
    assert receipt["stderr_bytes"] == len(stderr)
    assert receipt["stdout_sha256"] == hashlib.sha256(raw).hexdigest()
    assert receipt["stderr_sha256"] == hashlib.sha256(stderr).hexdigest()
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    assert all(type(row) is dict and type(row.get("State")) is str for row in rows)
    return receipt, rows


def validate(bundle):
    red = bundle["red"]
    green = bundle["green"]
    pre = bundle["preflight"]
    post = bundle["postflight"]
    assert red["disposition"] == "EXPECTED_RED"
    assert red["test"] == "test_input_edge_receipt_rejects_unknown_outer_adapter_rows"
    assert red["cases"] == 3 and red["failures"] == 3 and red["errors"] == 0
    assert green["disposition"] == "PASS"
    assert green["test"] == red["test"]
    assert green["cases"] == 3 and green["failures"] == 0 and green["errors"] == 0
    assert green["py_compile"] == "PASS"
    expected_cases = ("unknown_duplicate_down", "unknown_duplicate_up",
                      "unknown_only_measurement")
    assert all(f"case='{case}'" in red["transcript"] for case in expected_cases)
    assert all("FAIL" in red["transcript"].split(f"case='{case}'", 1)[1].splitlines()[0]
               for case in expected_cases)
    assert "Ran 1 test" in red["transcript"] and "FAILED (failures=3)" in red["transcript"]
    assert "... ok" in green["transcript"] and "Ran 1 test" in green["transcript"]
    assert "OK" in green["transcript"] and "FAIL" not in green["transcript"]
    assert pre["start_gate"] == "CLEAR" and pre["parse_errors"] == []
    assert pre["nonterminal_rows"] == [] and pre["rows_parsed"] == 205
    assert post["start_gate"] == "CLEAR" and post["parse_errors"] == []
    assert post["nonterminal_rows"] == [] and post["rows_parsed"] == 205
    assert bundle["preflight_ids"] == bundle["postflight_ids"]
    assert bundle["red_exit"] == 0 and bundle["green_exit"] == 1
    assert bundle["green_a02_exit"] == 0
    assert "frozen source_sha256 mismatch" in bundle["green_a02_log"]
    assert bundle["green_a02_result_exists"] is False
    assert "swap limit capabilities" in bundle["red_log"]
    assert "swap limit capabilities" in bundle["green_log"]
    assert "swap limit capabilities" in bundle["green_a02_log"]
    return True


freeze = load_json(SRC / "audit_freeze_a05.json")
assert freeze["auditor_sha256"] == sha(SRC / "audit_raw_a05.py")
for rel, digest in freeze["sha256"].items():
    if rel.startswith("raw/"):
        path = EVIDENCE / rel.removeprefix("raw/")
    elif rel.startswith("audit-a05/"):
        path = AUDIT / rel.removeprefix("audit-a05/")
    else:
        path = SRC / rel
    assert sha(path) == digest, f"hash mismatch: {rel}"

red_freeze = load_json(SRC / "red_freeze.json")
green_freeze = load_json(SRC / "green_freeze_a02.json")
red_result = load_json(EVIDENCE / "red-result.json")
green_result = load_json(EVIDENCE / "green-a02-result.json")
for result, result_freeze in ((red_result, red_freeze), (green_result, green_freeze)):
    for key in ("source_sha256", "test_sha256", "fixture_sha256", "runner_sha256"):
        assert result[key] == result_freeze["sha256"][key]
assert sha(SRC / "controller.py") == red_freeze["sha256"]["source_sha256"]
assert sha(SRC / "candidate_controller.py") == green_freeze["sha256"]["source_sha256"]
assert sha(SRC / "test_map01_v39_typed_state_feedback.py") == green_freeze["sha256"]["test_sha256"]
assert sha(SRC / "run_unknown_outer.py") == green_freeze["sha256"]["runner_sha256"]
preflight, pre_rows = parse_inventory("preflight")
postflight, post_rows = parse_inventory("postflight")
audit_pre_dir = AUDIT / "preflight"
audit_pre = load_json(audit_pre_dir / "preflight-list.capture.json")
audit_pre_raw = (audit_pre_dir / "preflight-list.stdout.bin").read_bytes()
audit_pre_stderr = (audit_pre_dir / "preflight-list.stderr.bin").read_bytes()
assert audit_pre["exit_code"] == 0
assert audit_pre["stdout_bytes"] == len(audit_pre_raw)
assert audit_pre["stderr_bytes"] == len(audit_pre_stderr)
assert audit_pre["stdout_sha256"] == hashlib.sha256(audit_pre_raw).hexdigest()
assert audit_pre["stderr_sha256"] == hashlib.sha256(audit_pre_stderr).hexdigest()
audit_pre_rows = [json.loads(line) for line in audit_pre_raw.decode("utf-8").splitlines() if line.strip()]
assert all(type(row) is dict and type(row.get("State")) is str for row in audit_pre_rows)
assert audit_pre["start_gate"] == "CLEAR" and audit_pre["parse_errors"] == []
assert audit_pre["nonterminal_rows"] == []
red_ids = sorted(row["ID"] for row in pre_rows)
post_ids = sorted(row["ID"] for row in post_rows)
bundle = {
    "red": red_result,
    "green": green_result,
    "preflight": preflight,
    "postflight": postflight,
    "preflight_ids": red_ids,
    "postflight_ids": post_ids,
    "audit_preflight": audit_pre,
    "red_exit": int((EVIDENCE / "red-exit-code.txt").read_text().strip()),
    "green_exit": int((EVIDENCE / "green-exit-code.txt").read_text().strip()),
    "green_a02_exit": int((EVIDENCE / "green-a02-exit-code.txt").read_text().strip()),
    "green_log": (EVIDENCE / "green-a02-container.log").read_text(encoding="utf-8"),
    "red_log": (EVIDENCE / "red-container.log").read_text(encoding="utf-8"),
    "green_a02_log": (EVIDENCE / "green-container.log").read_text(encoding="utf-8"),
    "green_a02_result_exists": (EVIDENCE / "green-result.json").exists(),
}
validate(bundle)

mutations = []
for label, change in (
    ("green_source_hash", lambda x: x["green"].__setitem__("source_sha256", "0" * 64)),
    ("green_disposition", lambda x: x["green"].__setitem__("disposition", "FAIL")),
    ("red_failure_count", lambda x: x["red"].__setitem__("failures", 0)),
):
    changed = copy.deepcopy(bundle)
    change(changed)
    try:
        validate(changed)
    except (AssertionError, KeyError, TypeError):
        mutations.append({"mutation": label, "disposition": "REJECTED"})
    else:
        mutations.append({"mutation": label, "disposition": "FALSE_ACCEPT"})
assert all(row["disposition"] == "REJECTED" for row in mutations)

checks = [
    "audit source hash pinned",
    "baseline controller/test/fixture/runner hashes pinned",
    "corrected controller/test/fixture/runner hashes pinned",
    "preflight stdout/stderr byte hashes verified",
    "preflight inventory fully parsed and terminal",
    "postflight stdout/stderr byte hashes verified",
    "postflight inventory fully parsed and terminal",
    "preflight/postflight container ID sets identical",
    "baseline expected red: exactly three assertion failures, zero errors",
    "corrected candidate: one method, three cases, zero failures/errors",
    "baseline and candidate compilation recorded pass",
    "freeze-transcription stop retained separately from test outcome",
    "requested swap-limit warning retained; no swap-bound claim",
    "three audit mutation controls rejected",
    "auditor preflight inventory clear and byte hashes verified",
]
report = {
    "disposition": "PASS_SCOPED_RAW_AUDIT",
    "checks": len(checks),
    "checklist": checks,
    "mutation_controls": mutations,
    "scientific_scope": "deterministic pure-projector construction on one retained synthetic trace",
    "not_established": [
        "live X-server key release or physical dwell",
        "application consumption",
        "useful task effect, recovery benefit, or MAP01 completion",
    ],
    "resource_note": "WSLc warned swap limit capabilities are unavailable; configured memory is not treated as swap-bounded.",
    "source_sha256": green_result["source_sha256"],
    "test_sha256": green_result["test_sha256"],
    "fixture_sha256": green_result["fixture_sha256"],
    "auditor_preflight_rows": audit_pre["rows_parsed"],
    "result_sha256": {
        "red": sha(EVIDENCE / "red-result.json"),
        "green": sha(EVIDENCE / "green-a02-result.json"),
    },
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
