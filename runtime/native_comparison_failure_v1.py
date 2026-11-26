"""Retain the observable evidence from an interrupted one-shot comparison."""

import hashlib
import json
import os
from pathlib import Path
import stat

from runtime import native_comparison_audit_v1 as audit


RAW_SEAL = "partial-raw-seal.json"
HOST_SEAL = "partial-host-seal.json"


def safe_file_digest(name, directory_fd):
    def fingerprint(info):
        return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns

    before = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    if not stat.S_ISREG(before.st_mode):
        raise ValueError("non_regular_artifact")
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd)
    with os.fdopen(fd, "rb") as stream:
        opened = os.fstat(stream.fileno())
        if not stat.S_ISREG(opened.st_mode) or fingerprint(opened) != fingerprint(before):
            raise ValueError("artifact_replaced_before_read")
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
        after = os.fstat(stream.fileno())
    # Access time may change while hashing. Identity, contents and change time may not.
    current = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    if fingerprint(before) != fingerprint(after) or fingerprint(after) != fingerprint(current):
        raise ValueError("artifact_changed_during_read")
    return digest


def expected_raw_paths():
    results = {"capture-plan.json", "capture.json", "capture-seal.json"}
    for arm in audit.ARMS:
        contract = "plain" if arm == "plain" else "compiled"
        preflight = f"preflight/{arm}/gate/{contract}-form-grounding"
        session = f"native-app-server/{arm}"
        runtime = f"arms/{arm}/runtime"
        results.update({
            f"{preflight}/preflight-result.json", f"{preflight}/{audit.RECEIPT}",
            f"{preflight}/model-call/events.jsonl", f"{session}/protocol.jsonl",
            f"{session}/{audit.APP_SERVER_JOB_RECEIPT}", f"arms/{arm}/task-details.json",
            f"{runtime}/events.jsonl", f"{runtime}/submission-history.jsonl",
            f"{runtime}/comparison-display-start.json", f"{runtime}/comparison-display-end.json",
            f"capture-arms/{arm}/arm-timing.json",
        })
    return results


def native_job_paths(root):
    exec_paths, app_paths = set(), set()

    def fail(error):
        raise error

    for folder, directories, files in os.walk(root, onerror=fail, followlinks=False):
        path = Path(folder)
        names = set(files)
        # These are produced at the native Exec worker boundary, including in
        # a directory the planned allocation may later reject.
        if "model-call" in directories or names & {"windows-runner-stdout.txt", "windows-runner-stderr.txt"}:
            exec_paths.add(path)
        if "protocol.jsonl" in names:
            stream = (path / "protocol.jsonl").lstat()
            if not stat.S_ISREG(stream.st_mode) or stream.st_size:
                app_paths.add(path)
    return exec_paths, app_paths


def read_job_record(root, relative):
    path = audit.scoped_path(root, relative)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        audit.require(stat.S_ISREG(info.st_mode) and info.st_size <= 64_000,
                      "invalid native owner receipt file")
        data = stream.read(64_001)
        audit.require(data.endswith(b"\n") or path.name in {audit.START_RECORD, audit.APP_SERVER_JOB_START},
                      "native owner terminal receipt write is incomplete")
        return json.loads(data)


def native_writers_retired(root, *, require_all=False):
    if root.is_symlink():
        return False
    if not root.exists():
        return not require_all
    try:
        exec_paths, app_paths = native_job_paths(root)
        planned_exec = {
            root / "preflight" / arm / "gate" / (("plain" if arm == "plain" else "compiled") + "-form-grounding")
            for arm in audit.ARMS
        }
        planned_apps = {root / "native-app-server" / arm for arm in audit.ARMS}
        for start_name, receipt_name, schema, observed, planned in (
            (audit.START_RECORD, audit.RECEIPT, "native-preflight-windows-job-v1", exec_paths, planned_exec),
            (audit.APP_SERVER_JOB_START, audit.APP_SERVER_JOB_RECEIPT,
             "native-app-server-windows-job-v1", app_paths, planned_apps),
        ):
            starts = {path.parent for path in root.rglob(start_name)}
            receipts = {path.parent for path in root.rglob(receipt_name)}
            if starts != receipts or not observed <= starts or (require_all and starts != planned):
                return False
            for directory in starts:
                relative = directory.relative_to(root)
                start = read_job_record(root, relative / start_name)
                receipt = read_job_record(root, relative / receipt_name)
                if not (audit.valid_hex(start.get("run_nonce"), 32)
                        and audit.valid_hex(start.get("owner_sha256"), 64)
                        and receipt.get("run_nonce") == start["run_nonce"]
                        and receipt.get("owner_sha256") == start["owner_sha256"]
                        and receipt.get("schema") == schema
                        and receipt.get("ownership") == "create-process-job-list"
                        and receipt.get("status") in {"COMPLETED", "OWNER_LOST", "TIMED_OUT",
                                                      "DESCENDANTS_ACTIVE", "STOP_REQUESTED"}
                        and receipt.get("job_empty") is True
                        and type(receipt.get("active_processes")) is int and receipt["active_processes"] == 0
                        and type(receipt.get("exit_code")) is int
                        and type(receipt.get("total_processes")) is int and receipt["total_processes"] >= 1):
                    return False
        return True
    except (OSError, ValueError, TypeError, AttributeError):
        return False


def snapshot(root, expected, *, all_files, settled=True, unsettled_reason="service_retirement_unverified"):
    if not settled:
        return {"state": "unsettled", "files": {}, "missing": None,
                "unsealed": {".": unsettled_reason}}
    files, unavailable = {}, {}
    try:
        mode = root.lstat().st_mode
    except FileNotFoundError:
        return {"state": "absent", "files": {}, "missing": sorted(expected), "unsealed": {}}
    if not stat.S_ISDIR(mode):
        return {"state": "unreadable", "files": {}, "missing": None,
                "unsealed": {".": "non_directory_evidence_root"}}

    def collect(relative, name, directory_fd, *, listed=False):
        try:
            files[relative] = safe_file_digest(name, directory_fd)
        except FileNotFoundError:
            if listed:
                unavailable[relative] = "artifact_disappeared_during_capture"
        except ValueError as error:
            unavailable[relative] = str(error)
        except OSError as error:
            unavailable[relative] = type(error).__name__

    if all_files:
        def walk_error(error):
            path = Path(error.filename or root)
            unavailable[path.relative_to(root).as_posix()] = type(error).__name__

        for folder, directories, names, directory_fd in os.fwalk(root, onerror=walk_error, follow_symlinks=False):
            for directory in list(directories):
                relative = (Path(folder) / directory).relative_to(root).as_posix()
                try:
                    entry = os.stat(directory, dir_fd=directory_fd, follow_symlinks=False)
                except OSError as error:
                    directories.remove(directory)
                    unavailable[relative] = type(error).__name__
                    continue
                if not stat.S_ISDIR(entry.st_mode):
                    directories.remove(directory)
                    unavailable[relative] = "non_regular_artifact"
            for name in sorted(names):
                collect((Path(folder) / name).relative_to(root).as_posix(), name, directory_fd, listed=True)
    else:
        directory_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            for name in expected:
                collect(name, name, directory_fd)
        finally:
            os.close(directory_fd)
    missing = expected - files.keys() - unavailable.keys()
    return {"state": "observed", "files": files, "unsealed": unavailable,
            "missing": sorted(name for name in missing if not any(
                path == "." or name.startswith(path + "/") for path in unavailable))}


def preservation_summary(state):
    return {"status": "partial" if state["unsealed"] else "sealed", "state": state["state"],
            "files": len(state["files"]), "missing": state["missing"], "unsealed": state["unsealed"]}


def retain(allocation, plan_sha, host_names, *, settled, reason):
    out = {"disposition": "HOLD", "reason": reason, "accounting_verified": False,
           "evidence_scope": "partial_failure", "preservation": {}}
    raw_retired = settled and native_writers_retired(allocation / "raw")
    for scope, name, root, expected in (
        ("raw", RAW_SEAL, allocation / "raw", expected_raw_paths()),
        ("host", HOST_SEAL, allocation, set(host_names)),
    ):
        try:
            # The caller owns the host receipts. For a service still running,
            # capture only the caller's closed receipts on this failure path.
            safe_expected = expected if settled or scope == "raw" else {
                "claim.json", "service-result.json",
            }
            state = snapshot(root, safe_expected, all_files=scope == "raw", settled=raw_retired or scope == "host",
                             unsettled_reason=("windows_job_retirement_unverified" if settled
                                               else "service_retirement_unverified"))
            if scope == "host" and not settled:
                state["unsealed"].update({name: "service_retirement_unverified"
                                            for name in expected - safe_expected})
            payload = {"schema": "native_comparison_partial_seal_v1", "scope": scope,
                       "launch_plan_sha256": plan_sha,
                       "retirement_verified": raw_retired if scope == "raw" else settled, "reason": reason,
                       "snapshot": state}
            if scope == "host":
                payload["raw_seal_sha256"] = out.get("seal_sha256")
                payload["raw_retirement_verified"] = raw_retired
                payload["raw_preservation"] = out["preservation"].get("raw")
            path = allocation / name
            audit.write_record(path, payload)
            out["seal_sha256" if scope == "raw" else "host_seal_sha256"] = audit.digest(path)
            out["preservation"][scope] = preservation_summary(state)
        except (OSError, ValueError, TypeError) as error:
            out["preservation"][scope] = {"status": "failed", "reason": str(error)}
    return out


def verify(allocation, plan_sha, host_names, *, raw_digest, host_digest):
    raw_path, host_path = allocation / RAW_SEAL, allocation / HOST_SEAL
    audit.require(audit.valid_hex(host_digest, 64) and audit.digest(host_path) == host_digest,
                  "failed comparison host manifest differs from the retained partial digest")
    host = audit.read(host_path)
    settled = host.get("retirement_verified")
    raw_retired = host.get("raw_retirement_verified")
    audit.require(type(settled) is bool and host.get("raw_seal_sha256") == raw_digest
                  and type(raw_retired) is bool and (settled or not raw_retired)
                  and host.get("schema") == "native_comparison_partial_seal_v1"
                  and host.get("scope") == "host" and host.get("launch_plan_sha256") == plan_sha,
                  "failed comparison host manifest does not match its allocation")
    expected_host = set(host_names) if settled else {"claim.json", "service-result.json"}
    host_state = snapshot(allocation, expected_host, all_files=False)
    if not settled:
        host_state["unsealed"].update({name: "service_retirement_unverified"
                                        for name in set(host_names) - expected_host})
    audit.require(audit.same(host_state, host.get("snapshot")), "failed comparison host evidence changed after preservation")
    result = {"disposition": "HOLD", "reason": host["reason"], "accounting_verified": False,
              "evidence_scope": "partial_failure", "host_seal_sha256": host_digest,
              "preservation": {"raw": host["raw_preservation"], "host": preservation_summary(host_state),
                               "retirement_verified": settled}}
    if raw_digest is None:
        audit.require(host["raw_preservation"]["status"] == "failed", "missing retained partial raw digest")
        return {**result, "partial_manifests_verified": False, "host_manifest_verified": True}
    audit.require(audit.valid_hex(raw_digest, 64) and audit.digest(raw_path) == raw_digest,
                  "failed comparison raw manifest differs from the retained partial digest")
    raw = audit.read(raw_path)
    raw_state = snapshot(allocation / "raw", expected_raw_paths(), all_files=True, settled=raw_retired,
                         unsettled_reason=("windows_job_retirement_unverified" if settled
                                           else "service_retirement_unverified"))
    audit.require(raw.get("schema") == "native_comparison_partial_seal_v1"
                  and raw.get("scope") == "raw" and raw.get("launch_plan_sha256") == plan_sha
                  and raw.get("retirement_verified") is raw_retired and raw.get("reason") == host["reason"],
                  "failed comparison raw manifest does not match its allocation")
    audit.require(audit.same(raw_state, raw.get("snapshot")), "failed comparison raw evidence changed after preservation")
    return {**result, "seal_sha256": raw_digest, "partial_manifests_verified": True}
