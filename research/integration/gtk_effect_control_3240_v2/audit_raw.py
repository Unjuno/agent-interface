"""Independent raw-byte audit for the additive #3240 arm64 diagnostic."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pid(identity):
    match = re.search(r"_NET_WM_PID\(CARDINAL\) = (\d+)", identity["xprop"])
    return int(match.group(1)) if match else None


def image_geometry(identity):
    names = ("Width", "Height", "Absolute upper-left X", "Absolute upper-left Y")
    result = {}
    for name in names:
        match = re.search(r"^\s*" + re.escape(name) + r":\s*(-?\d+)",
                          identity["xwininfo"], re.MULTILINE)
        result[name] = int(match.group(1)) if match else None
    return result


def audit(root):
    errors = []
    rows = []
    positive = root / "01_application_save"
    decoy = root / "02_render_only_decoy"
    ppre = read_json(positive / "target_identity_pre.json")
    ppost = read_json(positive / "target_identity_post.json")
    dpre = read_json(decoy / "target_identity_pre.json")
    dpost = read_json(decoy / "target_identity_post.json")
    prow = read_json(positive / "row.json")
    drow = read_json(decoy / "row.json")
    if ppre != ppost or dpre != dpost:
        errors.append("target_identity_changed")
    for case, identity in ((positive, ppre), (decoy, dpre)):
        if identity["xid"] <= 0 or pid(identity) is None:
            errors.append("target_identity_invalid:" + case.name)
    effect = read_json(positive / "effect.json")
    if effect != {"saved": True, "text": "gtk3240"}:
        errors.append("application_effect_mismatch")
    events = [json.loads(line) for line in
              (positive / "app-events.jsonl").read_text().splitlines() if line]
    if not any(event.get("type") == "save" for event in events):
        errors.append("application_save_event_missing")
    action = read_json(positive / "adapter-action.json")
    raw = action.get("raw_dispatch", {})
    native = raw.get("result", {})
    execution = native.get("execution", {})
    if raw.get("status") != "returned" or native.get("status") != "completed":
        errors.append("adapter_native_execution_incomplete")
    if action.get("status") != "partial" or action.get("task_success") is not None:
        errors.append("adapter_boundary_changed_or_claimed_unscored_success")
    releases = execution.get("releases", [])
    if not releases or any(r.get("verified") is not True or r.get("keys_down") or
                           r.get("buttons_down") for r in releases):
        errors.append("release_not_verified_empty")
    devents = (decoy / "app-events.jsonl")
    if devents.exists() and devents.read_text().strip():
        errors.append("decoy_target_received_event")
    if (decoy / "effect.json").exists():
        errors.append("decoy_target_effect_exists")
    didentity = read_json(decoy / "decoy_identity.json")
    if didentity["xid"] == dpre["xid"] or pid(didentity) == pid(dpre):
        errors.append("decoy_identity_not_distinct")
    if image_geometry(didentity) != image_geometry(dpre):
        errors.append("decoy_geometry_mismatch")
    if prow.get("target_pre_sha256") == prow.get("target_post_sha256"):
        errors.append("positive_target_pixels_unchanged")
    if drow.get("target_pre_sha256") != drow.get("target_post_sha256"):
        errors.append("untouched_target_pixels_changed")
    if drow.get("visual_only_would_accept") is not True:
        errors.append("visual_decoy_not_effective")
    for folder, row in ((positive, prow), (decoy, drow)):
        for key, file in (("target_initial_sha256", "target_pre.xwd"),
                          ("target_post_sha256", "target_post.xwd")):
            if row.get(key) != sha(folder / file):
                errors.append("raw_image_hash_mismatch:" + folder.name + ":" + key)
    for process_file in (positive / "processes.json", decoy / "processes.json"):
        if any(p.get("returncode") is None for p in read_json(process_file)):
            errors.append("process_not_reaped:" + process_file.parent.name)
    rows.extend([
        {"case": "APPLICATION_SAVE", "adapter_status": action.get("status"),
         "native_status": native.get("status"), "target_xid": ppre["xid"],
         "target_pid": pid(ppre), "effect": effect},
        {"case": "RENDER_ONLY_DECOY", "target_xid": dpre["xid"],
         "decoy_xid": didentity["xid"], "visual_only_would_accept": drow.get("visual_only_would_accept"),
         "target_pre_sha256": drow.get("target_pre_sha256"),
         "target_post_sha256": drow.get("target_post_sha256")},
    ])
    return {"decision": "PASS_APP_EFFECT_DISCRIMINATED" if not errors else
            "HOLD_EVIDENCE_OR_EFFECT_BOUNDARY", "errors": errors, "rows": rows,
            "model_calls": 0, "provider_calls": 0,
            "scope": "two-row GTK/X11 diagnostic only; not full #2606 acceptance"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.evidence.resolve())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["errors"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
