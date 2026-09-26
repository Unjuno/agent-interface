"""Independent X11/process/frame oracle; imports no candidate transport/gate."""
import hashlib
import json
import os
from pathlib import Path
import sys

from Xlib import X, display


def sha(data):
    return hashlib.sha256(data).hexdigest()


def frame_path(root, value):
    path = Path(value)
    if path.is_absolute():
        raise ValueError("artifact paths must be relative")
    resolved = (root / path).resolve()
    if root.resolve() not in resolved.parents:
        raise ValueError("artifact path escapes evidence root")
    return resolved


def pid_start(pid):
    value = Path(f"/proc/{pid}/stat").read_text(encoding="ascii")
    return value[value.rfind(")") + 2:].split()[19]


def generation(display_name, xid, pid, start):
    return sha(f"{display_name}\0{xid}\0{pid}\0{start}".encode())


def effect_ref(obs, epoch, region, region_sha):
    return sha(f"{obs}\0{epoch}\0{region}\0{region_sha}".encode())


def title_of(window):
    v = window.get_wm_name()
    return v.decode("utf-8", "replace") if isinstance(v, bytes) else str(v or "")


def get_pid(dpy, window):
    atom = dpy.intern_atom("_NET_WM_PID")
    prop = window.get_full_property(atom, X.AnyPropertyType)
    return int(prop.value[0]) if prop is not None and len(prop.value) else None


def verify_x11(display_name, xid, expected_pid, expected_title, event, root):
    dpy = display.Display(display_name)
    try:
        root_window = dpy.screen().root
        children = [int(w.id) for w in root_window.query_tree().children]
        assert int(xid) in children, "source XID not a root child"
        win = dpy.create_resource_object("window", int(xid))
        attrs = win.get_attributes()
        geo = win.get_geometry()
        pid = get_pid(dpy, win)
        title = title_of(win)
        assert int(attrs.map_state) == X.IsViewable
        assert pid == expected_pid and pid == event["receipt"]["source_pid"]
        assert title == expected_title == event["receipt"]["source_title"]
        assert event["receipt"]["observation_id"] == event["request"]["observation_id"]
        assert event["receipt"]["intent_epoch"] == event["request"]["intent_epoch"]
        assert event["receipt"]["region_id"] == event["request"]["region_id"]
        assert event["receipt"]["region_rect"] == event["request"]["region_rect"]
        assert event["receipt"]["focus_stable"] is True
        focus = dpy.get_input_focus().focus
        focus_xid = int(focus.id) if hasattr(focus, "id") else int(focus)
        assert focus_xid == event["source_window_snapshot"]["focus_xid"]
        assert focus_xid == event["receipt"]["focus_xid"]
        actual_geo = [int(geo.x), int(geo.y), int(geo.width), int(geo.height)]
        assert actual_geo == event["receipt"]["geometry"]
        start = pid_start(pid)
        expected_generation = generation(display_name, xid, pid, start)
        assert expected_generation == event["source_generation"] == event["receipt"]["source_generation"]
        full = bytes(win.get_image(0, 0, int(geo.width), int(geo.height), X.ZPixmap, 0xffffffff).data)
        rect = event["request"]["region_rect"]
        region = bytes(win.get_image(rect[0], rect[1], rect[2], rect[3], X.ZPixmap, 0xffffffff).data)
        full_path = frame_path(root, event["receipt"]["full_frame_path"])
        region_path = frame_path(root, event["receipt"]["region_frame_path"])
        assert sha(full) == event["receipt"]["full_frame_sha256"] == sha(full_path.read_bytes())
        assert sha(region) == event["receipt"]["region_frame_sha256"] == sha(region_path.read_bytes())
        assert len(full) == event["receipt"]["full_frame_bytes"]
        assert len(region) == event["receipt"]["region_frame_bytes"] > 0
        return {"xid": xid, "pid": pid, "title": title, "generation": expected_generation,
                "frame_sha256": sha(full), "region_sha256": sha(region)}
    finally:
        dpy.close()


def independently_admitted(request, receipt, source_event, pid, title, generation_token,
                            full_data, region_data, arrival_ns):
    if not isinstance(receipt, dict):
        return False
    if receipt.get("observation_id") != request.get("observation_id"):
        return False
    if receipt.get("intent_epoch") != request.get("intent_epoch"):
        return False
    if receipt.get("region_id") != request.get("region_id"):
        return False
    if receipt.get("source_window") != source_event["receipt"].get("source_window"):
        return False
    if receipt.get("source_window") != request.get("trusted_xid"):
        return False
    if receipt.get("focus_xid") != source_event.get("source_window_snapshot", {}).get("focus_xid"):
        return False
    if receipt.get("focus_stable") is not True:
        return False
    if receipt.get("source_pid") != pid or receipt.get("source_title") != title:
        return False
    if receipt.get("source_generation") != generation_token:
        return False
    if receipt.get("coverage") != "COMPLETE" or receipt.get("freshness") != "CURRENT":
        return False
    if receipt.get("effect_binding") != "BOUND":
        return False
    if receipt.get("authority_grants") != 0 or receipt.get("ambiguous") is not False:
        return False
    if not isinstance(receipt.get("capture_start_ns"), int) or not isinstance(receipt.get("capture_end_ns"), int):
        return False
    if receipt["capture_end_ns"] < receipt["capture_start_ns"]:
        return False
    if type(arrival_ns) is not int or arrival_ns < receipt["capture_end_ns"]:
        return False
    max_age_ns = request.get("max_receipt_age_ns")
    if type(max_age_ns) is not int or arrival_ns - receipt["capture_end_ns"] > max_age_ns:
        return False
    if sha(full_data) != receipt.get("full_frame_sha256") or sha(region_data) != receipt.get("region_frame_sha256"):
        return False
    if receipt.get("effect_binding_ref") != effect_ref(request["observation_id"], request["intent_epoch"],
                                                       request["region_id"], receipt["region_frame_sha256"]):
        return False
    return True


def main(root_arg):
    root = Path(root_arg)
    manifest = json.loads((root / "manifest.json").read_text())
    raw_rows = [json.loads(x) for x in (root / "raw_events.jsonl").read_text().splitlines()]
    deliveries = [json.loads(x) for x in (root / "deliveries.jsonl").read_text().splitlines()]
    decisions = [json.loads(x) for x in (root / "decisions.jsonl").read_text().splitlines()]
    schedule = json.loads(Path("/src/research/observation_gating/o3_live_receipt_transport_2692_v1/case_schedule.json").read_text())
    raw_by_id = {row["capture_id"]: row for row in raw_rows}
    assert len(raw_rows) == len(deliveries) == len(decisions) == schedule["expected_rows"]
    assert len(raw_by_id) == len(raw_rows)
    assert len({(row["surface"], row["request"]["region_id"], row["case"]) for row in deliveries}) == 36

    actual_windows = {}
    for surface, info in manifest["surfaces"].items():
        actual_windows[surface] = {"xid": info["xid"], "pid": info["pid"], "title": info["title"]}
    x11_checks = []
    for event in raw_rows:
        surface = event["surface"]
        identity = actual_windows[surface]
        assert event["receipt"]["source_window"] == identity["xid"]
        assert event["receipt"]["source_pid"] == identity["pid"]
        assert event["receipt"]["source_title"] == identity["title"]
        x11_checks.append(verify_x11(manifest["display"], identity["xid"], identity["pid"],
                                     identity["title"], event, root))

    errors = []
    case_counts = {}
    for delivery, decision in zip(deliveries, decisions):
        case = delivery["case"]
        key = (delivery["surface"], delivery["request"]["region_id"], case)
        case_counts[case] = case_counts.get(case, 0) + 1
        request = delivery["request"]
        target = actual_windows[delivery["surface"]]
        request["trusted_xid"] = target["xid"]
        source = raw_by_id[delivery["source_capture_id"]]
        receipt = delivery.get("receipt")
        arrival_ns = delivery.get("arrival_ns")
        full = frame_path(root, source["receipt"]["full_frame_path"]).read_bytes()
        region = frame_path(root, source["receipt"]["region_frame_path"]).read_bytes()
        token = source["source_generation"]
        want = case == "complete_current" and source["capture_id"] == delivery["request_capture_id"]
        oracle_accept = independently_admitted(request, receipt, source, target["pid"], target["title"],
                                               token, full, region, arrival_ns)
        if oracle_accept is not want:
            errors.append(f"{key}: oracle expected {want}, got {oracle_accept}")
        if decision["admitted"] is not oracle_accept:
            errors.append(f"{key}: candidate/oracle disagreement")
        if decision["model_escalation_eligible"] is oracle_accept:
            errors.append(f"{key}: model escalation should be inverse of local admission")
        if decision["action_emissions"] != 0:
            errors.append(f"{key}: action emitted")

    expected_counts = {case: 4 for case in schedule["cases"]}
    if case_counts != expected_counts:
        errors.append(f"case denominator mismatch: {case_counts}")
    admitted = sum(bool(x["admitted"]) for x in decisions)
    positives = sum(d["case"] == "complete_current" and bool(x["admitted"])
                    for d, x in zip(deliveries, decisions))
    negatives_admitted = sum(d["case"] != "complete_current" and bool(x["admitted"])
                             for d, x in zip(deliveries, decisions))
    if positives != 4 or negatives_admitted != 0 or admitted != 4:
        errors.append("positive/negative admission counts mismatch")
    if manifest["model_calls"] != 0 or manifest["action_emissions"] != 0:
        errors.append("allocation crossed read-only boundary")
    result = {
        "decision": "PASS_LIVE_RELEVANT_REGION_FAIL_OPEN_SCOPED" if not errors else "FAIL_INDEPENDENT_ORACLE",
        "raw_capture_rows": len(raw_rows), "delivered_rows": len(deliveries),
        "x11_independent_checks": len(x11_checks), "case_counts": case_counts,
        "admitted": admitted, "positive_admitted": positives,
        "negative_admitted": negatives_admitted,
        "model_calls": manifest["model_calls"], "action_emissions": manifest["action_emissions"],
        "oracle_errors": errors,
    }
    (root / "AUDIT_RESULT.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main(sys.argv[1])
