"""Read-only retained evidence validation. Never launches WSLc, Xvfb or input."""
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile

from audit import inspect

ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def row_custody_errors(root, row):
    errors = []
    app = row["app"]
    for filename, expected, label in [
        ("app_result.json", app, "app_result_binding"),
        ("ready.json", row["ready"], "ready_binding"),
        ("first_visual.json", app["first_visual"], "first_visual_binding"),
    ]:
        try:
            value = json.loads((Path(root) / filename).read_bytes())
        except (OSError, ValueError):
            value = None
        if value != expected:
            errors.append(label)
    try:
        stdout_app = json.loads(row["app_stdout"].strip().splitlines()[-1])
    except (ValueError, IndexError):
        stdout_app = None
    if stdout_app != app:
        errors.append("app_stdout_binding")
    if row["app_pid"] != app.get("pid"):
        errors.append("app_pid_binding")
    return errors


def manifest_errors(root, lines):
    errors = []
    seen = set()
    for line in lines:
        expected, separator, name = line.partition("  ")
        path = Path(name)
        if (not separator or not re.fullmatch(r"[a-f0-9]{64}", expected)
                or not name or path.is_absolute() or ".." in path.parts
                or "\\" in name or ":" in name):
            errors.append("unsafe_manifest_path")
            continue
        if name in seen:
            errors.append("duplicate_manifest_path")
        seen.add(name)
        try:
            actual = sha(Path(root) / path)
        except OSError:
            actual = None
        if actual != expected:
            errors.append("manifest_hash:" + name)
    return errors


def main():
    errors = []
    freeze = json.loads((ROOT / "FREEZE.json").read_bytes())
    run = json.loads((ROOT / "RUN.json").read_bytes())
    source_binding = {"freeze_sha256": sha(ROOT / "FREEZE.json"),
        "fixture_sha256": sha(ROOT / "fixture.json"),
        "source_sha256": {name: freeze["sha256"][name] for name in
            ("candidate.py", "app.py", "schedule.py", "fixture.json", "audit.py")}}
    for name, expected in freeze["sha256"].items():
        if sha(ROOT / name) != expected:
            errors.append("frozen_source:" + name)
    input_dir = ROOT / "results/formal01-candidate-data"
    raw_path = input_dir / "candidate_stdout.json"
    raw = json.loads(raw_path.read_bytes())
    audit = json.loads((ROOT / "results/formal01-auditor-launch/stdout.bin").read_bytes())
    fixture = json.loads((ROOT / "fixture.json").read_bytes())
    rebuilt = inspect(raw_path, input_dir, image_audit=False,
                      expected_fixture=fixture, binding=source_binding)
    errors.extend("raw_audit:" + err for err in rebuilt["errors"])
    if audit["status"] != "PASS_AUDIT" or audit["errors"]:
        errors.append("retained_auditor_failed")
    for field in ("rows", "exact_save_failures", "baseline_image_integrity_rows"):
        if audit[field] != rebuilt[field]:
            errors.append("audit_reconstruction:" + field)
    for group, values in rebuilt["groups"].items():
        for field in ("n", "exact_save", "first_key_target", "first_visual"):
            if audit["groups"].get(group, {}).get(field) != values[field]:
                errors.append("group_reconstruction:" + group + ":" + field)
    if raw["row_count"] != 96 or raw["rows_completed"] != 96:
        errors.append("formal_cardinality")
    if raw["environment"]["image_id"] != freeze["image"]["id"]:
        errors.append("image_binding")
    if any(raw["environment"][name] != 0 for name in ("xvfb_exit", "openbox_exit")):
        errors.append("private_process_cleanup")
    pids = [row["app_pid"] for row in raw["rows"]]
    if len(set(pids)) != 96:
        errors.append("fresh_app_pid_cardinality")
    for index, row in enumerate(raw["rows"]):
        errors.extend(f"row_{index}:" + error for error in
            row_custody_errors(input_dir / f"row-{index:03d}", row))
    for role in ("candidate", "auditor"):
        directory = ROOT / f"results/formal01-{role}-launch"
        receipt = json.loads((directory / "receipt.json").read_bytes())
        if receipt["exit_code"] != 0 or receipt["launch_error"] is not None:
            errors.append(role + "_launch_failed")
        binding = receipt["binding"]
        if binding["source_commit"] != run["source_freeze_commit"]:
            errors.append(role + "_source_commit")
        if binding["freeze_sha256"] != source_binding["freeze_sha256"]:
            errors.append(role + "_freeze_sha256")
        if binding["source_sha256"] != freeze["sha256"]:
            errors.append(role + "_source_sha256")
        if receipt["argv"] != freeze["commands"][role]:
            errors.append(role + "_argv")
        for name, expected in receipt["output_sha256"].items():
            if sha(directory / name) != expected:
                errors.append(role + "_stream_hash:" + name)
        if role == "auditor" and binding["candidate_raw_sha256"] != sha(raw_path):
            errors.append("auditor_input_sha256")
    if sha(raw_path) != run["candidate_raw_sha256"]:
        errors.append("run_candidate_raw_sha256")
    if sha(ROOT / "results/formal01-auditor-launch/stdout.bin") != run["auditor_raw_sha256"]:
        errors.append("run_auditor_raw_sha256")

    # Corruption copies use the ORIGINAL read-only image directory.
    # No GUI/container/input command is called and no retained file is edited.
    mutations = {
        "schema": lambda r: r.update(schema="wrong"),
        "missing_row": lambda r: r["rows"].pop(),
        "coordinate": lambda r: r["rows"][0]["injection"].update(x=0),
        "map_order": lambda r: r["rows"][0]["ready"]["map_configure_events"][0].update(
            monotonic_ns=r["rows"][0]["injection"]["click_started_ns"] + 1),
        "geometry": lambda r: r["rows"][0]["ready"]["geometry"].update(target_width=0),
        "baseline_hash": lambda r: r["rows"][0]["ready"]["baseline_frame"].update(sha256="0"*64),
        "baseline_size": lambda r: r["rows"][0]["ready"]["baseline_frame"].update(bytes=1),
        "frame_hash": lambda r: r["rows"][0]["app"]["first_visual"]["frame"].update(sha256="0"*64),
        "frame_size": lambda r: r["rows"][0]["app"]["first_visual"]["frame"].update(bytes=1),
        "save_count": lambda r: r["rows"][0]["app"].update(save_count=2),
        "visual_order": lambda r: r["rows"][0]["app"]["first_visual"].update(observed_ns=0),
        "app_exit": lambda r: r["rows"][0].update(app_exit=1),
        "freeze_binding": lambda r: r.update(freeze_sha256="wrong"),
        "fixture_binding": lambda r: r.update(fixture_sha256="wrong"),
        "source_binding": lambda r: r.update(source_sha256={}),
    }
    rejected = {}
    with tempfile.TemporaryDirectory(prefix="5260-a02-audit-controls-") as scratch:
        for name, mutation in mutations.items():
            changed = copy.deepcopy(raw)
            mutation(changed)
            path = Path(scratch) / (name + ".json")
            path.write_text(json.dumps(changed), encoding="utf-8")
            result = inspect(path, input_dir, image_audit=False,
                             expected_fixture=fixture, binding=source_binding)
            rejected[name] = bool(result["errors"])
            if not rejected[name]:
                errors.append("accepted_corruption:" + name)
    lines = (ROOT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
    errors.extend(manifest_errors(ROOT, lines))
    names = {line.partition("  ")[2] for line in lines}
    actual_names = {str(p.relative_to(ROOT)).replace("\\", "/")
                    for p in ROOT.rglob("*") if p.is_file()
                    and "__pycache__" not in p.parts and p.name != "SHA256SUMS.txt"}
    if names != actual_names:
        errors.append("manifest_file_set")
    print(json.dumps({"status": "PASS_RETAINED_PACKET" if not errors else "FAIL",
        "errors": errors, "rows": rebuilt["rows"], "exact_save": 96 - rebuilt["exact_save_failures"],
        "initial_h_failures": rebuilt["exact_save_failures"],
        "manifest_files": len(lines), "corruptions_rejected": rejected,
        "formal_commands_executed": 0}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
