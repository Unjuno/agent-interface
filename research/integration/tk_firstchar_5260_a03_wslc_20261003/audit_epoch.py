"""Read-only independent reconstruction; never starts GUI or containers."""
import hashlib
import json
from datetime import datetime
from pathlib import Path
import sys


SCHEDULE = [("LEGACY", 0), ("FIXED", 0), ("FIXED", 1), ("LEGACY", 1),
            ("LEGACY", 2), ("FIXED", 2), ("FIXED", 3), ("LEGACY", 3)]
SOURCES = ("readiness_once.py", "probe_app.py", "probe_epoch.py")


def validate(raw, freeze):
    errors = []

    def require(ok, label):
        if not ok:
            errors.append(label)

    try:
        require(raw["schema"] == "5260-a03-epoch-construction01-v1", "schema")
        require(raw["allocation"] == "5260-a03-wslc-no-input-construction01-20261003", "allocation")
        require(raw["status"] == "CONSTRUCTION_ONLY_NO_INPUT", "scope")
        require(raw["image_id"] == freeze["image_id"], "image")
        require(raw["source_sha256"] == {n: freeze["source_sha256"][n] for n in SOURCES}, "sources")
        require(raw["xvfb_exit"] == raw["openbox_exit"] == 0, "display_exits")
        require(len(raw["rows"]) == 8, "coverage")
        pids = []
        for index, row in enumerate(raw["rows"]):
            prefix = f"row{index}:"
            app = row["app"]
            require(row["index"] == index and (row["mode"], row["replicate"]) == SCHEDULE[index], prefix + "schedule")
            require(row["exit"] == 0, prefix + "exit")
            require(app["schema"] == "5260-a03-no-input-app-v1", prefix + "app_schema")
            require(app["mode"] == row["mode"] and app["pid"] == row["pid"] > 0, prefix + "identity")
            pids.append(row["pid"])
            require(json.loads(row["stdout"]) == app, prefix + "stdout")
            require(app["input_events"] == 0 and app["target_text"] == app["decoy_text"] == "", prefix + "no_input")
            events = app["events"]
            kinds = [event["kind"] for event in events]
            times = [event["ns"] for event in events]
            require(times == sorted(times) and all(0 < t <= app["ended_ns"] for t in times), prefix + "event_clocks")
            require("Map" in kinds and "Configure" in kinds and "UNEXPECTED_INPUT" not in kinds, prefix + "mapped_events")
            count = app["finalizations"]
            require(isinstance(count, int) and count >= 1 and
                    count == app["scheduled"] == app["focus_callbacks"] and
                    kinds.count("schedule") == count and kinds.count("decoy_focus_callback") == count,
                    prefix + "callback_counts")
            first, last, observed = app["first_ready"], app["last_ready"], row["first_observer_read"]
            require(row["final_ready_file"] == last, prefix + "final_file")
            require(first["epoch"] == 1 and last["epoch"] == count and
                    1 <= observed["epoch"] <= count, prefix + "epoch_counts")
            require(0 < first["ready_ns"] <= observed["ready_ns"] <= last["ready_ns"] <= app["ended_ns"], prefix + "ready_clocks")
            identities = [{k: v for k, v in ready.items() if k not in ("epoch", "ready_ns")}
                          for ready in (first, last, observed)]
            require(identities[0] == identities[1] == identities[2], prefix + "ready_geometry_identity")
            for ready in (first, last, observed):
                require(ready["mapped"] is True and ready["root_id"] > 0 and
                        ready["target_id"] > 0 and ready["target_id"] != ready["root_id"] and
                        ready["root_width"] == 520 and ready["root_height"] == 250 and
                        min(ready["target_width"], ready["target_height"]) > 1, prefix + "geometry")
            require(max(e["ns"] for e in events if e["kind"] == "schedule") < first["ready_ns"], prefix + "ready_after_schedule")
            if row["mode"] == "FIXED":
                require(count == 1 and first == last == observed, prefix + "fixed_single_epoch")
        require(len(set(pids)) == len(pids), "fresh_processes")
    except (KeyError, TypeError, ValueError, IndexError):
        errors.append("malformed_or_incomplete")
    return errors


def verify_files(raw, data):
    errors = []
    for row in raw["rows"]:
        prefix = f"row{row['index']}:"
        directory = Path(data) / f"row-{row['index']:02d}"
        try:
            for name in ("stdout", "stderr"):
                if (directory / (name + ".bin")).read_bytes() != row[name].encode("utf-8"):
                    errors.append(prefix + name + "_bytes")
            for name, key in (("ready.json", "final_ready_file"), ("app_result.json", "app")):
                if json.loads((directory / name).read_bytes()) != row[key]:
                    errors.append(prefix + name + "_binding")
        except (OSError, ValueError):
            errors.append(prefix + "missing_or_invalid_file")
    return errors


def validate_launch(attempt, receipt, freeze, blobs):
    errors = []
    try:
        if attempt["argv"] != freeze["command"] or receipt["argv"] != freeze["command"]:
            errors.append("launch_argv")
        if receipt["started_utc"] != attempt["started_utc"]:
            errors.append("launch_start")
        start = datetime.fromisoformat(receipt["started_utc"])
        finish = datetime.fromisoformat(receipt["finished_utc"])
        if start.tzinfo is None or finish.tzinfo is None or finish < start or receipt["wall_seconds"] <= 0:
            errors.append("launch_clocks")
        if receipt["exit_code"] != 0 or receipt["launch_error"] is not None:
            errors.append("launch_exit")
        expected = {n: hashlib.sha256(b).hexdigest() for n, b in blobs.items()}
        if receipt["output_sha256"] != expected or json.loads(blobs["attempt.json"]) != attempt:
            errors.append("launch_stream_bytes")
        if json.loads(blobs["stdout.bin"]) != {"rows": 8, "input_events": 0}:
            errors.append("launch_summary")
    except (KeyError, TypeError, ValueError):
        errors.append("launch_malformed")
    return errors


def main(data, freeze_path, launch):
    data, freeze_path = Path(data), Path(freeze_path)
    raw = json.loads((data / "raw.json").read_bytes())
    freeze = json.loads(freeze_path.read_bytes())
    errors = validate(raw, freeze) + verify_files(raw, data)
    launch = Path(launch)
    blobs = {n: (launch / n).read_bytes() for n in ("attempt.json", "stdout.bin", "stderr.bin")}
    errors += validate_launch(json.loads(blobs["attempt.json"]),
        json.loads((launch / "receipt.json").read_bytes()), freeze, blobs)
    for name, expected in freeze["source_sha256"].items():
        if hashlib.sha256((freeze_path.parent / name).read_bytes()).hexdigest() != expected:
            errors.append("source_disk:" + name)
    result = {"status": "STOP_CONSTRUCTION_CUSTODY" if errors else "PASS_CONSTRUCTION_CUSTODY",
        "errors": errors, "scope": "no-input disposable Tk readiness only",
        "rows": len(raw["rows"]), "raw_sha256": hashlib.sha256((data / "raw.json").read_bytes()).hexdigest(),
        "legacy_duplicate_rows": sum(r["app"]["finalizations"] > 1 for r in raw["rows"] if r["mode"] == "LEGACY"),
        "fixed_single_epoch_rows": sum(r["app"]["finalizations"] == 1 for r in raw["rows"] if r["mode"] == "FIXED"),
        "formal_commands_executed": 0}
    print(json.dumps(result, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(*sys.argv[1:]))
