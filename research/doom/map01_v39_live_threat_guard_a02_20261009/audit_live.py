"""Independent, read-only audit of the first live A02 outcome."""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ALLOC = "map01-v39-live-threat-guard-a02-20261009"
ROOT = REPO / "results-local/doom" / ALLOC


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    freeze = read_json(ROOT / "FREEZE.json")
    events = [json.loads(line) for line in (ROOT / "episode/runtime/events.jsonl").read_text().splitlines()]
    protocol = [json.loads(line) for line in (ROOT / "episode/planner-protocol.jsonl").read_text().splitlines()]
    accepted = [row for row in events if row.get("event") == "accepted"]
    terminals = [row for row in events if row.get("event") == "terminal"]
    typed = [row for row in events if row.get("event") == "typed_observation"]
    observations = [row for row in events if row.get("event") == "observation"]
    completed = [row["message"]["params"]["turn"] for row in protocol
                 if row.get("message", {}).get("method") == "turn/completed"]
    turn_starts = [row for row in protocol if row.get("direction") == "send_prepared" and
                   row.get("message", {}).get("method") == "turn/start"]
    score = read_json(ROOT / "episode/runtime/score.json")
    failure = read_json(ROOT / "episode/controller-failure.json")
    fixture = REPO / "research/doom/fixtures/map01-threat-contact-v2"
    host_receipts = [json.loads(line) for line in (ROOT / "host-image-receipts.jsonl").read_text().splitlines()]
    turns = [{"status": row.get("status"), "duration_ms": row.get("durationMs"),
              "agent_messages": sum(item.get("type") == "agentMessage" for item in row.get("items", []))}
             for row in completed]
    health = [row["signals"]["health"]["value"] for row in typed]
    ammo = [row["signals"]["ammo"]["value"] for row in typed]
    source_hashes_ok = all(sha(REPO / name) == digest for name, digest in freeze["source_hashes"].items())
    images_ok = all(sha(item["host_path"]) == item["sha256"] and
                    Path(item["host_path"]).stat().st_size == item["bytes"]
                    for row in host_receipts for item in row["images"])
    release_rows = [row for row in events if row.get("event") == "input_released"]
    released_empty = all(row.get("owner_release", {}).get("verified") is True and
                         row["owner_release"].get("keys_down") == [] and
                         row["owner_release"].get("buttons_down") == [] and
                         row["owner_release"].get("keys_unknown") == []
                         for row in release_rows)
    exact_event_frames = len(observations) == len(list((ROOT / "episode/runtime").glob("[0-9][0-9][0-9].png")))
    failed_terminal = next((row for row in terminals if row.get("id") == "cover-3"), {})
    failure_text = "up_batch requires the active input lease"
    dynamic = {"health_min": min(health), "health_max": max(health),
               "ammo_min": min(ammo), "ammo_max": max(ammo),
               "health_values": sorted(set(health)), "ammo_values": sorted(set(ammo)),
               "authored_health_guard_hard_crossing": False,
               "interpretation": "health fell in two soft-change intervals (97->91 and 91->85); the authored minimums were not crossed, so hard guard invalidation was not exposed"}
    checks = {
        "source_hashes_match_freeze": source_hashes_ok,
        "fixture_hashes_match_freeze": sha(fixture / "fixture.json") == freeze["fixture_manifest_sha256"] and
                                         sha(fixture / "save.png") == freeze["fixture_save_sha256"],
        "wad_hash_match_expected": freeze["wad_sha256"] == "a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b",
        "host_verified_all_forwarded_images": images_ok and len(host_receipts) == 4,
        "four_model_turns_started_and_completed": len(turn_starts) == 4 and len(completed) == 4 and
                                                   all(row["status"] == "completed" for row in completed),
        "all_protocol_images_are_retained": len(host_receipts) == len(turn_starts),
        "observations_reconcile_to_pngs": exact_event_frames and len(typed) == len(observations),
        "accepted_programs_have_terminals": {row["id"] for row in accepted} == {row["id"] for row in terminals},
        "reported_cancel_releases_are_empty": released_empty and failure.get("input_releases_verified_empty") is True,
        "runtime_failure_retained": failure.get("primary_error_type") == "RuntimeError" and
                                    failure.get("failed_stage") == "cover_terminal_validation" and
                                    failure_text in (ROOT / "guest.stderr.txt").read_text(errors="replace"),
        "score_is_nonterminal": score.get("map_exit") is False and score.get("episode_finished") is False,
    }
    value = {
        "schema": "map01-v39-live-threat-guard-audit-v1",
        "allocation": ALLOC,
        "audit_code_sha256": sha(__file__),
        "status": "FAIL_RETAIN_FIRST_RUNTIME_FAILURE" if not checks["runtime_failure_retained"] or
                  not checks["accepted_programs_have_terminals"] else "RETAINED_RUNTIME_FAILURE",
        "formal_pass": False,
        "checks": checks,
        "counts": {"model_turns_started": len(turn_starts), "model_turns_completed": len(completed),
                   "accepted_programs": len(accepted), "terminals": len(terminals),
                   "typed_observations": len(typed), "exact_observations": len(observations),
                   "host_verified_image_requests": len(host_receipts), "verified_empty_release_events": len(release_rows)},
        "model_turns": turns,
        "health_ammo": dynamic,
        "runtime_failure": {"stage": failure.get("failed_stage"), "error": failure_text,
                            "cover_terminal_status": failed_terminal.get("status"),
                            "release_verified_empty": bool(failed_terminal.get("release", {}).get("verified") is True and
                                                            failed_terminal.get("release", {}).get("keys_down") == [] and
                                                            failed_terminal.get("release", {}).get("keys_unknown") == [])},
        "score": score,
        "scope": "One live MAP01 episode on a dedicated OrbStack arm64 VM. It does not establish hard health-guard behavior because no authored health threshold was crossed; the controller stopped on a V15 release-batch runtime failure. No retry was made.",
    }
    (ROOT / "AUDIT.json").write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(value, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
