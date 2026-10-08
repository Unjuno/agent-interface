"""Read-only integrity and session-eligibility auditor for Issue #5962 T1."""
from __future__ import annotations

import hashlib
import json
import sys
import tarfile
from pathlib import PurePosixPath

MANIFEST_BLOB_SHA1 = "68d328b9a9d99a6b19c84aa7ac9f8a152d810a5b"
ARCHIVE_SHA256 = "811e63849956658bdbb0fecc1a7237308dd93c71d96644050b1581bc243c4dd2"
MAIN_SNAPSHOT = "ad123c3875d81ebdc8bdfbdb59340005d705a60d"
CAMPAIGNS = ("current", "interrupted02", "caller-stop03")
ROUTES = ("direct", "guarded")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha1(data: bytes) -> str:
    header = b"blob " + str(len(data)).encode("ascii") + b"\0"
    return hashlib.sha1(header + data).hexdigest()


def read_member(archive: tarfile.TarFile, name: str):
    member = archive.getmember(name)
    stream = archive.extractfile(member)
    if stream is None:
        raise ValueError(f"not a regular readable member: {name}")
    return stream.read()


def verify_archive(manifest_bytes: bytes, archive_path: str):
    if git_blob_sha1(manifest_bytes) != MANIFEST_BLOB_SHA1:
        raise ValueError("manifest Git blob identity mismatch")
    manifest = json.loads(manifest_bytes)
    if manifest.get("archive_sha256") != ARCHIVE_SHA256:
        raise ValueError("manifest archive digest mismatch")
    with open(archive_path, "rb") as raw:
        actual_archive_sha = sha256(raw.read())
    if actual_archive_sha != ARCHIVE_SHA256:
        raise ValueError("raw archive SHA-256 mismatch")

    expected = {row["path"]: row for row in manifest["files"]}
    if len(expected) != len(manifest["files"]):
        raise ValueError("duplicate paths in manifest")
    with tarfile.open(archive_path, "r:gz") as archive:
        members = archive.getmembers()
        actual = {}
        for member in members:
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or not member.isfile():
                raise ValueError(f"unsafe/non-file tar member: {member.name}")
            if member.name in actual:
                raise ValueError(f"duplicate archive path: {member.name}")
            payload = read_member(archive, member.name)
            actual[member.name] = {"bytes": len(payload), "sha256": sha256(payload)}
    if set(actual) != set(expected):
        raise ValueError("archive/manifest member set mismatch")
    for path, row in expected.items():
        if actual[path]["bytes"] != row["bytes"] or actual[path]["sha256"] != row["sha256"]:
            raise ValueError(f"member integrity mismatch: {path}")
    return {"archive_sha256": actual_archive_sha, "manifest_git_blob_sha1": git_blob_sha1(manifest_bytes),
            "members_verified": len(actual), "member_errors": 0}


def json_member(archive: tarfile.TarFile, name: str):
    try:
        return json.loads(read_member(archive, name))
    except KeyError:
        return None


def campaign_report(archive: tarfile.TarFile, campaign: str):
    prefix = campaign + "/"
    plan = json_member(archive, prefix + "PLAN.json")
    routes = {}
    for route in ROUTES:
        base = prefix + route + "/"
        allocation = json_member(archive, base + "allocation.json")
        goal = json_member(archive, base + "goal.json")
        evaluation = json_member(archive, base + "evaluation-current.json")
        finish = json_member(archive, base + "finish.json")
        try:
            event_bytes = read_member(archive, base + "host/host-events.jsonl")
            events = [json.loads(line) for line in event_bytes.splitlines() if line.strip()]
        except KeyError:
            events = []
        order = [task.get("task_id") for task in (goal or {}).get("tasks", [])]
        expected = [f"task-{i}" for i in range(1, 7)]
        explicit_session_keys = sorted({
            key for row in events for key in row
            if key.lower() in {"session_id", "session_uuid", "conversation_id", "thread_id"}
        })
        contiguous_event_sequence = (
            [row.get("sequence") for row in events] == list(range(1, len(events) + 1))
        ) if events else False
        complete_effect_ledger = bool(
            evaluation and evaluation.get("success") is True
            and evaluation.get("record_count") == 6
            and evaluation.get("exact_counts") == {task: 1 for task in expected}
            and not evaluation.get("unexpected") and not evaluation.get("duplicates")
            and not evaluation.get("missing")
        )
        phases = [task.get("phase") for task in (goal or {}).get("tasks", [])]
        routes[route] = {
            "allocation_present": allocation is not None,
            "route_history_identity": ({"display": allocation.get("display"), "window": allocation.get("window"),
                                         "history_path": allocation.get("history")} if allocation else None),
            "explicit_session_identity_keys": explicit_session_keys,
            "session_identity_grade": "explicit" if explicit_session_keys else ("route-local composite only" if allocation else "absent"),
            "task_order": order,
            "six_task_order_complete": order == expected,
            "effect_oracle_complete_exact_once": complete_effect_ledger,
            "effect_oracle_record_count": evaluation.get("record_count") if evaluation else None,
            "effect_oracle_missing": evaluation.get("missing") if evaluation else expected,
            "task_phases_show_carryover": bool(phases and any(x in {"warm", "invalidation_repair", "post_repair_warm"} for x in phases)),
            "task_phases": phases,
            "host_event_count": len(events),
            "host_event_sequence_contiguous": contiguous_event_sequence,
            "finish_record": finish,
            "allocation_reset_boundary_explicit": False,
        }
    return {
        "campaign": campaign,
        "source_revision": (plan or {}).get("source_revision"),
        "seed": (plan or {}).get("seed"),
        "route_order": (plan or {}).get("routes", []),
        "campaign_kind": (plan or {}).get("kind"),
        "plan_exposure_limitations": (plan or {}).get("limitations"),
        "pair_has_explicit_reset_boundary": False,
        "model_context_order_known_but_counterbalanced": False,
        "routes": routes,
    }


def audit(manifest_path: str, archive_path: str):
    with open(manifest_path, "rb") as stream:
        manifest_bytes = stream.read()
    integrity = verify_archive(manifest_bytes, archive_path)
    result = {"schema": "issue5962-session-eligibility-t1-v1", "main_snapshot": MAIN_SNAPSHOT,
              "integrity": integrity, "campaigns": []}
    with tarfile.open(archive_path, "r:gz") as archive:
        result["campaigns"] = [campaign_report(archive, c) for c in CAMPAIGNS]
    current = result["campaigns"][0]
    complete_pair = all(x["six_task_order_complete"] and x["effect_oracle_complete_exact_once"]
                        for x in current["routes"].values())
    result["classification"] = {
        "current_pair_has_complete_descriptive_six_task_outcomes": complete_pair,
        "current_pair_has_explicit_stable_session_ids": all(
            x["session_identity_grade"] == "explicit" for x in current["routes"].values()),
        "current_pair_has_explicit_reset_boundary": current["pair_has_explicit_reset_boundary"],
        "current_pair_exposure_or_order_confounded": not current["model_context_order_known_but_counterbalanced"],
        "independent_comparable_pairs": 0 if not complete_pair else 1,
        "t2_route_ranking_eligible": False,
        "disposition": "HOLD_T2_NO_COMPARABLE_SESSION_COHORT",
        "reasons": [
            "Only one complete six-task direct/guarded pair is retained for the current seed/source.",
            "The route pair is serial with growing conversation context; route order is not counterbalanced.",
            "Route trace identity is a display/window/history composite, not an explicit session/conversation ID.",
            "No explicit reset/clean-boundary receipt joins the pair to a stable session identifier."
        ]
    }
    return result


if __name__ == "__main__":
    report = audit(sys.argv[1], sys.argv[2])
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
