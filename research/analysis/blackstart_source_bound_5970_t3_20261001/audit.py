from __future__ import annotations

import hashlib
import base64
import io
import json
import lzma
import subprocess
import sys
import tarfile
from pathlib import Path


def adjudicate(run: dict) -> tuple[str, list[str]]:
    errors = []
    expected = {"KeyPress", "KeyRelease"}
    app = run.get("app_rows", [])
    observer = run.get("observer_rows", [])
    epoch = run.get("epoch")
    for source, rows in (("app", app), ("observer", observer)):
        relevant = [r for r in rows if r.get("kind") in expected and r.get("source") == source]
        if {r.get("kind") for r in relevant} != expected or len(relevant) != 2:
            errors.append(f"{source.upper()}_EVENT_SET_MISMATCH")
        if any(r.get("causal_parent_ids") != [f"act:{r.get('actuation_id')}"] for r in relevant):
            errors.append(f"{source.upper()}_PARENT_MISMATCH")
        if any(not r.get("source_seq") or not r.get("event_id") for r in relevant):
            errors.append(f"{source.upper()}_LOCAL_ID_MISSING")
        if any(r.get("actuation_id") != f"{epoch}:{r.get('kind').lower()}" for r in relevant):
            errors.append(f"{source.upper()}_ACTION_BINDING_MISMATCH")
    for kind in expected:
        left = [r for r in app if r.get("kind") == kind and r.get("source") == "app"]
        right = [r for r in observer if r.get("kind") == kind and r.get("source") == "observer"]
        if len(left) == len(right) == 1:
            a, b = left[0], right[0]
            if a.get("actuation_id") != b.get("actuation_id"):
                errors.append(f"{kind}_ACTUATION_MISMATCH")
            if a.get("keycode") != b.get("detail"):
                errors.append(f"{kind}_KEYCODE_MISMATCH")
            if a.get("time") != b.get("time"):
                errors.append(f"{kind}_X_TIME_MISMATCH")
    if not run.get("release_attempted"):
        errors.append("CLEANUP_RELEASE_NOT_ATTEMPTED")
    if run.get("terminal_neutral") is not True:
        errors.append("TERMINAL_NEUTRAL_NOT_PROVEN")
    if run.get("error") is not None:
        errors.append("RUNNER_REPORTED_ERROR")
    return ("PASS_SOURCE_BOUND_CAUSAL_PAIR" if not errors else "HOLD_SOURCE_BOUND_TRACE_INCOMPLETE"), errors


def independently_verify_source() -> dict:
    here = Path(__file__).resolve().parent
    freeze = json.loads((here / "FREEZE.json").read_text())
    commit = freeze["source_commit"]
    prefix = freeze["archive_path"] + "/"
    def blob(path: str) -> bytes:
        return subprocess.check_output(["git", "show", f"{commit}:{prefix}{path}"])
    meta = json.loads(blob("EVIDENCE_BASE64.json"))
    chunks = []
    for part in meta["parts"]:
        raw = blob(part["path"]).decode("ascii").strip()
        digest = hashlib.sha256(raw.encode("ascii")).hexdigest()
        if digest != freeze["archive_parts"].get(part["path"]) or digest != part["sha256"]:
            raise ValueError(f"AUDIT_ARCHIVE_PART_MISMATCH:{part['path']}")
        chunks.append(raw)
    archive = base64.b64decode("".join(chunks), validate=True)
    if len(archive) != freeze["archive_bytes"] or hashlib.sha256(archive).hexdigest() != freeze["archive_sha256"]:
        raise ValueError("AUDIT_ARCHIVE_HASH_MISMATCH")
    with tarfile.open(fileobj=io.BytesIO(lzma.decompress(archive)), mode="r:") as tar:
        files = {m.name: m for m in tar.getmembers() if m.isfile()}
        if len(files) != freeze["expanded_file_count"]:
            raise ValueError("AUDIT_FILE_INVENTORY_MISMATCH")
        source_hashes = {}
        for name in ("app.py", "observer.py"):
            candidates = [n for n in files if n.endswith("/source/" + name)]
            if len(candidates) != 1:
                raise ValueError(f"AUDIT_SOURCE_MEMBER_MISMATCH:{name}")
            digest = hashlib.sha256(tar.extractfile(files[candidates[0]]).read()).hexdigest()
            if digest != freeze["source_hashes"][name]:
                raise ValueError(f"AUDIT_SOURCE_HASH_MISMATCH:{name}")
            source_hashes[name] = digest
    return {"archive_sha256": hashlib.sha256(archive).hexdigest(), "expanded_file_count": len(files), "source_hashes": source_hashes}


def main() -> int:
    here = Path(__file__).resolve().parent
    frozen = json.loads((here / "FREEZE_T3.json").read_text())
    frozen_errors = [f"FROZEN_SOURCE_CHANGED:{name}" for name, expected in frozen["analysis_sources_sha256"].items()
                     if hashlib.sha256((here / name).read_bytes()).hexdigest() != expected]
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else here / "candidate.raw.json"
    raw = path.read_bytes()
    candidate = json.loads(raw)
    errors = list(frozen_errors)
    source_check = independently_verify_source()
    if candidate.get("source_reconstruction", {}).get("archive_sha256") != source_check["archive_sha256"]:
        errors.append("CANDIDATE_ARCHIVE_RECONSTRUCTION_MISMATCH")
    if candidate.get("source_reconstruction", {}).get("sources", {}) and {k: v.get("sha256") for k, v in candidate["source_reconstruction"]["sources"].items()} != source_check["source_hashes"]:
        errors.append("CANDIDATE_SOURCE_HASH_MISMATCH")
    disposition, trace_errors = adjudicate(candidate.get("run") or {})
    errors.extend(trace_errors)
    if errors:
        disposition = "HOLD_SOURCE_BOUND_TRACE_INCOMPLETE"
    result = {"schema": "blackstart-source-bound-t3-independent-audit-v1", "candidate_sha256": hashlib.sha256(raw).hexdigest(),
              "source_check": source_check, "disposition": disposition, "errors": errors, "timestamps_used_to_infer_causality": False}
    (here / "audit.raw.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if disposition == "PASS_SOURCE_BOUND_CAUSAL_PAIR" else 2


if __name__ == "__main__":
    raise SystemExit(main())
