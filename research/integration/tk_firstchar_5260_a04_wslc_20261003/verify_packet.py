"""Read-only A04 retained qualification; never launches GUI, input or WSLc."""
import copy
from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import tempfile
from audit import inspect

ROOT = Path(__file__).resolve().parent
BINDING_SOURCES = ("candidate.py", "app.py", "schedule.py", "fixture.json", "audit.py",
                   "readiness_once.py", "ready_guard.py")

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def manifest_errors(root, lines):
    root = Path(root).resolve()
    errors, seen = [], set()
    for line in lines:
        expected, separator, name = line.partition("  ")
        path = PurePosixPath(name)
        if (not separator or not re.fullmatch(r"[a-f0-9]{64}", expected) or
                not name or path.is_absolute() or ".." in path.parts or
                "\\" in name or ":" in name or name == "SHA256SUMS"):
            errors.append("unsafe_manifest_path")
            continue
        target = (root / name).resolve()
        if root not in target.parents:
            errors.append("escaping_manifest_path")
            continue
        if name in seen:
            errors.append("duplicate_manifest_path")
        seen.add(name)
        try:
            if sha(target) != expected:
                errors.append("manifest_hash:" + name)
        except OSError:
            errors.append("manifest_missing:" + name)
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*")
              if p.is_file() and p.relative_to(root).as_posix() != "SHA256SUMS"
              and "__pycache__" not in p.parts}
    if seen != actual:
        errors.append("incomplete_manifest")
    return errors

def stream_errors(root, receipt):
    root = Path(root)
    errors = []
    try:
        attempt = json.loads((root / "attempt.json").read_bytes())
        for key in ("argv", "started_utc", "binding"):
            if attempt.get(key) != receipt.get(key):
                errors.append("attempt:" + key)
        names = ("attempt.json", "stdout.bin", "stderr.bin")
        actual = {n: sha(root / n) for n in names}
        if receipt["output_sha256"] != actual:
            errors.append("stream_hashes")
        if receipt["exit_code"] != 0 or receipt["launch_error"] is not None:
            errors.append("exit")
        start = datetime.fromisoformat(receipt["started_utc"])
        finish = datetime.fromisoformat(receipt["finished_utc"])
        if start.tzinfo is None or finish.tzinfo is None or finish < start or receipt["wall_seconds"] <= 0:
            errors.append("clocks")
    except (OSError, KeyError, TypeError, ValueError):
        errors.append("malformed_receipt")
    return errors

def visual_file_errors(root, row):
    try:
        value = json.loads((Path(root) / "first_visual.json").read_bytes())
    except (OSError, ValueError):
        value = None
    return [] if value == row["app"].get("first_visual") else ["first_visual_file_binding"]

def allocation_errors(raw, freeze, fixture):
    errors = []
    if len(raw["rows"]) != freeze["budget"]["rows"] or raw["rows_completed"] != freeze["budget"]["rows"]:
        errors.append("allocation_cardinality")
    env = raw["environment"]
    if env["image_id"] != freeze["image"]["id"] or env["display"] != fixture["private_display"] or env["screen"] != fixture["screen"]:
        errors.append("allocation_environment")
    if env["xvfb_exit"] != 0 or env["openbox_exit"] != 0:
        errors.append("private_cleanup")
    pids = [row["app_pid"] for row in raw["rows"]]
    if len(set(pids)) != len(pids):
        errors.append("fresh_processes")
    for index, row in enumerate(raw["rows"]):
        keys = row["injection"]["key_requests"]
        if ([key["char"] for key in keys] != list(fixture["payload"]) or
                [key["index"] for key in keys] != list(range(len(fixture["payload"])))):
            errors.append(f"row_{index}:dispatch_identity")
    return errors

def run_statistics_errors(run, audit, retained, raw, freeze_sha):
    h_before_focus = 0
    for row in raw["rows"]:
        app = row["app"]
        if app["saved_text"] == raw["fixture"]["payload"]:
            continue
        h = next((e for e in app["events"] if e["kind"] == "KeyPress" and e.get("char") == raw["fixture"]["payload"][0]), None)
        focus = next((e for e in app["events"] if e["kind"] == "FocusIn" and e.get("widget") == "target"), None)
        if h and focus and h["widget"] == "decoy" and h["monotonic_ns"] < focus["monotonic_ns"]:
            h_before_focus += 1
    expected = {"allocation": raw["allocation"], "freeze_sha256": freeze_sha,
        "rows": audit["rows"], "exact_save": audit["rows"]-audit["exact_save_failures"],
        "nonexact_save": audit["exact_save_failures"],
        "baseline_integrity_rows": audit["baseline_image_integrity_rows"],
        "ready_custody_failures": sum("readiness:" in e for e in audit["errors"]),
        "ocr_matches": sum(e["ocr_status"] == "MATCH" for e in retained["first_visual_ocr_rows"]),
        "first_h_in_decoy_before_target_focus_failures": h_before_focus,
        "formal_candidate_invocations": 1, "formal_auditor_invocations": 1, "retries": 0}
    return ["run_statistics:" + key for key, value in expected.items()
            if run.get(key) != value or type(run.get(key)) is not type(value)]

def corruptions(raw_path, data, freeze, fixture, binding):
    original = json.loads(Path(raw_path).read_bytes())
    controls = {
        "schema": lambda r: r.update(schema="invalid"),
        "missing_row": lambda r: r["rows"].pop(),
        "source_binding": lambda r: r.update(source_sha256={}),
        "freeze_binding": lambda r: r.update(freeze_sha256="invalid"),
        "fixture_binding": lambda r: r["fixture"].update(seed=-1),
        "image_binding": lambda r: r["environment"].update(image_id="invalid"),
        "app_exit": lambda r: r["rows"][0].update(app_exit=1),
        "ready_epoch": lambda r: r["rows"][0]["ready"].update(ready_ns=r["rows"][0]["ready"]["ready_ns"]+1),
        "ready_witness": lambda r: r["rows"][0]["ready"]["readiness"].update(finalizations=2),
        "app_pid": lambda r: r["rows"][0].update(app_pid=-1),
        "app_snapshot": lambda r: r["rows"][0]["app"].update(ready_snapshot={}),
        "coordinate": lambda r: r["rows"][0]["injection"].update(x=0,y=0),
        "dispatch_char": lambda r: r["rows"][0]["injection"]["key_requests"][0].update(char="wrong"),
        "frame_hash": lambda r: r["rows"][0]["app"]["first_visual"]["frame"].update(sha256="invalid"),
        "frame_size": lambda r: r["rows"][0]["app"]["first_visual"]["frame"].update(bytes=1),
        "baseline_hash": lambda r: r["rows"][0]["ready"]["baseline_frame"].update(sha256="invalid"),
        "save_count": lambda r: r["rows"][0]["app"].update(save_count=0),
    }
    rejected = {}
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "mutant.json"
        for name, mutate in controls.items():
            raw = copy.deepcopy(original)
            mutate(raw)
            path.write_text(json.dumps(raw), encoding="utf-8")
            audit = inspect(path, data, image_audit=False, expected_fixture=fixture, binding=binding)
            rejected[name] = bool(audit["errors"] + allocation_errors(raw, freeze, fixture))
    return rejected

def main():
    errors = manifest_errors(ROOT, (ROOT / "SHA256SUMS").read_text().splitlines())
    freeze = json.loads((ROOT / "FREEZE.json").read_bytes())
    run = json.loads((ROOT / "RUN.json").read_bytes())
    fixture = json.loads((ROOT / "fixture.json").read_bytes())
    for name, expected in freeze["sha256"].items():
        if sha(ROOT / name) != expected:
            errors.append("frozen_source:" + name)
    data = ROOT / "results/formal01-candidate-data"
    raw_path = data / "candidate_stdout.json"
    raw = json.loads(raw_path.read_bytes())
    binding = {"freeze_sha256": sha(ROOT / "FREEZE.json"), "fixture_sha256": sha(ROOT / "fixture.json"),
               "source_sha256": {name: freeze["sha256"][name] for name in BINDING_SOURCES}}
    rebuilt = inspect(raw_path, data, image_audit=False, expected_fixture=fixture, binding=binding)
    errors.extend("raw_audit:" + err for err in rebuilt["errors"])
    errors.extend(allocation_errors(raw, freeze, fixture))
    retained = json.loads((ROOT / "results/formal01-auditor-launch/stdout.bin").read_bytes())
    errors.extend(run_statistics_errors(run, rebuilt, retained, raw, binding["freeze_sha256"]))
    if retained["status"] != "PASS_AUDIT" or retained["errors"]:
        errors.append("retained_audit_failed")
    for key in ("rows", "exact_save_failures", "baseline_image_integrity_rows"):
        if retained[key] != rebuilt[key]:
            errors.append("audit_reconstruction:" + key)
    for group, values in rebuilt["groups"].items():
        for key in ("n", "exact_save", "first_key_target", "first_visual"):
            if retained["groups"].get(group, {}).get(key) != values[key]:
                errors.append("group_reconstruction:" + group + ":" + key)
    for index, row in enumerate(raw["rows"]):
        errors.extend(f"row_{index}:" + err for err in visual_file_errors(data / f"row-{index:03d}", row))
    expected_binding = {"source_commit": run["source_freeze_commit"], "freeze_sha256": binding["freeze_sha256"],
                        "source_sha256": freeze["sha256"], "allocation": freeze["allocation"]}
    for role in ("candidate", "auditor"):
        directory = ROOT / f"results/formal01-{role}-launch"
        receipt = json.loads((directory / "receipt.json").read_bytes())
        errors.extend(role + ":" + err for err in stream_errors(directory, receipt))
        expected = dict(expected_binding)
        if role == "auditor":
            expected["candidate_raw_sha256"] = sha(raw_path)
        if receipt["binding"] != expected or receipt["argv"] != freeze["commands"][role]:
            errors.append(role + ":frozen_binding_or_argv")
        for run_suffix, receipt_key in (("started_utc", "started_utc"), ("finished_utc", "finished_utc"),
                                        ("wall_seconds", "wall_seconds")):
            if run.get(role + "_" + run_suffix) != receipt[receipt_key]:
                errors.append(role + ":run_clock_binding")
    if (sha(raw_path) != run["candidate_raw_sha256"] or
            sha(ROOT / "results/formal01-auditor-launch/stdout.bin") != run["auditor_raw_sha256"]):
        errors.append("run_raw_binding")
    if (run["disposition"] != "PASS_METHOD_SCOPED" or run["formal_candidate_invocations"] != 1 or
            run["formal_auditor_invocations"] != 1 or run["retries"] != 0 or freeze["budget"]["rows"] != 48):
        errors.append("run_scope")
    # C01 has its own frozen source/fixture/raw; never pooled into formal rows.
    source = ROOT / "results/construction01-source"
    construction_freeze = json.loads((source / "FREEZE.json").read_bytes())
    for name, expected in construction_freeze["sha256"].items():
        if sha(source / name) != expected:
            errors.append("construction_source:" + name)
    cdata = ROOT / "results/construction01-candidate-data"
    cfixture = json.loads((source / "fixture.json").read_bytes())
    cbinding = {"freeze_sha256": sha(source / "FREEZE.json"), "fixture_sha256": sha(source / "fixture.json"),
                "source_sha256": {name: construction_freeze["sha256"][name] for name in BINDING_SOURCES}}
    caudit = inspect(cdata / "candidate_stdout.json", cdata, image_audit=False, expected_fixture=cfixture, binding=cbinding)
    if caudit["errors"] or caudit["rows"] != 1:
        errors.append("construction_reconstruction")
    retained_c = json.loads((ROOT / "results/construction01-auditor-launch/stdout.bin").read_bytes())
    if retained_c["status"] != "PASS_AUDIT" or retained_c["errors"] or any(
            caudit[key] != retained_c[key] for key in ("rows", "exact_save_failures", "baseline_image_integrity_rows")):
        errors.append("construction_retained_audit")
    for role in ("candidate", "auditor"):
        directory = ROOT / f"results/construction01-{role}-launch"
        receipt = json.loads((directory / "receipt.json").read_bytes())
        errors.extend("construction_" + role + ":" + err for err in stream_errors(directory, receipt))
        if receipt["argv"] != construction_freeze["commands"][role]:
            errors.append("construction_" + role + ":argv")
    rejected = corruptions(raw_path, data, freeze, fixture, binding)
    if not all(rejected.values()):
        errors.append("corruption_control")
    result = {"status": "FAIL_RETAINED_PACKET" if errors else "PASS_RETAINED_METHOD_SCOPED",
              "errors": errors, "scientific_disposition": run["disposition"], "rows": rebuilt["rows"],
              "exact_save": rebuilt["rows"]-rebuilt["exact_save_failures"],
              "nonexact_save": rebuilt["exact_save_failures"], "ready_custody_errors": sum("readiness:" in e for e in rebuilt["errors"]),
              "corruptions_rejected": rejected, "formal_commands_executed": 0,
              "scope": "private disposable Tk text/focus receipts; no public-client/default-wait/visual/resource/performance claim"}
    print(json.dumps(result, sort_keys=True))
    return 1 if errors else 0

if __name__ == "__main__":
    raise SystemExit(main())
