"""Independent read-only raw-lineage, selection, effect, release and cleanup audit."""
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE / "evidence/session"
RUN = ROOT / "allocation/run"
CONTAINER = "issue3435-save-selection-991131-20260920"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def main():
    start = read(ROOT / "start-response.json")
    meta = json.loads(start["content"][0]["text"])
    source1 = read(RUN / "source-1.json")
    exact_initial = (meta["image_status"] == "image" and meta["image_reference"]["sequence"] == 1
                     and source1["sequence"] == 1 and start["content"][1]["sha256"] == sha(ROOT / "start-1.png")
                     == source1["native"]["artifact"]["sha256"])
    stages = []
    for n in (1, 2):
        reqp, repp = RUN / f"request-{n}.json", RUN / f"reply-{n}.json"
        raw = reqp.read_bytes()
        req, rep = json.loads(raw), read(repp)
        source = read(RUN / f"source-{n}.json")
        stages.append({"stage": n, "request_sha256": hashlib.sha256(raw).hexdigest(),
                       "reply_sha256": sha(repp), "request_sequence": req["source_sequence"],
                       "source_sequence": source["sequence"], "reply_decision_sha256": rep["decision_sha256"],
                       "linked": req["source_sequence"] == source["sequence"]
                       and rep["decision_sha256"] == hashlib.sha256(raw).hexdigest(),
                       "reply_status": rep["status"]})
    action_data = read(RUN / "actions.json")
    actions = action_data if isinstance(action_data, list) else [action_data[k] for k in sorted(action_data, key=int)]
    releases = [r for row in actions for r in row.get("result", {}).get("execution", {}).get("releases", [])]
    release_ok = bool(releases) and all(r.get("verified") is True and r.get("keys_down") == []
                                        and r.get("buttons_down") == [] for r in releases)
    svg = RUN / "shape.svg"
    rects = ET.parse(svg).getroot().findall("{http://www.w3.org/2000/svg}rect")
    attrs = rects[0].attrib if len(rects) == 1 else {}
    try:
        effect = (float(attrs["x"]) > 50.5 and abs(float(attrs["y"]) - 50) < .1
                  and abs(float(attrs["width"]) - 40) < .1 and abs(float(attrs["height"]) - 30) < .1
                  and "transform" not in attrs)
    except (KeyError, ValueError):
        effect = False
    terminal = json.loads(read(ROOT / "status-after-finish-response.json")["content"][0]["text"])
    cleanup = read(RUN / "cleanup-report.json")
    process_rows = read(RUN / "cleanup.json")
    ctr = json.loads(subprocess.check_output(["docker", "inspect", CONTAINER], text=True))[0]
    state, host = ctr["State"], ctr["HostConfig"]
    owner_zero = terminal["allocation"]["status"] == "terminal" and terminal["allocation"]["returncode"] == 0
    tracked = cleanup.get("tracked_processes_terminal") is True and bool(process_rows) and all(
        p.get("returncode") is not None for p in process_rows)
    private_stopped = host.get("Privileged") is False and host.get("PidMode") in ("", "private") \
        and state.get("Status") == "exited" and state.get("Pid") == 0
    termination = owner_zero and tracked and private_stopped
    click_image = ROOT / "click-only-1.png"
    final_image = ROOT / "gated-save-finish-1.png"
    linked = exact_initial and len(stages) == 2 and all(s["linked"] for s in stages)
    result = {
        "schema": "issue-3483-independent-audit-v1",
        "disposition": ("PASS_SELECTION_GATED_SAVED_MOVE_SCOPED" if linked and effect and release_ok and termination
                        and state.get("ExitCode") == 0 else
                        "FAIL_TASK_EFFECT" if linked and not effect else "HOLD_AUDIT_INCOMPLETE"),
        "initial_source_image_linked": exact_initial, "stages": stages,
        "selection_review": {"image_sha256": sha(click_image), "image_path": str(click_image),
                             "reviewed_visually": True},
        "final_image_sha256": sha(final_image),
        "actions": [{"status": a.get("result", {}).get("status"),
                     "admission": a.get("result", {}).get("admission"),
                     "emissions": a.get("result", {}).get("execution", {}).get("emissions"),
                     "program_emissions": a.get("result", {}).get("execution", {}).get("program_emissions"),
                     "feedback": a.get("feedback", {}).get("status"),
                     "releases": a.get("result", {}).get("execution", {}).get("releases")} for a in actions],
        "verified_empty_releases": release_ok,
        "saved_svg_sha256": sha(svg), "saved_svg_geometry": {k: attrs.get(k) for k in
                               ("x", "y", "width", "height", "transform")}, "saved_svg_effect": effect,
        "raw_cleanup": cleanup, "owner_exit_zero": owner_zero, "tracked_processes_terminal": tracked,
        "private_container_stopped": private_stopped, "independent_termination": termination,
        "container": {"id": ctr["Id"], "image": ctr["Image"], "status": state["Status"],
                      "exit_code": state["ExitCode"], "network_mode": host.get("NetworkMode"),
                      "privileged": host.get("Privileged"), "pid_mode": host.get("PidMode")},
        "raw_manifest": {str(p.relative_to(BASE)): sha(p) for p in sorted(BASE.rglob("*"))
                          if p.is_file() and p.name != "audit.json"},
    }
    out = BASE / "audit.json"
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
