from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import zipfile
import base64
import io
from pathlib import Path


SOURCE_SHA256 = "28b207348b6279395670b282edcdc719ac1a653ff0e2dc09c987cf95526cf4d5"
TRANSPORT_SHA256 = "474b6381e8381ed8cae12141303e4638539d12cf6cf8b1c999c630efae80efe7"
RAW_SHA256 = "5f48e0274f9fd800ac26af3dd70bd52171700b32ce159f3cdbe0f28c7ec35e7d"
SOURCE_GIT_BLOB = "1a6cc0e46b32d4cd6989aed118d003cce4cfe399"
TRANSPORT_GIT_BLOB = "c38dd2002f201d49b6fc261caff019550a4bf4bc"
SOURCE_RELATIVE = "research/analysis/predicate_order_drift_4258_v1/src/audit.py"
TRANSPORT_RELATIVE = "research/analysis/predicate_order_drift_4258_v1/RAW_AND_AUDIT.zip.base64"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_inputs(repo_root: Path):
    source_path = repo_root / "audit.py" if repo_root.is_dir() and repo_root.name == "source" else repo_root / SOURCE_RELATIVE
    transport_path = repo_root / "RAW_AND_AUDIT.zip.base64" if repo_root.is_dir() and repo_root.name == "input" else repo_root / TRANSPORT_RELATIVE
    source_bytes = source_path.read_bytes()
    transport_bytes = transport_path.read_bytes()
    identities = {
        "source_sha256": sha256(source_bytes),
        "transport_sha256": sha256(transport_bytes),
        "source_git_blob_expected": SOURCE_GIT_BLOB,
        "transport_git_blob_expected": TRANSPORT_GIT_BLOB,
        "source_bytes": len(source_bytes),
        "transport_bytes": len(transport_bytes),
    }
    if identities["source_sha256"] != SOURCE_SHA256:
        raise ValueError("STOP_SOURCE_SHA256_MISMATCH")
    if identities["transport_sha256"] != TRANSPORT_SHA256:
        raise ValueError("STOP_TRANSPORT_SHA256_MISMATCH")
    decoded = base64.b64decode(b"".join(transport_bytes.split()), validate=True)
    with zipfile.ZipFile(io.BytesIO(decoded)) as archive:
        if archive.namelist() != ["RAW.json", "AUDIT.json"]:
            raise ValueError("STOP_ARCHIVE_MEMBER_SET_MISMATCH")
        raw_bytes = archive.read("RAW.json")
    identities.update({"decoded_zip_sha256": sha256(decoded), "raw_sha256": sha256(raw_bytes),
                       "raw_bytes": len(raw_bytes)})
    if identities["raw_sha256"] != RAW_SHA256 or identities["raw_bytes"] != 186739:
        raise ValueError("STOP_RAW_MEMBER_IDENTITY_MISMATCH")
    raw = json.loads(raw_bytes)
    rows = sum(len(distribution.get("rows", [])) for distribution in raw.get("distributions", []))
    if (len(raw.get("distributions", [])), rows, raw.get("truth_state_count")) != (21, 336, 16):
        raise ValueError("STOP_RAW_SCHEMA_COUNTS_MISMATCH")
    return source_path, source_bytes, raw_bytes, raw, identities


def summarize(result: dict) -> dict:
    return {"status": result.get("status"), "errors": result.get("errors"),
            "corruption_controls_rejected": result.get("corruption_controls_rejected"),
            "corruption_control_count": result.get("corruption_control_count"),
            "distribution_count": result.get("distribution_count"),
            "row_count": result.get("row_count")}


CHILD = r'''import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("frozen_4733_audit", sys.argv[1])
if spec is None or spec.loader is None:
    raise RuntimeError("STOP_AUDITOR_IMPORT_UNAVAILABLE")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
if not callable(getattr(module, "audit", None)):
    raise RuntimeError("STOP_AUDITOR_API_MISMATCH")
doc = json.load(sys.stdin)
print(json.dumps(module.audit(doc), sort_keys=True, allow_nan=False))
'''


MODES = ("normal", "python_-O", "PYTHONOPTIMIZE=1")


def run_auditor(source_path: Path, doc: dict, mode: str) -> dict:
    env = os.environ.copy()
    command = [sys.executable]
    if mode == "python_-O":
        command.append("-O")
        env.pop("PYTHONOPTIMIZE", None)
    elif mode == "PYTHONOPTIMIZE=1":
        env["PYTHONOPTIMIZE"] = "1"
    payload = json.dumps(doc, sort_keys=True, allow_nan=True, separators=(",", ":"))
    completed = subprocess.run(command + ["-c", CHILD, str(source_path)], input=payload,
                               text=True, encoding="utf-8", capture_output=True,
                               check=False, env=env, timeout=30)
    if completed.returncode != 0:
        return {"status": "CHILD_PROCESS_FAILURE", "exit_code": completed.returncode,
                "stderr": completed.stderr[-2000:]}
    try:
        return summarize(json.loads(completed.stdout))
    except (json.JSONDecodeError, TypeError) as exc:
        return {"status": "CHILD_OUTPUT_INVALID", "reason": f"{type(exc).__name__}: {exc}",
                "stdout_sha256": sha256(completed.stdout.encode())}


def execute(repo_root: Path, environment: dict) -> dict:
    source_path, source_bytes, raw_bytes, original, identities = load_inputs(repo_root)
    baseline = {mode: run_auditor(source_path, copy.deepcopy(original), mode) for mode in MODES}
    mutants = {}
    mutant = copy.deepcopy(original)
    mutant["distributions"][0]["rows"][0]["weight"] = float("nan")
    mutants["first_row_weight_json_nan"] = mutant

    mutant = copy.deepcopy(original)
    mutant["development_alpha"] = 0.5
    mutants["development_alpha_0_5"] = mutant

    mutant = copy.deepcopy(original)
    mutant["truth_state_count"] = 99
    mutants["truth_state_count_99"] = mutant
    mutations = {name: {mode: run_auditor(source_path, copy.deepcopy(doc), mode)
                        for mode in MODES} for name, doc in mutants.items()}

    if sha256(source_path.read_bytes()) != identities["source_sha256"]:
        raise ValueError("STOP_SOURCE_CHANGED_DURING_PROBE")
    if sha256(raw_bytes) != identities["raw_sha256"]:
        raise ValueError("STOP_RAW_CHANGED_DURING_PROBE")

    baseline_valid = all(item["status"] == "PASS_DRIFT_BOUNDARY_MAPPED" and item["errors"] == []
                         and item["corruption_controls_rejected"] == 5
                         and item["corruption_control_count"] == 5 for item in baseline.values())
    reproduced = any(item[mode]["status"] == "PASS_DRIFT_BOUNDARY_MAPPED"
                     and item[mode]["errors"] == [] for item in mutations.values() for mode in MODES)
    all_rejected = all(item[mode]["status"] != "PASS_DRIFT_BOUNDARY_MAPPED" or item[mode]["errors"]
                       for item in mutations.values() for mode in MODES)
    disposition = ("STOP_PROVENANCE_OR_RUNTIME" if not baseline_valid else
                   "PASS_AUDIT_GAP_REPRODUCED" if reproduced else
                   "FAIL_GAP_NOT_REPRODUCED" if all_rejected else "STOP_PROVENANCE_OR_RUNTIME")
    return {"schema": "predicate-order-audit-integrity-4733-probe-v1",
            "issue": 4953, "allocation": "predicate-order-audit-integrity-4733-20260928-01",
            "disposition": disposition, "environment": environment, "identities": identities,
            "baseline": baseline, "mutations": mutations,
            "original_raw_sha256_before_after_equal": True,
            "source_sha256_before_after_equal": True}


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: run_probe.py SOURCE_PATH TRANSPORT_PATH OUTPUT_JSON", file=sys.stderr)
        return 64
    output = Path(sys.argv[2])
    if output.exists():
        print("STOP_OUTPUT_ALREADY_EXISTS", file=sys.stderr)
        return 2
    try:
        env = {"platform": sys.platform, "python": sys.version.split()[0],
               "executable": sys.executable,
               "runtime_mode": os.environ.get("PROBE_RUNTIME_MODE", "unspecified")}
        result = execute(Path(sys.argv[1]), env)
        # The transport path is separately mounted read-only; verify the same bytes
        # the standard repository-relative loader would consume.
        if sha256(Path(sys.argv[2]).read_bytes()) != TRANSPORT_SHA256:
            raise ValueError("STOP_TRANSPORT_MOUNT_MISMATCH")
    except Exception as exc:
        result = {"schema": "predicate-order-audit-integrity-4733-probe-v1",
                  "issue": 4953, "allocation": "predicate-order-audit-integrity-4733-20260928-01",
                  "disposition": "STOP_PROVENANCE_OR_RUNTIME",
                  "stop_reason": f"{type(exc).__name__}: {exc}"}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0 if result["disposition"] in {"PASS_AUDIT_GAP_REPRODUCED", "FAIL_GAP_NOT_REPRODUCED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
