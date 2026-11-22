#!/usr/bin/env python3
"""Read-only independent check of retained source and WSLc STOP evidence."""
import argparse, base64, hashlib, json, re
from pathlib import Path

TREE = "2ce07e058ed6b868ea97799e9a7b65deff21da71"
IMAGE = "python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016"
MODULES = [
    "test_input_owner_v12_cleanup_measurement.CleanupMeasurementTests",
    "test_input_owner_v12_key_measurement",
    "test_input_owner_v12_batch_sample_custody",
    "test_batch_key_measurement_composition",
    "test_input_owner_v12_explicit_up_cancel",
    "test_input_owner_v12_wheel_cleanup",
    "test_input_transition_owner_v4",
]
PIL = "ModuleNotFoundError: No module named 'PIL'"

def need(ok, label):
    if not ok:
        raise ValueError(label)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-dir", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / "SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
    plan = json.loads((root / "RUN_PLAN.json").read_text(encoding="utf-8"))
    execution = json.loads((root / "EXECUTION.json").read_text(encoding="utf-8"))
    need(manifest["git_tree"] == TREE and manifest["file_count"] == 1996, "source-manifest")
    need(manifest["total_bytes"] == 11194822, "source-total")
    need(plan["virtual_merge_tree"] == TREE and plan["modules"] == MODULES, "run-plan")
    need(execution["source_tree"] == TREE and execution["image"] == IMAGE, "execution-pins")
    need(execution["python"] == "3.12.15" and execution["active_containers_after"] == 0, "runtime-cleanup")
    files = {}
    total = 0
    for row in manifest["files"]:
        rel = row["path"]
        need(rel not in files, "duplicate:" + rel)
        files[rel] = row
        need(rel.endswith(".py") and len(row["sha256"]) == 64 and len(row["git_blob"]) == 40, "manifest-row:" + rel)
        data = (args.source_dir / rel).read_bytes()
        need(len(data) == row["bytes"], "source-size:" + rel)
        need(hashlib.sha256(data).hexdigest() == row["sha256"], "source-sha:" + rel)
        total += len(data)
    actual = {"research/" + p.relative_to(args.source_dir / "research").as_posix()
              for p in (args.source_dir / "research").rglob("*.py")}
    need(actual == set(files), "source-file-set")
    need(total == manifest["total_bytes"], "source-byte-total")
    checks = ["manifest-structure", "materialized-source-hashes", "source-file-set",
              "run-plan", "image-runtime", "container-cleanup"]
    modes = {}
    for mode in ("normal", "optimized"):
        run = execution["runs"][mode]
        need(run["exit_code"] == 1, mode + "-exit")
        streams = {}
        for kind in ("stdout", "stderr"):
            meta = run[kind]
            data = base64.b64decode((root / meta["path"]).read_bytes(), validate=True)
            need(len(data) == meta["bytes"], mode + "-" + kind + "-bytes")
            need(hashlib.sha256(data).hexdigest() == meta["sha256"], mode + "-" + kind + "-sha")
            streams[kind] = data.decode("utf-8", errors="strict")
        combined = streams["stdout"] + "\n" + streams["stderr"]
        need(re.findall(r"Ran (\d+) tests?", combined) == ["47"], mode + "-test-count")
        summary = re.findall(r"FAILED \(([^)]*)\)", combined)
        need(len(summary) == 1 and "errors=8" in summary[0], mode + "-summary")
        need(len(re.findall(r"(?m)^ERROR: (.+)$", combined)) == 8, mode + "-error-count")
        need(combined.count(PIL) == 8, mode + "-pil-errors")
        warning = "Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap."
        need(warning in streams["stderr"], mode + "-resource-warning")
        modes[mode] = {"exit_code": 1, "tests": 47, "errors": 8,
                       "error": PIL, "stdout_sha256": run["stdout"]["sha256"],
                       "stderr_sha256": run["stderr"]["sha256"]}
        checks.append(mode + "-raw-stop")
    result = {
        "schema": "v15-cleanup-crosspython-independent-audit-v1",
        "disposition": "PASS_AUDIT_STOP_ENVIRONMENT_DEPENDENCY",
        "candidate_disposition": "STOP_CONTAINER_IMAGE_MISSING_PIL",
        "source_tree": TREE, "source_files_checked": len(files),
        "source_bytes_checked": total, "check_count": len(checks),
        "checks": checks, "modes": modes,
        "scope": "read-only source/raw audit; no candidate code executed"
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"disposition": result["disposition"],
                      "candidate_disposition": result["candidate_disposition"],
                      "checks": len(checks), "source_files": len(files),
                      "source_bytes": total}, sort_keys=True))

if __name__ == "__main__":
    main()