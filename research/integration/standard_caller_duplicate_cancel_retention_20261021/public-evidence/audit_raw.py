"""Verify the sanitized public copy of the standard-caller characterization."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main():
    raw = json.loads((ROOT / "raw/r02.json").read_text(encoding="utf-8"))
    audit = json.loads((ROOT / "audit.json").read_text(encoding="utf-8"))
    redaction = json.loads((ROOT / "redaction.json").read_text(encoding="utf-8"))
    conditions = json.loads((ROOT / "conditions.json").read_text(encoding="utf-8"))
    require(conditions["source_revision"] == raw["source_revision"],
            "condition/source revision mismatch")
    require(raw["call_id"] == "CALL_R02", "call ID redaction missing")
    require(raw["terminal_interface_results"]["call_directory"] == "<TEMP>/CALL_R02",
            "temporary path redaction missing")
    require(raw["release_attempt_count"] == 1, "cleanup count changed")
    require(raw["first_cancel"]["cleanup_status"] == "UNKNOWN",
            "first cancellation uncertainty changed")
    require(raw["first_cancel"]["release_confirmed"] is False,
            "release confirmation changed")
    require(raw["second_cancel"]["status"] == "not_active",
            "duplicate response changed")
    require("cancellation" not in raw["terminal_interface_results"],
            "terminal retention observation changed")
    require(raw["terminal_interface_results"]["task_success"] is None,
            "task-success classification changed")
    require(audit["decision"] == "PASS_CHARACTERIZATION_GAP_REPRODUCED",
            "audit decision changed")
    require(audit["public_sha256"] == sha256(ROOT / "raw/r02.json"),
            "audit does not bind public raw")
    require(audit["run_probe_sha256"] == sha256(ROOT / "run_probe.py"),
            "audit does not bind the public probe source")
    require(redaction["public_raw_sha256"] == sha256(ROOT / "raw/r02.json"),
            "redaction record does not bind public raw")
    forbidden = ("C:\\Users\\", "D:\\CodexData\\Temp\\", "44100",
                 "4a43f263361747c59f208ae93c35439b")
    serialized = json.dumps(raw)
    require(not any(value in serialized for value in forbidden),
            "host-local identity remains in public JSON")
    manifest = (ROOT / "SHA256SUMS").read_text(encoding="ascii").splitlines()
    listed = set()
    for line in manifest:
        expected, relative = line.split("  ", 1)
        listed.add(relative)
        require(expected == sha256(ROOT / relative),
                f"manifest mismatch for {relative}")
    actual = {
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file() and path.name != "SHA256SUMS"
    }
    require(listed == actual, "manifest file membership differs")
    print(json.dumps({"decision": "PASS_PUBLIC_COPY_AUDIT", "errors": []},
                     sort_keys=True))


if __name__ == "__main__":
    main()
