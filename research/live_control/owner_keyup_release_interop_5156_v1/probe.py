"""Independent source-interop falsification probe; synthetic/static only."""
import hashlib
import ast
import argparse
import json
import platform
from pathlib import Path

from release_protocol_v2 import AUTONOMOUS_REASONS, ProtocolError, validate_receipt


PIN = {
    "main": "53b93cd5dcb0fbbedee1db23ddf550ba1eb289e0",
    "owner_path": "research/live_control/input_owner_v10.py",
    "owner_blob": "341b3c01649943ddaad5f28431a792c4889cc36e",
    "wrapper_path": "research/live_control/input_transition_owner_v3.py",
    "wrapper_blob": "0ea631abcf6272f0538a9ef9198ad8069b47b464",
    "protocol_path": "research/live_control/owner_keyup_release_semantics_5156_v2/release_protocol_v2.py",
    "protocol_blob": "55272e127073a84c9eb541bc650fee74f3fc7123",
    "protocol_sha256": "3ae2ad7ca09bdd6572080aa55ce9fae9cb24a566629c95bf9736220098f134cd",
}

HERE = Path(__file__).resolve().parent


def git_blob_sha(path):
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def owner_release_reasons(source):
    tree = ast.parse(source)
    reasons = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name) or node.func.id != "release":
            continue
        if node.args:
            reasons.update(n.value for n in ast.walk(node.args[0])
                           if isinstance(n, ast.Constant) and isinstance(n.value, str))
    return reasons


def base(kind, operation, sequence, start, end):
    row = {
        "schema": "owner-keyup-release-v2", "release_kind": kind,
        "operation": operation, "request_id": "request-1" if kind == "explicit_client_up" else None,
        "release_reason": "expired" if kind == "autonomous_cleanup" else None,
        "owner_id": "owner-1", "intent_token": "intent-1", "key": "Down",
        "owner_sequence": sequence,
        "caller_started_ns": start if kind == "explicit_client_up" else None,
        "owner_release_started_ns": start + 1, "owner_sync_returned_ns": end - 1,
        "caller_returned_ns": end if kind == "explicit_client_up" else None,
        "owned_before": True, "owned_after": False, "grants_input_authority": False,
    }
    if kind == "autonomous_cleanup":
        row.pop("caller_started_ns")
        row.pop("caller_returned_ns")
    return row


def accepted(row):
    try:
        validate_receipt(row)
        return True, "accepted"
    except ProtocolError as exc:
        return False, str(exc)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS")
    owner_path = HERE / "input_owner_v10.py"
    wrapper_path = HERE / "input_transition_owner_v3.py"
    owner_source = owner_path.read_text(encoding="utf-8")
    wrapper_source = wrapper_path.read_text(encoding="utf-8")
    owner_reasons = owner_release_reasons(owner_source)
    if not {"stop_requested", "expired", "surface_changed", "focus_changed", "cancelled", "thread_exit"}.issubset(owner_reasons):
        raise SystemExit("STOP_OWNER_RELEASE_CALLGRAPH_MISMATCH")
    if "type(key) is not int or key not in (1,2,3)" not in owner_source:
        raise SystemExit("STOP_OWNER_BUTTON_CONTRACT_MISMATCH")
    if '"key" if operation == "up" else "button": key' not in wrapper_source:
        raise SystemExit("STOP_WRAPPER_BUTTON_FIELD_MISMATCH")
    protocol_path = HERE / "release_protocol_v2.py"
    protocol_sha = hashlib.sha256(protocol_path.read_bytes()).hexdigest()
    source_blobs = {"owner": git_blob_sha(owner_path), "wrapper": git_blob_sha(wrapper_path),
                    "protocol": git_blob_sha(protocol_path)}
    if source_blobs != {"owner": PIN["owner_blob"], "wrapper": PIN["wrapper_blob"],
                        "protocol": PIN["protocol_blob"]}:
        raise SystemExit("STOP_SOURCE_BLOB_MISMATCH")
    if protocol_sha != PIN["protocol_sha256"]:
        raise SystemExit("STOP_PROTOCOL_SOURCE_SHA_MISMATCH")
    rows = []
    owner_reasons.discard("release")
    for reason in sorted(owner_reasons):
        row = base("autonomous_cleanup", None, 1, 100, 110)
        row["release_reason"] = reason
        ok, error = accepted(row)
        rows.append({"case": f"owner_reason:{reason}", "accepted": ok, "result": error,
                     "expected": True})

    button = base("explicit_client_up", "button_up", 1, 100, 110)
    button.pop("key")
    button["button"] = 1
    ok, error = accepted(button)
    rows.append({"case": "owner_button_up_integer_identity", "accepted": ok, "result": error,
                 "expected": True})

    report = {
        "schema": "issue-5156-release-protocol-interop-probe-v1",
        "decision": "FAIL_RELEASE_RECEIPT_INTEROP" if any(r["accepted"] != r["expected"] for r in rows) else "PASS_RELEASE_RECEIPT_INTEROP",
        "classification": "CONSTRUCTION_COMPATIBILITY_DIAGNOSTIC_NOT_FORMAL_X11",
        "pins": PIN,
        "source_git_blobs": source_blobs,
        "protocol_source_sha256": protocol_sha,
        "owner_source_sha256": hashlib.sha256(owner_path.read_bytes()).hexdigest(),
        "wrapper_source_sha256": hashlib.sha256(wrapper_path.read_bytes()).hexdigest(),
        "owner_autonomous_reasons": sorted(owner_reasons),
        "protocol_autonomous_reasons": sorted(AUTONOMOUS_REASONS),
        "checks": rows,
        "mismatches": [r["case"] for r in rows if r["accepted"] != r["expected"]],
        "authority_grants": 0,
        "x11_or_input_used": False,
        "runtime": {"python": platform.python_version(), "platform": platform.platform()},
    }
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(encoded, encoding="utf-8", newline="\n")
    print(encoded, end="")
    raise SystemExit(0)


if __name__ == "__main__":
    main()
