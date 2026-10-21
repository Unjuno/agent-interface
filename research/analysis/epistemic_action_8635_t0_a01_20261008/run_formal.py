def verify_sources(root, expected):
    import hashlib

    errors = []
    for relative, digest in sorted(expected.items()):
        path = root / relative
        if not path.is_file():
            errors.append("missing frozen source: " + relative)
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != digest:
            errors.append("frozen source hash mismatch: " + relative)
    return errors


def reserve_output(path):
    path.mkdir(parents=True, exist_ok=False)
    return path


def build_wslc_command(wslc_exe, image, name, mount_source, script, *script_args):
    return [
        str(wslc_exe), "run", "--rm", "--pull", "never", "--network", "none",
        "--cpus", "1", "--user", "65534:65534", "--name", str(name),
        "--mount", f"type=bind,source={mount_source},target=/src,readonly",
        "--workdir", "/src", str(image), "python", f"/src/{script}", *map(str, script_args),
    ]


def prepare_candidate_stage(root, stage):
    import shutil
    from pathlib import Path

    root = Path(root)
    stage = Path(stage)
    stage.mkdir()
    names = ("candidate.py", "policies.py", "fixture.json")
    for name in names:
        shutil.copyfile(root / name, stage / name)
    return names


def prepare_auditor_stage(root, stage, raw_candidate):
    import shutil
    from pathlib import Path

    root = Path(root)
    stage = Path(stage)
    stage.mkdir()
    names = ("auditor.py", "fixture.json", "oracle.json")
    for name in names:
        shutil.copyfile(root / name, stage / name)
    (stage / "raw_candidate.json").write_bytes(raw_candidate)
    return (*names, "raw_candidate.json")


def run_once(root, output_dir, wslc_exe):
    import hashlib
    import json
    import platform
    import subprocess
    import sys
    import time
    from datetime import datetime, timezone
    from pathlib import Path

    root = Path(root).resolve()
    wslc_exe = str(wslc_exe)
    freeze = json.loads((root / "FREEZE.json").read_text(encoding="utf-8"))
    errors = verify_sources(root, freeze["files"])
    if errors:
        raise RuntimeError("freeze verification failed: " + "; ".join(errors))
    output_dir = reserve_output(Path(output_dir).resolve())

    image = freeze["image"]
    candidate_stage = output_dir / "candidate_input"
    candidate_input_files = prepare_candidate_stage(root, candidate_stage)

    started = datetime.now(timezone.utc).isoformat()
    candidate_command = build_wslc_command(
        wslc_exe,
        image,
        "epistemic-8635-candidate-a01",
        str(candidate_stage.resolve()),
        "candidate.py",
        "/src/fixture.json",
    )
    t0 = time.perf_counter_ns()
    launch_error = None
    try:
        candidate = subprocess.run(candidate_command, capture_output=True, check=False)
    except OSError as error:
        candidate = None
        launch_error = {"type": type(error).__name__, "message": str(error)}
    candidate_elapsed = time.perf_counter_ns() - t0
    candidate_stdout = candidate.stdout if candidate else b""
    candidate_stderr = candidate.stderr if candidate else (str(launch_error["message"]).encode("utf-8", errors="replace") if launch_error else b"")
    (output_dir / "raw_candidate.json").write_bytes(candidate_stdout)
    (output_dir / "candidate.stderr").write_bytes(candidate_stderr)

    auditor_command = None
    auditor = None
    auditor_elapsed = None
    if candidate and candidate.returncode == 0:
        auditor_stage = output_dir / "auditor_input"
        auditor_input_files = prepare_auditor_stage(root, auditor_stage, candidate.stdout)
        auditor_command = build_wslc_command(
            wslc_exe,
            image,
            "epistemic-8635-auditor-a01",
            str(auditor_stage.resolve()),
            "auditor.py",
            "--fixture", "/src/fixture.json",
            "--oracle", "/src/oracle.json",
            "--candidate", "/src/raw_candidate.json",
        )
        t1 = time.perf_counter_ns()
        auditor = subprocess.run(auditor_command, capture_output=True, check=False)
        auditor_elapsed = time.perf_counter_ns() - t1
        (output_dir / "raw_audit.json").write_bytes(auditor.stdout)
        (output_dir / "auditor.stderr").write_bytes(auditor.stderr)
    else:
        (output_dir / "raw_audit.json").write_bytes(b"")
        (output_dir / "auditor.stderr").write_bytes(b"")

    auditor_stdout = auditor.stdout if auditor else b""
    auditor_stderr = auditor.stderr if auditor else b""
    try:
        audit = json.loads(auditor_stdout)
        audit_valid = True
    except (UnicodeDecodeError, json.JSONDecodeError):
        audit = None
        audit_valid = False

    def digest(data):
        return hashlib.sha256(data).hexdigest()

    receipt = {
        "allocation": "EPISTEMIC-ACTION-8635-T0-A01-20261008",
        "schema": "epistemic-action-run-v1",
        "started_utc": started,
        "platform": platform.platform(),
        "host_python": sys.version,
        "source_hashes_verified": True,
        "runtime": "WSLc",
        "wslc_executable": wslc_exe,
        "image": image,
        "candidate_command": candidate_command,
        "candidate_invocations": 1 if candidate else 0,
        "candidate_exit_code": candidate.returncode if candidate else None,
        "candidate_elapsed_ns": candidate_elapsed,
        "candidate_stdout_bytes": len(candidate_stdout),
        "candidate_stdout_sha256": digest(candidate_stdout),
        "candidate_stderr_bytes": len(candidate_stderr),
        "candidate_stderr_sha256": digest(candidate_stderr),
        "candidate_input_files": candidate_input_files,
        "auditor_command": auditor_command,
        "auditor_invocations": 1 if auditor else 0,
        "auditor_exit_code": auditor.returncode if auditor else None,
        "auditor_elapsed_ns": auditor_elapsed,
        "auditor_stdout_bytes": len(auditor_stdout),
        "auditor_stdout_sha256": digest(auditor_stdout),
        "auditor_stderr_bytes": len(auditor_stderr),
        "auditor_stderr_sha256": digest(auditor_stderr),
        "auditor_input_files": list(auditor_input_files) if auditor else [],
        "auditor_output_valid": audit_valid,
        "retries": 0,
        "formal_disposition": audit.get("method_disposition", "HOLD") if audit else "HOLD",
        "hypothesis_disposition": audit.get("hypothesis_disposition", "HOLD") if audit else "HOLD",
    }
    if launch_error:
        receipt["launch_error"] = launch_error
    (output_dir / "RUN.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return receipt


def main():
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--wslc-exe", default=r"C:\Program Files\WSL\wslc.exe")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    receipt = run_once(root, root / args.output_dir, args.wslc_exe)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["formal_disposition"] == "PASS_METHOD_SCOPED" and receipt["hypothesis_disposition"] == "H_PASS_SCOPED" and receipt["candidate_exit_code"] == 0 and receipt["auditor_exit_code"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
