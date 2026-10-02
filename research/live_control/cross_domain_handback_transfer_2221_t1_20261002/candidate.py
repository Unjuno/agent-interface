"""Project audited retained DOOM and browser evidence into a typed handback."""
import argparse
import hashlib
import json
from pathlib import Path


def load_pinned(repo_root, relative_path, source_manifest):
    path = repo_root / relative_path
    data = path.read_bytes()
    want = source_manifest["sources"][relative_path]["sha256"]
    got = hashlib.sha256(data).hexdigest()
    if got != want:
        raise ValueError(f"source SHA-256 mismatch: {relative_path}")
    return json.loads(data.decode("utf-8")), got


def source_ref(path, sha256, field):
    return {"artifact": path, "sha256": sha256, "field": field}


def verify_freeze(package, freeze_path):
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    for relative, expected in freeze["sha256"].items():
        observed = hashlib.sha256((package / relative).read_bytes()).hexdigest()
        if observed != expected:
            raise ValueError(f"frozen source changed: {relative}")
    return freeze


def build_transfer(repo_root):
    package = Path(__file__).resolve().parent
    pins = json.loads((package / "SOURCE_HASHES.json").read_text(encoding="utf-8"))
    doom_path = "research/doom/results/map01-v38-v39-control-tempo-posthoc-v1/analysis.json"
    desktop_audit_path = "runtime/results/public-six-task-comparison-04/audit.json"
    task6_path = "runtime/results/public-six-task-comparison-04/task6-visual-audit.json"
    doom, doom_sha = load_pinned(repo_root, doom_path, pins)
    public_audit, public_sha = load_pinned(repo_root, desktop_audit_path, pins)
    task6, task6_sha = load_pinned(repo_root, task6_path, pins)

    doom_runs = {row["run"]: row for row in doom["runs"]}
    v38 = doom_runs["map01-v38-integrated-threat-live-01"]
    v39 = doom_runs["map01-v39-coast-liveness-live-01"]
    direct = task6["task6"]
    if (len(v38["first_exact_plan_feedback"]) != 1
            or len(v39["first_exact_plan_feedback"]) != 3
            or any(x["semantic_task_feedback"] != "unverified"
                   for x in v38["first_exact_plan_feedback"]
                   + v39["first_exact_plan_feedback"])):
        raise ValueError("DOOM first-frame feedback source changed")
    if (v38["totals"]["independent_map_exit"] is not False
            or v39["totals"]["independent_map_exit"] is not False
            or v39["totals"]["independent_kills"] != 1):
        raise ValueError("DOOM independently scored outcome changed")
    if (public_audit["status"] != "PASS_PUBLIC_SIX_TASK_CORRECTNESS_SCOPED"
            or public_audit["raw_files"] != 1051
            or direct["submission"]["exact"] is not True
            or direct["visual_cue_after_fresh_observation"]
               != "UNKNOWN_NOT_OBSERVED"
            or direct["save_release_verified"] is not True):
        raise ValueError("browser task-6 independent evidence changed")
    if sum(len(v["first_exact_plan_feedback"]) for v in (v38, v39)) != 4:
        raise ValueError("unexpected feedback denominator")

    authority = {"input_authority": False, "semantic_authority": False}
    records = [
        {
            "case_id": "doom-v38-first-plan-frame", "domain": "doom-map01",
            "evidence_type": "OBSERVED_CHANGE", "task_effect": "UNRESOLVED",
            "semantic_task_feedback": "unverified", "task_terminal": "NOT_ESTABLISHED",
            "map_exit": False,
            "first_exact_capture_ms": 55.243,
            "lineage": "plan-0-primary-0-0", "clock_join": "NOT_CLAIMED",
            "source": source_ref(doom_path, doom_sha,
                                  "runs[map01-v38-integrated-threat-live-01].first_exact_plan_feedback[0]"),
            **authority,
        },
        {
            "case_id": "doom-v39-first-plan-frames", "domain": "doom-map01",
            "evidence_type": "OBSERVED_CHANGE", "task_effect": "UNRESOLVED",
            "semantic_task_feedback": "unverified", "task_terminal": "NOT_ESTABLISHED",
            "map_exit": False, "independent_kills": 1, "independent_deaths": 0,
            "frame_count": 3,
            "frame_capture_ms": [78.217, 69.492, 51.484],
            "lineage": ["plan-0-primary-0-1", "plan-3-primary-0-1", "plan-4-primary-0-1"],
            "clock_join": "NOT_CLAIMED",
            "source": source_ref(doom_path, doom_sha,
                                  "runs[map01-v39-coast-liveness-live-01].first_exact_plan_feedback"),
            **authority,
        },
        {
            "case_id": "doom-v39-typed-revocation-release", "domain": "doom-map01",
            "evidence_type": "PHYSICAL_RELEASE", "physical_release": "VERIFIED",
            "capture_to_release_ms": 38.844, "typed_emit_to_release_ms": 26.090,
            "release_to_terminal_ms": 52.961, "task_effect": "UNRESOLVED",
            "lineage": "plan-3-primary-0-1", "clock_join": "WITHIN_SOURCE_EVENT_ONLY",
            "source": source_ref(doom_path, doom_sha,
                                  "runs[map01-v39-coast-liveness-live-01].running_release_latency"),
            **authority,
        },
        {
            "case_id": "browser-direct-task6-save", "domain": "browser-desktop",
            "evidence_type": "TASK_EFFECT", "task_effect": "EXACT_ONCE_SUBMISSION",
            "independently_scored": True, "task_id": "task-6",
            "visual_acknowledgement": "UNKNOWN_NOT_OBSERVED",
            "physical_release_verified": True,
            "call_id": direct["call_id"], "submission_count": 1,
            "clock_join": "NOT_CLAIMED",
            "source": source_ref(task6_path, task6_sha, "task6"),
            "crosscheck_source": source_ref(desktop_audit_path, public_sha,
                                            "routes.direct.exact_tasks / acceptance"),
            **authority,
        },
    ]
    return {
        "experiment_id": "CROSS-DOMAIN-HANDBACK-2221-T1-20261002-01",
        "status": "PASS_RETAINED_SOURCE_TRANSFER_CANDIDATE",
        "scope": "read-only retained-evidence projection; no model/GUI/input/live task",
        "records": records,
        "limits": [
            "This does not satisfy #2221 live model-recovery acceptance.",
            "DOOM viewport change is not independently scored as useful task feedback.",
            "A kill is domain progress, not MAP01 exit or task completion.",
            "Browser exact-once server submission does not prove the visual acknowledgement was rendered or seen.",
            "No cross-source latency or shared clock is inferred.",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--freeze", type=Path)
    args = parser.parse_args()
    if args.freeze:
        verify_freeze(Path(__file__).resolve().parent, args.freeze)
    result = build_transfer(args.repo_root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({"status": result["status"], "records": len(result["records"])}))


if __name__ == "__main__":
    main()
