"""Read-only, offline replay audit for an extracted Issue #3483 evidence bundle.

This auditor writes only to stdout. It independently checks every path and
SHA-256 recorded in the frozen audit's raw_manifest, then rechecks request /
reply lineage, verified releases, and saved SVG geometry. Container lifecycle
fields in the frozen audit are explicitly treated as producer attestations;
they cannot be independently re-queried from this portable bundle.
"""
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


BASE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def main():
    base = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else BASE
    frozen = read(base / "audit.json")
    expected = frozen["raw_manifest"]
    mismatches = []
    for relative, digest in expected.items():
        path = base / relative
        if not path.is_file():
            mismatches.append({"path": relative, "error": "missing"})
        elif sha(path) != digest:
            mismatches.append({"path": relative, "error": "sha256_mismatch", "actual": sha(path)})

    root = base / "evidence/session"
    run = root / "allocation/run"
    start = read(root / "start-response.json")
    start_meta = json.loads(start["content"][0]["text"])
    source1 = read(run / "source-1.json")
    initial_linked = (start_meta["image_status"] == "image"
                      and start_meta["image_reference"]["sequence"] == 1
                      and source1["sequence"] == 1
                      and start["content"][1]["sha256"] == sha(root / "start-1.png")
                      == source1["native"]["artifact"]["sha256"])

    stages = []
    for n in (1, 2):
        request_path, reply_path = run / f"request-{n}.json", run / f"reply-{n}.json"
        request_raw = request_path.read_bytes()
        request = json.loads(request_raw)
        reply = read(reply_path)
        source = read(run / f"source-{n}.json")
        request_hash = hashlib.sha256(request_raw).hexdigest()
        stages.append({
            "stage": n,
            "request_sha256": request_hash,
            "reply_sha256": sha(reply_path),
            "source_sequence": source["sequence"],
            "request_sequence": request["source_sequence"],
            "reply_decision_sha256": reply["decision_sha256"],
            "linked": request["source_sequence"] == source["sequence"]
                      and reply["decision_sha256"] == request_hash,
        })

    # Bind the exact inspected click-only PNG to both the response metadata and
    # the stage-one reply / stage-two source that authorized keyboard input.
    click_image = root / "click-only-1.png"
    click_meta = json.loads(read(root / "click-only-response.json")["content"][0]["text"])
    reply1 = read(run / "reply-1.json")
    source2 = read(run / "source-2.json")
    click_hash = sha(click_image)
    selected_artifact_hash = source2["native"]["artifact"]["sha256"]
    selection_frame_linked = (
        click_meta.get("image_status") == "image"
        and click_meta.get("image_reference", {}).get("sequence") == source2.get("sequence")
        and click_meta.get("image_reference", {}).get("sha256") == click_hash
        and reply1.get("observation", {}).get("native", {}).get("artifact", {}).get("sha256")
        == selected_artifact_hash == click_hash
        and frozen.get("selection_review", {}).get("image_sha256") == click_hash
    )

    actions_data = read(run / "actions.json")
    actions = actions_data if isinstance(actions_data, list) else [
        actions_data[k] for k in sorted(actions_data, key=int)]
    action_checks = []
    for row in actions:
        result = row.get("result", {})
        feedback = row.get("feedback", {})
        releases = result.get("execution", {}).get("releases", [])
        action_checks.append({
            "status_completed": result.get("status") == "completed",
            "admission_accepted": result.get("admission") == "accepted",
            "feedback_matched": feedback.get("status") == "matched",
            "verified_empty_releases": bool(releases) and all(
                item.get("verified") is True and item.get("keys_down") == []
                and item.get("buttons_down") == [] for item in releases),
        })
    actions_ok = len(actions) == 2 and all(all(check.values()) for check in action_checks)
    releases_ok = len(action_checks) == 2 and all(
        check["verified_empty_releases"] for check in action_checks)

    svg = run / "shape.svg"
    rects = ET.parse(svg).getroot().findall("{http://www.w3.org/2000/svg}rect")
    attrs = rects[0].attrib if len(rects) == 1 else {}
    try:
        effect = (float(attrs["x"]) > 50.5 and abs(float(attrs["y"]) - 50) < .1
                  and abs(float(attrs["width"]) - 40) < .1
                  and abs(float(attrs["height"]) - 30) < .1
                  and "transform" not in attrs)
    except (KeyError, ValueError):
        effect = False

    lineage_ok = initial_linked and len(stages) == 2 and all(stage["linked"] for stage in stages)
    visual_review_attested = frozen.get("selection_review", {}).get("reviewed_visually") is True
    raw_hashes_ok = not mismatches and len(expected) == 62
    core_ok = (raw_hashes_ok and lineage_ok and selection_frame_linked and actions_ok
               and releases_ok and effect and visual_review_attested)
    lifecycle = {
        "verification_scope": "producer_attestation_only_portable_raw_bundle_has_no_docker_inspect_receipt",
        "owner_exit_zero": frozen.get("owner_exit_zero"),
        "tracked_processes_terminal": frozen.get("tracked_processes_terminal"),
        "private_container_stopped": frozen.get("private_container_stopped"),
        "outer_exit_code": frozen.get("container", {}).get("exit_code"),
        "raw_cleanup_flags_preserved": frozen.get("raw_cleanup", {}),
    }
    result = {
        "schema": "issue-3483-offline-replay-audit-v1",
        "disposition": "PASS_SELECTION_GATED_SAVED_MOVE_SCOPED_RAW_REPLAY"
                      if core_ok else "HOLD_OFFLINE_REPLAY_AUDIT",
        "raw_manifest_entries": len(expected),
        "raw_manifest_hashes_match": raw_hashes_ok,
        "raw_manifest_mismatches": mismatches,
        "initial_source_image_linked": initial_linked,
        "stages": stages,
        "selection_frame_sha256": click_hash,
        "selection_frame_linked_to_reply_and_authorizing_source": selection_frame_linked,
        "action_checks": action_checks,
        "actions_completed_admitted_and_feedback_matched": actions_ok,
        "verified_empty_releases": releases_ok,
        "saved_svg_sha256": sha(svg),
        "saved_svg_geometry": {key: attrs.get(key) for key in
                                ("x", "y", "width", "height", "transform")},
        "saved_svg_effect": effect,
        "selection_visual_review_attested_in_frozen_audit": visual_review_attested,
        "lifecycle": lifecycle,
        "scope": "Offline replay independently checks archived hashes, lineage, releases, and SVG effect. It does not independently verify container lifecycle or perform a new visual inspection.",
    }
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
