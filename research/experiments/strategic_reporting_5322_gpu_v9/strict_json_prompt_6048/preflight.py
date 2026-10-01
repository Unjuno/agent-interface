#!/usr/bin/env python3
"""Read-only CPU/host gate; does not import torch or load a model."""
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
SNAPSHOT = (Path.home() / ".cache" / "huggingface" / "hub" /
            "models--Qwen--Qwen2.5-0.5B-Instruct" / "snapshots" /
            FREEZE["model_revision"])
OUTDIR = HERE / "results" / "candidate-01"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_hashes():
    manifest_path = HERE / "SOURCE_HASHES.json"
    if sha256(manifest_path) != FREEZE.get("source_manifest_sha256"):
        return False, {}
    expected = json.loads(manifest_path.read_text(encoding="utf-8"))
    actual = {name: sha256(HERE / name) for name in expected}
    return expected == actual, actual


def smi(args):
    proc = subprocess.run(["nvidia-smi", *args], capture_output=True,
                          text=True, timeout=10, check=True)
    return proc.stdout.strip()


def main():
    now = datetime.now(timezone.utc)
    errors = []
    start = datetime.fromisoformat(FREEZE["window_start_utc"].replace("Z", "+00:00"))
    end = datetime.fromisoformat(FREEZE["window_end_utc"].replace("Z", "+00:00"))
    if not start <= now <= end:
        errors.append("outside_reserved_window")
    if OUTDIR.exists():
        errors.append("output_collision")
    src_ok, actual_sources = source_hashes()
    if not src_ok:
        errors.append("source_hash_mismatch")
    frozen_files = [".gitattributes", "research/experiments/strategic_reporting_5322_gpu_v9/strict_json_prompt_6048/FREEZE.json",
                    "research/experiments/strategic_reporting_5322_gpu_v9/strict_json_prompt_6048/SOURCE_HASHES.json",
                    "research/experiments/strategic_reporting_5322_gpu_v9/strict_json_prompt_6048/INPUT.json",
                    "research/experiments/strategic_reporting_5322_gpu_v9/strict_json_prompt_6048/protocol.py",
                    "research/experiments/strategic_reporting_5322_gpu_v9/strict_json_prompt_6048/test_protocol.py",
                    "research/experiments/strategic_reporting_5322_gpu_v9/strict_json_prompt_6048/preflight.py",
                    "research/experiments/strategic_reporting_5322_gpu_v9/strict_json_prompt_6048/generate_one.py",
                    "research/experiments/strategic_reporting_5322_gpu_v9/strict_json_prompt_6048/audit.py",
                    "research/experiments/strategic_reporting_5322_gpu_v9/strict_json_prompt_6048/test_audit_contract.py",
                    "research/experiments/strategic_reporting_5322_gpu_v9/strict_json_prompt_6048/RUNBOOK.md"]
    try:
        subprocess.run(["git", "diff", "--quiet", "HEAD", "--", *frozen_files],
                       cwd=ROOT, check=True, timeout=5)
        subprocess.run(["git", "ls-files", "--error-unmatch", *frozen_files],
                       cwd=ROOT, check=True, stdout=subprocess.DEVNULL, timeout=5)
    except Exception:
        errors.append("frozen_source_not_committed_or_worktree_dirty")
    input_bytes = (HERE / "INPUT.json").read_bytes()
    input_digest = hashlib.sha256(input_bytes).hexdigest()
    if input_digest != FREEZE.get("input_sha256"):
        errors.append("input_hash_mismatch")
    try:
        from protocol import make_report
        frozen_input = json.loads(input_bytes.decode("utf-8"))
        if frozen_input != make_report(FREEZE["data_seed"]):
            errors.append("input_seed_reconstruction_mismatch")
    except Exception as exc:
        errors.append("input_validation_failed:" + type(exc).__name__)
    model_file = SNAPSHOT / FREEZE["model_file"]
    model_digest = sha256(model_file) if model_file.is_file() else None
    if model_digest != FREEZE["model_sha256"]:
        errors.append("model_missing_or_hash_mismatch")
    tokenizer_files = {}
    if SNAPSHOT.is_dir():
        for path in sorted(p for p in SNAPSHOT.rglob("*")
                           if p.is_file() and p.name != FREEZE["model_file"]):
            tokenizer_files[path.relative_to(SNAPSHOT).as_posix()] = sha256(path)
    else:
        errors.append("snapshot_missing")
    tokenizer_manifest = json.dumps(tokenizer_files, sort_keys=True,
                                   separators=(",", ":")).encode("utf-8")
    tokenizer_digest = hashlib.sha256(tokenizer_manifest).hexdigest()
    if tokenizer_digest != FREEZE.get("tokenizer_manifest_sha256"):
        errors.append("tokenizer_manifest_hash_mismatch")
    if tokenizer_files != FREEZE.get("tokenizer_file_hashes"):
        errors.append("tokenizer_file_inventory_mismatch")
    try:
        gpu_text = smi(["--query-gpu=index,name,uuid,driver_version,memory.total,memory.used,utilization.gpu",
                        "--format=csv,noheader"])
        process_text = smi(["--query-compute-apps=pid,process_name,used_memory",
                            "--format=csv,noheader"])
        if "RTX 3080" not in gpu_text:
            errors.append("RTX3080_not_visible")
        if process_text and "No running processes found" not in process_text:
            errors.append("preexisting_compute_process")
    except Exception as exc:
        gpu_text = ""
        process_text = ""
        errors.append("nvidia_smi_preflight_failed:" + type(exc).__name__)
    try:
        versions = {name: importlib.metadata.version(name)
                    for name in ("torch", "transformers", "safetensors")}
    except importlib.metadata.PackageNotFoundError as exc:
        versions = {}
        errors.append("required_package_missing:" + str(exc))
    actual_python = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    expected_packages = {name: FREEZE["runtime"][name] for name in versions}
    if versions != expected_packages or actual_python != FREEZE["runtime"]["python"]:
        errors.append("runtime_version_mismatch")
    try:
        disk = shutil.disk_usage(SNAPSHOT if SNAPSHOT.exists() else Path.home())
        free_bytes = disk.free
    except OSError:
        free_bytes = 0
        errors.append("disk_inventory_failed")
    if free_bytes < 1_000_000_000:
        errors.append("less_than_1GB_free")
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=HERE,
                                       text=True, timeout=5).strip()
    except Exception:
        head = None
        errors.append("git_head_unavailable")
    try:
        main_ref = subprocess.check_output(
            ["git", "rev-parse", "origin/main"], cwd=HERE, text=True, timeout=5
        ).strip()
        merge_base = subprocess.check_output(
            ["git", "merge-base", "HEAD", "origin/main"],
            cwd=HERE, text=True, timeout=5
        ).strip()
    except Exception:
        main_ref = merge_base = None
        errors.append("current_main_ref_unavailable")
    if main_ref != FREEZE["main_sha_at_run"] or merge_base != FREEZE["main_sha_at_run"]:
        errors.append("worktree_not_based_on_frozen_current_main")
    receipt = {
        "allocation_id": FREEZE["allocation_id"],
        "checked_utc": now.isoformat(),
        "main_sha": head,
        "source_hashes": actual_sources,
        "input_sha256": input_digest,
        "model_path": str(SNAPSHOT),
        "model_sha256": model_digest,
        "tokenizer_file_hashes": tokenizer_files,
        "tokenizer_manifest_sha256": tokenizer_digest,
        "versions": versions,
        "disk_free_bytes": free_bytes,
        "nvidia_smi_gpu": gpu_text,
        "nvidia_smi_compute_processes": process_text,
        "container_or_wsl_workload": "not used by this allocation",
        "errors": errors,
        "load_authorized": not errors,
    }
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / "PREFLIGHT.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"load_authorized": not errors, "errors": errors,
                      "model_sha256": model_digest, "tokenizer_manifest_sha256": tokenizer_digest,
                      "disk_free_bytes": free_bytes}, sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
