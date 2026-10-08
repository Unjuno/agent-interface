"""Raw-only independent audit for the Issue #5260 T1 candidate record."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import subprocess
import sys
from schedule import schedule as expected_schedule


def sha(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(131072), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect(raw_path, out_dir, image_audit=True):
    raw = json.loads(Path(raw_path).read_text(encoding="utf-8"))
    root = Path(out_dir)
    fixture = raw.get("fixture", {})
    schedule = expected_schedule(fixture)
    errors = []
    if raw.get("schema") not in ("issue5260-firstchar-a01-v1", "issue5260-first-character-a01-v1", "issue5260-firstchar-a01-raw-v1"):
        errors.append("schema")
    if raw.get("allocation") != fixture.get("allocation"):
        errors.append("allocation")
    if raw.get("schedule") != schedule:
        errors.append("schedule")
    rows = raw.get("rows", [])
    if len(rows) != len(schedule) or raw.get("row_count") != len(schedule):
        errors.append("row_count")
    if raw.get("rows_completed") != len(schedule):
        errors.append("rows_completed")
    grouped = defaultdict(lambda: {"n": 0, "exact_save": 0, "first_key_target": 0,
                                    "first_visual": 0, "frame_ocr": 0, "delay_ms": []})
    ocr_rows = []
    for index, row in enumerate(rows):
        if index >= len(schedule):
            errors.append(f"row_{index}_extra")
            continue
        plan = schedule[index]
        for key, value in plan.items():
            if row.get(key) != value:
                errors.append(f"row_{index}_plan_{key}")
        group = (row.get("coordinate_method"), row.get("first_key_delay_ms"), row.get("load"))
        stats = grouped[group]
        stats["n"] += 1
        if row.get("app_exit") != 0 or row.get("app_parse_error") is not None or not isinstance(row.get("app"), dict):
            errors.append(f"row_{index}_app_exit_or_parse")
            continue
        app = row["app"]
        ready = row.get("ready", {})
        geom = ready.get("geometry", {})
        events = ready.get("map_configure_events", [])
        names = [event.get("kind") for event in events if isinstance(event, dict)]
        if "Map" not in names or "Configure" not in names:
            errors.append(f"row_{index}_map_configure_missing")
        map_ns = next((event.get("monotonic_ns") for event in events if event.get("kind") == "Map"), None)
        configure_ns = next((event.get("monotonic_ns") for event in events if event.get("kind") == "Configure"), None)
        ready_ns = ready.get("ready_ns")
        click_ns = row.get("injection", {}).get("click_started_ns")
        if not all(type(value) is int for value in (map_ns, configure_ns, ready_ns, click_ns)):
            errors.append(f"row_{index}_map_time_type")
        elif max(map_ns, configure_ns) > ready_ns or ready_ns > click_ns:
            errors.append(f"row_{index}_map_barrier_order")
        expected_address = geom.get("target_id") if row.get("coordinate_method") == "CHILD_ROOT_COORD" else geom.get("root_id")
        if row.get("injection", {}).get("addressed_id") != expected_address:
            errors.append(f"row_{index}_addressed_window")
        if any(type(geom.get(key)) is not int or geom[key] <= 1 for key in
               ("root_width", "root_height", "target_width", "target_height")):
            errors.append(f"row_{index}_geometry_nonpositive")
        if row.get("coordinate_method") == "CHILD_ROOT_COORD":
            want_x = geom.get("target_root_x", 0) + geom.get("target_width", 0) // 2
            want_y = geom.get("target_root_y", 0) + geom.get("target_height", 0) // 2
        else:
            want_x = geom.get("root_x", 0) + geom.get("target_x", 0) + geom.get("target_width", 0) // 2
            want_y = geom.get("root_y", 0) + geom.get("target_y", 0) + geom.get("target_height", 0) // 2
        inj = row.get("injection", {})
        if (inj.get("x"), inj.get("y")) != (want_x, want_y):
            errors.append(f"row_{index}_coordinate_provenance")
        keys = inj.get("key_requests", [])
        if len(keys) != len(fixture.get("payload", "")):
            errors.append(f"row_{index}_dispatch_count")
        if keys:
            first = keys[0]
            click_sync = inj.get("click_sync_returned_ns")
            if type(click_sync) is not int or first.get("request_started_ns", 0) < click_sync:
                errors.append(f"row_{index}_first_dispatch_precedes_click")
            elif (first["request_started_ns"] - click_sync) / 1_000_000 + 2 < row["first_key_delay_ms"]:
                errors.append(f"row_{index}_first_dispatch_delay_short")
        if app.get("saved_text") == fixture.get("payload") and app.get("save_count") == 1:
            stats["exact_save"] += 1
        key_events = [event for event in app.get("events", []) if event.get("kind") == "KeyPress"]
        if key_events and key_events[0].get("widget") == "target" and key_events[0].get("char") == fixture["payload"][0]:
            stats["first_key_target"] += 1
        first_visual = app.get("first_visual")
        if first_visual:
            stats["first_visual"] += 1
            first_key_ns = app.get("first_key_ns")
            visual_ns = first_visual.get("observed_ns")
            if type(first_key_ns) is not int or type(visual_ns) is not int or visual_ns < first_key_ns:
                errors.append(f"row_{index}_visual_time_order")
            if first_visual.get("widget") != (key_events[0].get("widget") if key_events else None):
                errors.append(f"row_{index}_visual_widget_binding")
            frame_info = first_visual.get("frame", {})
            frame_path = root / f"row-{index:03d}" / "first_visual.xwd"
            actual_hash = sha(frame_path) if frame_path.is_file() else None
            if not frame_path.is_file() or frame_info.get("exit") != 0 or actual_hash != frame_info.get("sha256"):
                errors.append(f"row_{index}_first_frame_integrity")
            elif not frame_info.get("bytes", 0):
                errors.append(f"row_{index}_first_frame_empty")
            elif image_audit:
                crop = first_visual.get("entry_crop", {})
                crop_path = root / f"row-{index:03d}" / "first_visual_crop.png"
                convert = subprocess.run(["convert", str(frame_path), "-crop",
                    f"{crop.get('width', 0)}x{crop.get('height', 0)}+{crop.get('x', 0)}+{crop.get('y', 0)}",
                    "+repage", "-resize", "400%", "-colorspace", "Gray", "-contrast-stretch", "0x10%",
                    str(crop_path)], capture_output=True, text=True, timeout=10)
                if convert.returncode != 0:
                    errors.append(f"row_{index}_image_crop_tool")
                    ocr = subprocess.CompletedProcess([], 1, "", convert.stderr)
                else:
                    ocr = subprocess.run(["tesseract", str(crop_path), "stdout", "--psm", "7",
                                          "-c", "tessedit_char_whitelist=hxy"], capture_output=True,
                                         text=True, timeout=10)
                visible_expected = first_visual.get("target_value", "")
                visible_recognized = "".join(ch for ch in ocr.stdout.lower() if ch.isalpha())
                if visible_expected and visible_recognized and visible_recognized == visible_expected:
                    stats["frame_ocr"] += 1
                ocr_rows.append({"index": index, "expected": visible_expected,
                                 "recognized": visible_recognized,
                                 "image_sha256": frame_info.get("sha256"),
                                 "ocr_status": "MATCH" if visible_recognized == visible_expected else "UNRESOLVED_OR_MISMATCH"})
        else:
            errors.append(f"row_{index}_first_visual_missing")
        baseline = ready.get("baseline_frame", {})
        baseline_path = root / f"row-{index:03d}" / "baseline.xwd"
        baseline_hash = sha(baseline_path) if baseline_path.is_file() else None
        baseline_integrity = bool(baseline_path.is_file() and baseline.get("exit") == 0 and
                                  baseline_hash == baseline.get("sha256") and
                                  baseline.get("bytes", 0) == baseline_path.stat().st_size)
        if row.get("load") == "cpu_busy":
            if row.get("worker", {}).get("pid") is None or row.get("worker", {}).get("exit") != 0:
                errors.append(f"row_{index}_worker_exit")
        elif row.get("worker", {}).get("pid") is not None or row.get("worker", {}).get("exit") is not None:
            errors.append(f"row_{index}_unexpected_worker")
        if app.get("save_count") != 1:
            errors.append(f"row_{index}_save_count")

    expected_groups = {(method, delay, load) for method in fixture.get("coordinate_methods", [])
                       for delay in fixture.get("first_key_delay_ms", [])
                       for load in fixture.get("load_conditions", [])}
    if set(grouped) != expected_groups or any(grouped[g]["n"] != fixture.get("replicates_per_cell") for g in expected_groups):
        errors.append("factorial_cell_cardinality")
    for value in grouped.values():
        value["exact_save_rate"] = value["exact_save"] / value["n"] if value["n"] else None
        value["first_key_target_rate"] = value["first_key_target"] / value["n"] if value["n"] else None
        value["frame_ocr_exact_rate"] = value["frame_ocr"] / value["n"] if value["n"] else None
    exact_failures = sum(value["n"] - value["exact_save"] for value in grouped.values())
    audit = {"schema": "issue5260-firstchar-a01-audit-v1", "status": "PASS_AUDIT" if not errors else "FAIL_AUDIT",
             "errors": errors, "rows": len(rows), "groups": {"|".join(map(str, key)): val for key, val in grouped.items()},
            "exact_save_failures": exact_failures, "first_visual_ocr_rows": ocr_rows,
             "baseline_image_integrity_rows": sum(1 for index in range(len(rows)) if
                 (root / f"row-{index:03d}" / "baseline.xwd").is_file() and
                 sha(root / f"row-{index:03d}" / "baseline.xwd") == rows[index].get("ready", {}).get("baseline_frame", {}).get("sha256")),
             "scope": "one disposable Tk/Xvfb application; no live user task, external effect, model, or product claim"}
    return audit


if __name__ == "__main__":
    result = inspect(sys.argv[1], sys.argv[2])
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    raise SystemExit(0 if result["status"] == "PASS_AUDIT" else 2)
