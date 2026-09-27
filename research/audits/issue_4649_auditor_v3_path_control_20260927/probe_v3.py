import base64
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path


EXPECTED_SOURCE_SHA256 = "7b506919f5ed0a9b6c1fe2ebd4a720ed4c2b41bf38ed8d9c6939e2fc9685863d"
EXPECTED_IMAGE_ID = "sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9"
ALLOCATION = "issue4649-auditor-v3-path-confinement-20260927-01"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_bytes((json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode())


def run_case(source, outer, name, rel, payload, link_target=None, manifest_escape=False):
    case = outer / name
    inputs = case / "inputs"
    inputs.mkdir(parents=True)
    outside = case / "outside"
    outside.mkdir()
    actual = inputs / "actual"
    actual.write_bytes(payload)
    (outside / "sentinel").write_bytes(payload)
    if link_target == "inside":
        (inputs / "link").symlink_to(actual)
    elif link_target == "outside":
        (inputs / "link").symlink_to(outside / "sentinel")

    input_rel = rel
    if rel == "../outside/sentinel":
        input_digest = sha(payload)
    else:
        input_digest = sha(payload)
    manifest = {"inputs": {"sentinel": {"path": input_rel, "sha256": input_digest}}}
    manifest_bytes = (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode()
    encoded_manifest = base64.b64encode(manifest_bytes) + b"\n"
    if manifest_escape:
        (outside / "manifest.b64").write_bytes(encoded_manifest)
        (inputs / "MANIFEST.json.b64").symlink_to(outside / "manifest.b64")
    else:
        (inputs / "MANIFEST.json.b64").write_bytes(encoded_manifest)

    freeze = {"manifest_sha256": sha(manifest_bytes), "input_sha256": {"sentinel": input_digest}}
    result = {"input_sha256": {"sentinel": {"path": input_rel, "sha256": input_digest}}}
    freeze_path = case / "freeze.json"
    result_path = case / "result.json"
    stub_path = case / "audit_v1_stub.py"
    write_json(freeze_path, freeze)
    write_json(result_path, result)
    stub_path.write_text(
        'import json\nprint(json.dumps({"decision":"PASS_INDEPENDENT","errors":[]}))\n',
        encoding="utf-8",
    )
    cp = subprocess.run(
        [sys.executable, "-B", str(source), "--input-root", str(inputs),
         "--freeze", str(freeze_path), "--result", str(result_path),
         "--audit-v1", str(stub_path)], capture_output=True, text=True, timeout=20,
    )
    try:
        observed = json.loads(cp.stdout)
    except Exception:
        observed = {"decision": "INVALID_OUTPUT", "errors": []}
    return {
        "name": name,
        "path": rel,
        "manifest_escape": manifest_escape,
        "decision": observed.get("decision"),
        "errors": observed.get("errors"),
        "stderr": cp.stderr,
        "exit": cp.returncode,
    }


def main():
    source = Path("/study/audit_v3.py")
    source_hash = sha(source.read_bytes())
    if source_hash != EXPECTED_SOURCE_SHA256:
        raise SystemExit("STOP_SOURCE_HASH_MISMATCH:" + source_hash)
    if os.environ.get("EXPECTED_IMAGE_ID") != EXPECTED_IMAGE_ID:
        raise SystemExit("STOP_IMAGE_ID_MISMATCH")
    payload = b"immutable-synthetic-sentinel\n"
    rows = []
    with tempfile.TemporaryDirectory(prefix="issue4649-v3-path-") as temp:
        outer = Path(temp)
        rows.append(run_case(source, outer, "contained_file", "actual", payload))
        rows.append(run_case(source, outer, "contained_symlink", "link", payload, link_target="inside"))
        rows.append(run_case(source, outer, "dotdot", "../outside/sentinel", payload))
        rows.append(run_case(source, outer, "input_symlink_escape", "link", payload, link_target="outside"))
        rows.append(run_case(source, outer, "manifest_symlink_escape", "actual", payload, manifest_escape=True))

    by_name = {row["name"]: row for row in rows}
    expected = {
        "contained_file": ("PASS_INDEPENDENT", []),
        "contained_symlink": ("PASS_INDEPENDENT", []),
        "dotdot": ("FAIL", None),
        "input_symlink_escape": ("FAIL", ["V3_UNSAFE_INPUT_PATH:sentinel"]),
        "manifest_symlink_escape": ("FAIL", ["V3_UNSAFE_MANIFEST_PATH"]),
    }
    checks = []
    for name, (decision, errors) in expected.items():
        row = by_name[name]
        checks.append(row["decision"] == decision and row["stderr"] == ""
                      and (errors is None or row["errors"] == errors))
    result = {
        "schema": "issue4649-auditor-v3-path-confinement-controls-v1",
        "allocation": ALLOCATION,
        "source_sha256": source_hash,
        "base_v2_sha256": "500946223763825cd7773dacae55ab67cc3b624b958c941fdd84b2b877f73630",
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "image_id": EXPECTED_IMAGE_ID,
        "checks_pass": all(checks),
        "decision": "PASS_PATH_CONFINEMENT_V3" if all(checks) else "FAIL_PATH_CONFINEMENT_OR_COMPATIBILITY",
        "rows": rows,
        "formal_runner_invocations": 0,
        "prior_eight_control_harness_invocations": 0,
    }
    encoded = json.dumps(result, sort_keys=True) + "\n"
    Path("/out/RESULT.json").write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
