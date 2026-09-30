import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path


EXPECTED_SOURCE_SHA256 = "500946223763825cd7773dacae55ab67cc3b624b958c941fdd84b2b877f73630"
ALLOCATION = "issue4649-auditor-v2-symlink-confinement-20260927-01"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_bytes((json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode())


def invoke(source, root, outer, name, rel, target_bytes, symlink):
    case = outer / name
    inputs = case / "inputs"
    inputs.mkdir(parents=True)
    outside = case / "outside"
    outside.mkdir()
    (outside / "sentinel").write_bytes(target_bytes)
    if symlink:
        (inputs / rel).symlink_to(outside / "sentinel")
    else:
        rel = "../outside/sentinel"
    manifest = {
        "inputs": {
            "sentinel": {"path": rel, "sha256": sha(target_bytes)}
        }
    }
    manifest_bytes = (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode()
    (inputs / "MANIFEST.json.b64").write_bytes(__import__("base64").b64encode(manifest_bytes) + b"\n")
    freeze = {
        "manifest_sha256": sha(manifest_bytes),
        "input_sha256": {"sentinel": sha(target_bytes)},
    }
    freeze_path = case / "freeze.json"
    result_path = case / "result.json"
    stub_path = case / "audit_v1_stub.py"
    write_json(freeze_path, freeze)
    write_json(result_path, {
        "input_sha256": {"sentinel": {"path": rel, "sha256": sha(target_bytes)}}
    })
    stub_path.write_text(
        'import json\nprint(json.dumps({"decision":"PASS_INDEPENDENT","errors":[]}))\n',
        encoding="utf-8",
    )
    cp = subprocess.run(
        [sys.executable, "-B", str(source), "--input-root", str(inputs),
         "--freeze", str(freeze_path), "--result", str(result_path),
         "--audit-v1", str(stub_path)],
        capture_output=True, text=True, timeout=20,
    )
    try:
        observed = json.loads(cp.stdout)
    except Exception:
        observed = {"parse_error": True}
    return {
        "name": name,
        "path": rel,
        "expected": "reject",
        "decision": observed.get("decision"),
        "errors": observed.get("errors"),
        "stderr": cp.stderr,
        "exit": cp.returncode,
        "rejected": observed.get("decision") != "PASS_INDEPENDENT",
    }


def main():
    root = Path("/study")
    source = root / "audit_v2.py"
    source_bytes = source.read_bytes()
    source_hash = sha(source_bytes)
    if source_hash != EXPECTED_SOURCE_SHA256:
        raise SystemExit("STOP_SOURCE_HASH_MISMATCH:" + source_hash)
    image_id = os.environ.get("EXPECTED_IMAGE_ID", "")
    rows = []
    with tempfile.TemporaryDirectory(prefix="issue4649-v2-path-") as tmp:
        outer = Path(tmp)
        payload = b"immutable-synthetic-sentinel\n"
        rows.append(invoke(source, root, outer, "dotdot", "unused", payload, False))
        rows.append(invoke(source, root, outer, "symlink", "linked-input", payload, True))
    checks_pass = all(row["rejected"] and row["stderr"] == "" for row in rows)
    result = {
        "schema": "issue4649-auditor-v2-symlink-control-v1",
        "allocation": ALLOCATION,
        "source_sha256": source_hash,
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "image_id": image_id,
        "checks_pass": checks_pass,
        "decision": "PASS_PATH_CONFINEMENT_CONTROL" if checks_pass else "FAIL_SYMLINK_PATH_CONFINEMENT",
        "rows": rows,
        "formal_runner_invocations": 0,
        "prior_eight_control_harness_invocations": 0,
    }
    encoded = json.dumps(result, sort_keys=True) + "\n"
    Path("/out/RESULT.json").write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0 if checks_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
