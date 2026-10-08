"""One-shot synthetic raw-row generator for #626 audit identity T0."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixture.json"
RAW = HERE / "candidate_raw.json"


def released():
    return {"terminal": {"status": "completed", "release": {
        "verified": True, "keys_down": [], "buttons_down": []}}}


def row(case, fixture):
    arm = case["arm"]
    out = {
        **case,
        "runtime_bundle_sha256": fixture["runtime_bundle_sha256"],
        "fixture_id": fixture["fixture_id"],
        "fixture_seed": fixture["seed"],
        "active_arbitration": {"selected": {"locomotion": {"proposal_id": "threat-g1"}}},
        "post_handoff_arbitration": {},
        "threat_exec": released(),
        "score": {"kill_count": 0, "death_count": 0, "map_exit": False, "player_dead": False},
        "final_health": 100,
        "final_ammo": 50,
        "stderr": "",
        "stale_submit_count": 0 if arm == "candidate" else 1,
        "stale_exec": None,
        "fresh_arbitration": {},
        "fresh_exec": None,
    }
    if arm == "baseline":
        out["post_handoff_arbitration"] = {"selected": {"locomotion": {"proposal_id": "deopt-g1"}}}
        out["stale_exec"] = released()
    else:
        out["post_handoff_arbitration"] = {"selected": {}, "deferred": [
            {"proposal_id": "deopt-g1", "reason": "STALE_RESOURCE_GENERATION"}]}
        out["fresh_arbitration"] = {"selected": {"locomotion": {"proposal_id": "deopt-g2"}}}
        out["fresh_exec"] = released()
    return out


def main():
    if RAW.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS")
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    raw = {"schema": "map01-threat-deopt-626-audit-identity-raw-v1",
           "fixture_sha256": __import__("hashlib").sha256(FIXTURE.read_bytes()).hexdigest(),
           "rows": [row(case, fixture) for case in fixture["cases"]]}
    RAW.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "CANDIDATE_COMPLETE", "rows": len(raw["rows"]),
                      "output": RAW.name}, sort_keys=True))


if __name__ == "__main__":
    main()
