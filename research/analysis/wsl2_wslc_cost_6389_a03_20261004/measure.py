"""Windows-host orchestrator for the A03 three-pair WSL2/WSLc comparison."""
from __future__ import annotations

import hashlib
import json
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent
SOURCE = ROOT / "research/analysis/belief_external_drift_5368_t0_20261003"
STAGER = ROOT / "research/analysis/wsl2_wslc_cost_6389_a01_20261004/stage_and_run.py"
FORMAL = PACKAGE / "formal"
IMAGE = "python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f"
BASE_MAIN = "2ed11c5552956499454e8a99acf5a2f374106d34"
IMAGE_DIGEST = "sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f"
LOCAL_IMAGE_ID = "sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4"
WSLC = Path(r"C:\Program Files\WSL\wslc.exe")
WSL = Path(r"C:\Windows\System32\wsl.exe")
EXPECTED = {
    "fixture.json": "374a6136bc5a0b5cfe39cce915625505c6a56cade870b20fb2e749aa4e7fe9d7",
    "candidate.py": "972b711c3a6c57e09d48652884c96491a70c5ef7ea183e96b052692c6bddee0a",
    "runner.py": "31a13ac9dee59d4d7d58fa7cb5c94afc9418477ca22d644459d6d01acf76ccdc",
    "audit.py": "81fe3dc715afb4f9e2039a513157f608fddfef950643e0bdd6431350f3a4ad4d",
}
OUTPUTS = ("formal_raw.jsonl", "sticky_baseline.jsonl", "age_baseline.jsonl")
ORDERS = (("native", "wslc"), ("wslc", "native"), ("native", "wslc"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest_gate_passes(image_table: str) -> bool:
    return IMAGE_DIGEST in image_table and LOCAL_IMAGE_ID in image_table


def wsl_path(path: Path) -> str:
    drive = path.drive[0].lower()
    tail = path.as_posix().split(":", 1)[1]
    return f"/mnt/{drive}{tail}"


def invoke(arm: str, mode: str, out: Path, input_dir: Path | None, pair_num: int) -> dict:
    preflight = []
    if arm == "native":
        args = [str(WSL), "-d", "Ubuntu", "--exec", "python3", "-B", wsl_path(STAGER), mode,
                wsl_path(SOURCE), wsl_path(out)]
        if input_dir is not None:
            args.append(wsl_path(input_dir))
    else:
        inventory = subprocess.run([str(WSLC), "container", "ls", "--quiet"], text=True,
                                   capture_output=True, encoding="utf-8", errors="replace", check=False)
        preflight.append({"name": "running_container_inventory", "command": [str(WSLC), "container", "ls", "--quiet"],
                          "exit_code": inventory.returncode, "stdout": inventory.stdout, "stderr": inventory.stderr})
        if inventory.returncode != 0 or inventory.stdout.strip():
            return {"arm": arm, "mode": mode, "gate_status": "STOP_WSLC_NOT_IDLE",
                    "command": [str(WSLC), "container", "ls", "--quiet"],
                    "exit_code": 125, "stdout": inventory.stdout, "stderr": inventory.stderr,
                    "external_elapsed_seconds": 0.0, "preflight": preflight}
        images = subprocess.run([str(WSLC), "images", "--digests", "--no-trunc"], text=True,
                                capture_output=True, encoding="utf-8", errors="replace", check=False)
        preflight.append({"name": "pinned_image_inventory", "command": [str(WSLC), "images", "--digests", "--no-trunc"],
                          "exit_code": images.returncode, "stdout": images.stdout, "stderr": images.stderr})
        if images.returncode != 0 or not digest_gate_passes(images.stdout):
            return {"arm": arm, "mode": mode, "gate_status": "STOP_PINNED_IMAGE_UNAVAILABLE",
                    "command": [str(WSLC), "images", "--digests", "--no-trunc"],
                    "exit_code": 125, "stdout": images.stdout, "stderr": images.stderr,
                    "external_elapsed_seconds": 0.0, "preflight": preflight}
        name = f"ai6389a03-p{pair_num}-{mode}"
        args = [str(WSLC), "run", "--rm", "--name", name, "--pull", "never", "--network", "none",
                "--cpus", "1", "--memory", "512M", "--volume", f"{SOURCE}:/source:ro",
                "--volume", f"{STAGER.parent}:/stager:ro", "--volume", f"{out}:/out:rw"]
        if input_dir is not None:
            args += ["--volume", f"{input_dir}:/input:ro"]
        args += [IMAGE, "python", "-B", "/stager/stage_and_run.py", mode, "/source", "/out"]
        if input_dir is not None:
            args.append("/input")
    started_utc = datetime.now(timezone.utc).isoformat()
    start = time.perf_counter()
    child = subprocess.run(args, text=True, capture_output=True, encoding="utf-8", errors="replace", check=False)
    elapsed = time.perf_counter() - start
    return {"arm": arm, "mode": mode, "command": args, "started_utc": started_utc,
            "ended_utc": datetime.now(timezone.utc).isoformat(), "external_elapsed_seconds": elapsed,
            "exit_code": child.returncode, "stdout": child.stdout, "stderr": child.stderr,
            "preflight": preflight}


def main() -> int:
    import os
    if os.name != "nt":
        raise RuntimeError("measure.py must be run by Windows Python")
    if FORMAL.exists():
        raise FileExistsError(f"formal output already exists: {FORMAL}")
    FORMAL.mkdir()
    journal = FORMAL / "events.jsonl"
    remote = subprocess.run(["git", "ls-remote", "origin", "refs/heads/main"], cwd=ROOT,
                            text=True, capture_output=True, encoding="utf-8", errors="replace", check=False)
    remote_line = remote.stdout.strip().splitlines()
    current_main = remote_line[0].split()[0] if remote.returncode == 0 and len(remote_line) == 1 else None
    if current_main != BASE_MAIN:
        event = {"status": "STOP_MAIN_ADVANCED_BEFORE_CANDIDATE", "expected_main": BASE_MAIN,
                 "observed_main": current_main, "command": ["git", "ls-remote", "origin", "refs/heads/main"],
                 "exit_code": remote.returncode, "stdout": remote.stdout, "stderr": remote.stderr,
                 "candidate_invocations": 0, "auditor_invocations": 0, "retry_count": 0}
        journal.write_text(json.dumps(event, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        summary = dict(event)
        with (FORMAL / "summary.json").open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(summary, stream, sort_keys=True, indent=2)
            stream.write("\n")
        print(json.dumps(summary, sort_keys=True))
        return 1
    for name, expected in EXPECTED.items():
        actual = sha(SOURCE / name)
        if actual != expected:
            raise ValueError(f"preflight_source_hash:{name}:{actual}:{expected}")
    if not STAGER.is_file() or not WSLC.is_file() or not WSL.is_file():
        raise FileNotFoundError("required stager or Windows runtime CLI missing")
    totals: dict[str, list[float]] = {"native": [], "wslc": []}
    reference_outputs = None
    reference_audit = None
    outcome = "PASS_PORTABILITY_ONLY"
    with journal.open("x", encoding="utf-8", newline="\n") as log:
        for pair_num, order in enumerate(ORDERS, 1):
            pair_durations = {}
            for arm in order:
                run = FORMAL / f"pair-{pair_num:02d}" / arm
                candidate_out, audit_out = run / "candidate", run / "audit"
                candidate_out.mkdir(parents=True)
                audit_out.mkdir()
                candidate = invoke(arm, "candidate", candidate_out, None, pair_num)
                log.write(json.dumps(candidate, sort_keys=True) + "\n")
                log.flush()
                if candidate["exit_code"] != 0 or set(OUTPUTS) - {p.name for p in candidate_out.iterdir()}:
                    outcome = candidate.get("gate_status", "STOP_OR_FAIL_CANDIDATE")
                    break
                candidate_hashes = {name: sha(candidate_out / name) for name in OUTPUTS}
                audit = invoke(arm, "audit", audit_out, candidate_out, pair_num)
                log.write(json.dumps(audit, sort_keys=True) + "\n")
                log.flush()
                pair_durations[arm] = candidate["external_elapsed_seconds"] + audit["external_elapsed_seconds"]
                if audit["exit_code"] != 0 or not (audit_out / "audit.json").is_file():
                    outcome = audit.get("gate_status", "FAIL_OR_STOP_AUDIT")
                    break
                audit_data = json.loads((audit_out / "audit.json").read_text(encoding="utf-8"))
                if (audit_data.get("status") != "PASS_METHOD_SCOPED" or audit_data.get("rows_received") != 9
                        or audit_data.get("unsafe_admissions") != 0 or audit_data.get("errors") != []
                        or sum(1 for m in audit_data.get("mutation_controls", []) if m.get("detected")) != 4):
                    outcome = "FAIL_AUDIT_GATE"
                    break
                totals[arm].append(pair_durations[arm])
            if outcome.startswith("STOP") or outcome.startswith("FAIL"):
                break
            native_hashes = {name: sha(FORMAL / f"pair-{pair_num:02d}" / "native" / "candidate" / name) for name in OUTPUTS}
            wslc_hashes = {name: sha(FORMAL / f"pair-{pair_num:02d}" / "wslc" / "candidate" / name) for name in OUTPUTS}
            if native_hashes != wslc_hashes:
                outcome = "FAIL_CANDIDATE_OUTPUT_MISMATCH"
                break
            audit_hashes = [sha(FORMAL / f"pair-{pair_num:02d}" / arm / "audit" / "audit.json") for arm in ("native", "wslc")]
            if audit_hashes[0] != audit_hashes[1]:
                outcome = "FAIL_AUDIT_OUTPUT_MISMATCH"
                break
            if reference_outputs is None:
                reference_outputs, reference_audit = native_hashes, audit_hashes[0]
            elif native_hashes != reference_outputs or audit_hashes[0] != reference_audit:
                outcome = "FAIL_REPEAT_OUTPUT_MISMATCH"
                break
    if outcome == "PASS_PORTABILITY_ONLY" and len(totals["native"]) == 3 and len(totals["wslc"]) == 3:
        native_med, wslc_med = statistics.median(totals["native"]), statistics.median(totals["wslc"])
        if native_med <= 0.9 * wslc_med:
            outcome = "PASS_COST_SCOPED"
        summary = {"status": outcome, "allocation": "6389-wsl2-vs-wslc-belief-replay-a03-20261004",
                   "native_pair_seconds": totals["native"], "wslc_pair_seconds": totals["wslc"],
                   "native_median_seconds": native_med, "wslc_median_seconds": wslc_med,
                   "native_relative_reduction": (wslc_med - native_med) / wslc_med,
                   "candidate_invocations_per_arm": 3, "auditor_invocations_per_arm": 3,
                   "retry_count": 0, "source_hashes": EXPECTED}
        with (FORMAL / "summary.json").open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(summary, stream, sort_keys=True, indent=2)
            stream.write("\n")
        print(json.dumps(summary, sort_keys=True))
        return 0 if outcome == "PASS_COST_SCOPED" else 2
    summary = {"status": outcome, "native_pair_seconds": totals["native"], "wslc_pair_seconds": totals["wslc"],
               "retry_count": 0, "source_hashes": EXPECTED}
    with (FORMAL / "summary.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(summary, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(json.dumps(summary, sort_keys=True))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
