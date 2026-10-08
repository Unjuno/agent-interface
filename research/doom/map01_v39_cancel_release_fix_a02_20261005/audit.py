#!/usr/bin/env python3
"""Offline audit of A02 source identities, retained outputs, and package hashes."""
import hashlib
import json
import re
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[2]


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def git_blob_sha1(path):
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def read_text(name):
    return (PACKAGE / name).read_text(encoding="utf-8-sig")


def exit_code(name):
    return int(read_text(name).strip())


def raw_json_line(name, prefix):
    matches = [line[len(prefix):] for line in read_text(name).splitlines()
               if line.startswith(prefix)]
    require(len(matches) == 1, f"{name}: expected one {prefix.strip()} record")
    return json.loads(matches[0])


def expiry_debug(name):
    return raw_json_line(name, "EXPIRY_DEBUG ")


def audit_manifest():
    manifest = PACKAGE / "SHA256SUMS"
    require(manifest.is_file(), "missing SHA256SUMS")
    entries = {}
    for line in manifest.read_text(encoding="ascii").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        require(match is not None, f"malformed manifest line: {line!r}")
        digest, name = match.groups()
        require(name not in entries, f"duplicate manifest path: {name}")
        entries[name] = digest
    actual = {
        path.relative_to(PACKAGE).as_posix()
        for path in PACKAGE.rglob("*")
        if path.is_file() and path.name != "SHA256SUMS"
        and "__pycache__" not in path.parts
    }
    require(set(entries) == actual,
            f"manifest path set mismatch: missing={sorted(actual-set(entries))}, "
            f"extra={sorted(set(entries)-actual)}")
    for name, digest in entries.items():
        observed = hashlib.sha256((PACKAGE / name).read_bytes()).hexdigest()
        require(observed == digest, f"SHA-256 mismatch: {name}")
    return len(entries)


def audit_sources():
    lock = json.loads(read_text("SOURCE_LOCK.json"))
    require(lock["base_main"] == "dccf55e264f434ca27f2948fe53be09919047819",
            "unexpected current-main source lock")
    for name, expected in lock["upstream_source_blobs"].items():
        path = ROOT / Path(name)
        require(path.is_file(), f"missing locked main input: {name}")
        observed = git_blob_sha1(path)
        require(observed == expected, f"main Git blob mismatch: {name}")
    for filename, expected in lock["candidate_git_blobs"].items():
        observed = git_blob_sha1(PACKAGE / filename)
        require(observed == expected, f"candidate Git blob mismatch: {filename}")
    return lock


def audit_suite_logs():
    checks = [
        ("candidate-suite-final.log", "candidate-suite-final.exit", 10),
        ("owner-compat-suite.log", "owner-compat-suite.exit", 10),
        ("existing-bridge-suite.log", "existing-bridge-suite.exit", 2),
    ]
    for log_name, exit_name, count in checks:
        log = read_text(log_name)
        require(exit_code(exit_name) == 0, f"{log_name}: nonzero saved exit")
        require(re.search(rf"Ran {count} tests? in ", log) is not None,
                f"{log_name}: expected {count} tests")
        require(re.search(r"\bOK\b", log) is not None, f"{log_name}: missing OK")
    require(exit_code("py-compile.exit") == 0, "py_compile did not pass")
    require(exit_code("expiry-red-a02-owner.exit") == 1, "expected pre-fix expiry red")
    require(exit_code("expiry-green-a02.exit") == 0, "expected A02 expiry green")

    red = expiry_debug("expiry-red-a02-owner.log")
    red_events = red["events"]
    require(not any(row.get("event") == "input_release_measurement" for row in red_events),
            "pre-fix bridge unexpectedly emitted a per-key release")
    red_terminal = next(row for row in red_events if row.get("event") == "terminal")
    red_release_rows = red_terminal["release"].get("per_key_release_measurements", [])
    require(red_terminal.get("status") == "expired" and
            red_terminal["release"].get("verified") is True,
            "pre-fix expiry control did not complete verified release")
    require(len(red_release_rows) == 1 and
            red_release_rows[0]["physical_key_measurement"].get("classification") == "CONFIRMED_PHYSICAL_UP",
            "pre-fix terminal lacks its owner up measurement")
    require(red["held"] == ["F8"] and red["fake_physical"] == [],
            "pre-fix stale bridge ledger/physical control differs")

    green = expiry_debug("expiry-green-a02.log")
    green_events = green["events"]
    names = [row.get("event") for row in green_events]
    admission_index = names.index("input_admission")
    release_index = names.index("input_release_measurement")
    terminal_index = names.index("terminal")
    require(admission_index < release_index < terminal_index,
            "A02 release is not ordered admission → up → terminal")
    down = green_events[admission_index]
    up = green_events[release_index]
    terminal = green_events[terminal_index]
    require(down["physical_key_measurement"]["actuation_id"] ==
            up["physical_key_measurement"]["actuation_id"],
            "A02 expiry release actuation identity mismatch")
    require((up.get("id"), up.get("step"), up.get("key")) ==
            ("expiry-executor-a01", 0, "F8"), "A02 expiry context mismatch")
    require(up["physical_key_measurement"].get("classification") == "CONFIRMED_PHYSICAL_UP",
            "A02 expiry up was not confirmed")
    require(terminal.get("status") == "expired" and terminal["release"].get("verified") is True,
            "A02 terminal disposition/release mismatch")
    require(green["held"] == [] and green["fake_physical"] == [],
            "A02 expiry ledgers are not empty")

    candidate_log = read_text("candidate-suite-final.log")
    raw = raw_json_line("candidate-suite-final.log", "RAW_RESULT ")
    require(raw["aggregate_query_number"] == 5, "fault was not injected at aggregate keymap query 5")
    require(raw["release_errors"] == ["sample failure"], "aggregate failure did not propagate")
    require(raw["release_rows"] == [{
        "key": "F8", "id": "release-query-failure", "step": 3,
        "actuation_id": raw["release_rows"][0].get("actuation_id"),
        "classification": "CONFIRMED_PHYSICAL_UP"}], "aggregate up summary mismatch")
    require(bool(raw["release_rows"][0].get("actuation_id")), "aggregate up missing actuation ID")
    owner_release = raw["owner_release"]
    require(owner_release == {
        "verified": False, "verification_status": "UNAVAILABLE", "keys_down": None,
        "buttons_down": None, "verification_error": "RuntimeError"},
        "aggregate failure falsely verifies neutral state or loses its unknown classification")
    require(raw["bridge_held"] == [] and raw["fake_physical"] == [],
            "aggregate confirmed F8 up did not reconcile exact key ledgers")
    require("test_aggregate_keymap_failure_preserves_confirmed_per_key_up_without_neutral_claim" in candidate_log,
            "aggregate regression missing from focused suite")
    return red, green, raw


def main():
    lock = audit_sources()
    tests = audit_suite_logs()
    files = audit_manifest()
    red, green, aggregate = tests
    print(json.dumps({
        "disposition": "PASS_AUDIT",
        "base_main": lock["base_main"],
        "upstream_sources": len(lock["upstream_source_blobs"]),
        "candidate_source_blobs": len(lock["candidate_git_blobs"]),
        "candidate_tests": 10,
        "owner_compatibility_tests": 10,
        "existing_bridge_tests": 2,
        "aggregate_release_rows": len(aggregate["release_rows"]),
        "pre_fix_expiry_up_events": sum(row.get("event") == "input_release_measurement" for row in red["events"]),
        "a02_expiry_up_events": sum(row.get("event") == "input_release_measurement" for row in green["events"]),
        "sha256_files_verified": files
    }, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FAIL_AUDIT: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
