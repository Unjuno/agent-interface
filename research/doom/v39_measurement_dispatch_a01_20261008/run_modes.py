"""Run the frozen dispatch check without modifying retained package evidence."""
import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUN = HERE / "run.py"
AUDIT_PATH = HERE / "audit.py"


def output_directory(value):
    if value is None:
        temp_root = Path(tempfile.gettempdir()).resolve()
        if temp_root == HERE or HERE in temp_root.parents:
            raise SystemExit("refusing system temporary directory inside the retained package")
        if shutil.disk_usage(temp_root).free < 65536:
            raise SystemExit("insufficient free space for temporary rerun output; pass --output-dir on another volume")
        return Path(tempfile.mkdtemp(prefix="v39-measurement-dispatch-a01-", dir=temp_root))
    path = Path(value).expanduser().resolve()
    if path == HERE or HERE in path.parents:
        raise SystemExit("refusing output directory inside the retained package")
    if path.exists():
        raise SystemExit(f"refusing existing output directory: {path}")
    space_probe = path.parent
    while not space_probe.exists():
        space_probe = space_probe.parent
    if shutil.disk_usage(space_probe).free < 65536:
        raise SystemExit("insufficient free space for rerun output; choose a path on another volume")
    path.mkdir(parents=True, exist_ok=False)
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path,
                        help="new, non-existing directory outside this evidence package")
    args = parser.parse_args()
    out = output_directory(args.output_dir)

    spec = importlib.util.spec_from_file_location("dispatch_audit", AUDIT_PATH)
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    outputs = {}
    for mode, optimize in (("normal", []), ("optimized", ["-O"])):
        proc = subprocess.run(
            [sys.executable, *optimize, "-B", str(RUN)], cwd=REPO,
            capture_output=True, text=True)
        outputs[mode] = {"exit_code": proc.returncode,
                         "stdout": proc.stdout, "stderr": proc.stderr}
        if proc.returncode:
            raise SystemExit(f"{mode} candidate failed: {proc.stderr}")
    if outputs["normal"]["stdout"] != outputs["optimized"]["stdout"]:
        raise SystemExit("normal/optimized outputs differ")

    result = json.loads(outputs["normal"]["stdout"])
    audit_result = audit.audit_result(result)
    if audit_result["status"] != "PASS_DISPATCH_CONSTRUCTION":
        raise SystemExit(f"independent audit failed: {audit_result}")
    for field, value in (("modes", "mutated"), ("instrumentation_chain", "mutated")):
        changed = json.loads(json.dumps(result))
        changed[field] = value
        if audit.audit_result(changed)["status"] != "FAIL_DISPATCH_CONSTRUCTION":
            raise SystemExit(f"audit accepted mutated {field}")

    (out / "normal.stdout").write_text(outputs["normal"]["stdout"], encoding="utf-8")
    (out / "optimized.stdout").write_text(outputs["optimized"]["stdout"], encoding="utf-8")
    (out / "normal.stderr").write_text(outputs["normal"]["stderr"], encoding="utf-8")
    (out / "optimized.stderr").write_text(outputs["optimized"]["stderr"], encoding="utf-8")
    (out / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "AUDIT.json").write_text(json.dumps(audit_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    run_record = {mode: {"exit_code": row["exit_code"]} for mode, row in outputs.items()}
    (out / "RUN.json").write_text(json.dumps({"runs": run_record, "mutation_controls": 2},
                                                indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted(out.iterdir()) if path.is_file()}
    (out / "SHA256SUMS.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"results_dir": str(out), "normal_exit": outputs["normal"]["exit_code"],
                      "optimized_exit": outputs["optimized"]["exit_code"],
                      "byte_identical": True, "audit": audit_result["status"],
                      "mutation_controls": 2, "disposition": result["disposition"]}, sort_keys=True))


if __name__ == "__main__":
    main()
