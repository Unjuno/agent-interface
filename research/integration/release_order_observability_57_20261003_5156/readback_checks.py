"""Post-execution byte/provenance checks, without importing or rerunning an assay.

Written after A01. This is not a prospectively frozen scientific input.
The optional private directory checks original capture bytes on the author's host;
an independent public export can verify the remaining checks without that directory.
"""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess


PROSPECTIVE = "676187138bad090909ac8ad87fd48cc2620690c4"
PRIMARY_BASE = "332da58a9b6b825c384a142dfb59d7ed2b8b774e"
PACKAGE = "research/integration/release_order_observability_57_20261003_5156"
FREEZE_SHA = "82107800e25c47b2929dc587fd21b2f489d508ef11ea0bbee6a43bc01f17f2df"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def signature(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--private", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    if args.output.exists():
        raise FileExistsError("readback record already exists")

    def git(*argv):
        result = subprocess.run(["git", "-C", str(args.repo), *argv],
                                capture_output=True, timeout=10, check=True)
        return result.stdout

    def load(name):
        return json.loads((here / name).read_bytes())

    started = datetime.now(timezone.utc).isoformat()
    freeze_bytes = (here / "FREEZE.json").read_bytes()
    assert digest(freeze_bytes) == FREEZE_SHA
    assert git("show", PROSPECTIVE + ":" + PACKAGE + "/FREEZE.json") == freeze_bytes
    freeze = load("FREEZE.json")
    assert freeze["source_base"] == PRIMARY_BASE
    assert len(freeze["sha256"]) == 18
    for name, expected in freeze["sha256"].items():
        working = (here / name).read_bytes()
        retained = git("show", PROSPECTIVE + ":" + PACKAGE + "/" + name)
        assert digest(working) == expected, name
        assert retained == working, name

    source_groups = []
    for source_name, construction in [("SOURCE.json", False),
                                       ("construction_sources/SOURCE.json", True)]:
        source = load(source_name)
        for path, pin in source["files"].items():
            blob = git("rev-parse", source["base_commit"] + ":" + path).decode().strip()
            data = git("cat-file", "blob", blob)
            relative = "construction_sources/" + Path(path).name + ".txt" if construction else pin["export_path"]
            assert blob == pin["git_blob"]
            assert data == (here / relative).read_bytes()
            assert len(data) == pin["bytes"] and digest(data) == pin["sha256"]
        source_groups.append({"base": source["base_commit"], "git_byte_matches": len(source["files"])})
    for name in ("__init__.py", "contracts.py", "lifecycle.py"):
        assert (here / "frozen_kernel" / name).read_bytes() == (here / "construction_sources" / (name + ".txt")).read_bytes()

    raw = load("run01/raw.json")
    audit = load("run01/audit.json")
    attempt = load("run01/ATTEMPT.json")
    run = load("run01/RUN_RECEIPT.json")
    assert attempt["prospective_commit"] == PROSPECTIVE
    assert attempt["freeze_sha256"] == raw["freeze_sha256"] == FREEZE_SHA
    assert raw["source_identity"] == load("SOURCE.json")
    assert raw["cases_sha256"] == digest((here / "cases.json").read_bytes())
    assert audit["raw_sha256"] == digest((here / "run01/raw.json").read_bytes())
    assert len(raw["rows"]) == audit["rows"] == 36
    assert len(audit["mixed_full_projection_classes"]) == 6
    assert audit["integrity"] == "PASS" and audit["errors"] == []
    assert audit["model_decision"] == "FAIL_TERMINAL_RELEASE_IDENTIFIABILITY"
    assert audit["kernel_false_release_reports"] == audit["end_floor_wrong_refusals"] == 12
    assert audit["ordered_witness_disagreements"] == 0
    assert len(audit["corruption_controls"]) == 12 and all(c["refused"] is True for c in audit["corruption_controls"])
    assert (run["candidate_invocations"], run["auditor_invocations"], run["retries"]) == (1, 1, 0)

    originals_checked = 0
    for label in ("construction", "candidate", "auditor"):
        receipt = load("run01/" + label + ".receipt.json")
        assert receipt["exit_code"] == 0 and receipt["timed_out"] is False
        if label in ("candidate", "auditor"):
            assert run[label] == receipt
            assert freeze["created_utc"] < attempt["start_utc"] <= receipt["start_utc"] < receipt["end_utc"]
        for stream, pin in receipt["streams"].items():
            published = (here / "run01" / (label + "." + stream + ".txt")).read_bytes()
            assert len(published) == pin["published_bytes"]
            assert digest(published) == pin["published_sha256"]
        if args.private is None:
            continue
        original_bytes = (args.private / (label + ".receipt.json")).read_bytes()
        original = json.loads(original_bytes)
        assert len(original_bytes) == receipt["original_receipt_bytes"]
        assert digest(original_bytes) == receipt["original_receipt_sha256"]
        assert original["cwd"] == str(here)
        assert ["<python>", *original["argv"][1:]] == receipt["argv"]
        assert receipt["cwd"] == "<study>" and "pid" not in receipt
        for key in ("label", "start_utc", "end_utc", "exit_code", "timed_out", "python", "platform"):
            assert original[key] == receipt[key], (label, key)
        for stream, pin in receipt["streams"].items():
            data = (args.private / (label + "." + stream)).read_bytes()
            assert len(data) == pin["original_bytes"] == original["streams"][stream]["bytes"]
            assert digest(data) == pin["original_sha256"] == original["streams"][stream]["sha256"]
            assert data.replace(str(here).encode(), b"<study>") == (here / "run01" / (label + "." + stream + ".txt")).read_bytes()
        originals_checked += 1

    rows = {r["case_id"]: r for r in raw["rows"]}
    safe = rows["e700-p200-r400-time"]
    held = rows["e700-p600-r400-time"]
    assert signature(safe["projection"]) == signature(held["projection"])
    assert safe["terminal_keys_down"] == [] and held["terminal_keys_down"] == ["A"]
    assert safe["kernel_outcome"] == held["kernel_outcome"]
    assert safe["kernel_outcome"]["release_verified"] is True
    assert safe["comparators"]["end_floor"] is False

    parsed = []
    for path in sorted(here.rglob("*.py")):
        ast.parse(path.read_bytes(), filename=path.name)
        parsed.append(path.relative_to(here).as_posix())
    report = {"kind": "post-run read-only Git/byte/provenance inspection; no producer/auditor/kernel import",
              "start_utc": started, "end_utc": datetime.now(timezone.utc).isoformat(),
              "result": "PASS", "prospective_commit": PROSPECTIVE, "freeze_sha256": FREEZE_SHA,
              "frozen_inputs_working_and_committed": 18, "source_groups": source_groups,
              "construction_reused_exact_source_files": 3, "original_capture_receipts_and_stream_pairs": originals_checked,
              "public_stream_pairs": 3, "primary_rows": 36, "copied_raw_controls_refused": 12,
              "witness_case_ids": [safe["case_id"], held["case_id"]],
              "raw_sha256": digest((here / "run01/raw.json").read_bytes()),
              "audit_sha256": digest((here / "run01/audit.json").read_bytes()),
              "syntax_only_python_files": parsed,
              "limits": "Source/JSON equality checks, not authentication or a new scientific execution. Private originals stay private; omission of --private does not verify them."}
    args.output.write_bytes((json.dumps(report, indent=2, sort_keys=True) + "\n").encode())
    print(json.dumps({"result": "PASS", "frozen_inputs": 18, "source_blobs": 8,
                      "original_captures": originals_checked, "syntax_only_files": len(parsed)}))


if __name__ == "__main__":
    main()
