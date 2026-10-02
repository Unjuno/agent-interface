"""Independent raw-only auditor. Deliberately does not import candidate.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

EXPECTED_POLICIES = {"NO_COORDINATION", "CENTRAL_CLAIMS", "LOCAL_MARKERS"}
EXPECTED_SCENARIOS = {
    "visible_contention", "delayed_observation", "marker_loss", "forged_marker",
    "stale_generation", "duplicate_delivery", "owner_crash", "external_mutation",
    "no_contention",
}


def validate(raw: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if raw.get("schema") != "stigmergic_coordination_5346_t0_raw_v1":
        errors.append("schema mismatch")
    if raw.get("source_issue") != 5346:
        errors.append("source Issue mismatch")
    if set(raw.get("policies", [])) != EXPECTED_POLICIES:
        errors.append("policy set mismatch")
    if raw.get("scenario_count") != len(EXPECTED_SCENARIOS):
        errors.append("scenario count mismatch")
    if raw.get("cell_count") != len(EXPECTED_SCENARIOS) * len(EXPECTED_POLICIES):
        errors.append("cell count mismatch")
    scenarios = raw.get("scenarios", [])
    names = [s.get("name") for s in scenarios]
    if set(names) != EXPECTED_SCENARIOS or len(names) != len(set(names)):
        errors.append("scenario identities mismatch")

    cells = raw.get("cells", [])
    keys = [(c.get("scenario"), c.get("policy")) for c in cells]
    expected_keys = {(s, p) for s in EXPECTED_SCENARIOS for p in EXPECTED_POLICIES}
    if set(keys) != expected_keys or len(keys) != len(set(keys)):
        errors.append("cell identity/uniqueness mismatch")

    by_key = {(c.get("scenario"), c.get("policy")): c for c in cells}
    for key, cell in by_key.items():
        events = cell.get("events", [])
        grants = [e for e in events if e.get("kind") == "LEASE_GRANTED"]
        if any(e.get("basis") != "authoritative_lease" for e in grants):
            errors.append(f"non-authoritative lease grant at {key}")
        if any(e.get("kind") == "MARKER_AUTHORITY_GRANTS" and e.get("count") != 0
               for e in events):
            errors.append(f"marker granted authority at {key}")
        if cell.get("unsafe_admissions") != 0 or not cell.get("all_effects_have_authoritative_gate"):
            errors.append(f"unsafe admission summary at {key}")
        if len(cell.get("completed_targets", [])) != cell.get("completion_count"):
            errors.append(f"completion total mismatch at {key}")
        if len(set(cell.get("completed_targets", []))) != cell.get("completion_count"):
            errors.append(f"duplicate completion in summary at {key}")
        oracle_targets = {e.get("target") for e in events if e.get("kind") == "EFFECT_CONFIRMED"}
        if oracle_targets != set(cell.get("completed_targets", [])):
            errors.append(f"raw effect evidence mismatch at {key}")
        event_collisions = sum(e.get("kind") == "LEASE_CONFLICT" for e in events)
        if event_collisions != cell.get("collision_retries"):
            errors.append(f"collision count mismatch at {key}")
        event_coord = sum(e.get("kind") in {"MARKER_PUBLISH", "MARKER_OBSERVED"}
                          for e in events)
        central_events = sum(e.get("kind") in {"CENTRAL_CLAIM_REQUEST", "CENTRAL_CLAIM_GRANT"}
                             for e in events)
        reconstructed_coord = event_coord if cell.get("policy") == "LOCAL_MARKERS" else (
            central_events if cell.get("policy") == "CENTRAL_CLAIMS" else 0)
        if reconstructed_coord != cell.get("coordination_events"):
            errors.append(f"coordination count mismatch at {key}")

    primary_baseline = by_key.get(("visible_contention", "NO_COORDINATION"), {})
    primary_local = by_key.get(("visible_contention", "LOCAL_MARKERS"), {})
    primary_central = by_key.get(("visible_contention", "CENTRAL_CLAIMS"), {})
    if primary_baseline.get("collision_retries") != 1 or primary_local.get("collision_retries") != 0:
        errors.append("primary contention discriminator failed")
    if primary_local.get("coordination_events") != 2 or primary_central.get("coordination_events") != 4:
        errors.append("primary coordination accounting discriminator failed")

    for name in EXPECTED_SCENARIOS:
        for policy in EXPECTED_POLICIES:
            cell = by_key.get((name, policy), {})
            if cell.get("completion_count") != 2:
                errors.append(f"incomplete two-target workflow at {(name, policy)}")
    for name in ("forged_marker", "stale_generation", "marker_loss", "delayed_observation"):
        cell = by_key.get((name, "LOCAL_MARKERS"), {})
        if cell.get("collision_retries") != 1:
            errors.append(f"fail-closed advisory control mismatch at {name}")
    if by_key.get(("duplicate_delivery", "LOCAL_MARKERS"), {}).get("collision_retries") != 0:
        errors.append("duplicate trace delivery was not deduplicated")
    crash = by_key.get(("owner_crash", "LOCAL_MARKERS"), {})
    if crash.get("recovery_latency_ticks", 0) <= 0:
        errors.append("owner crash did not exercise lease-expiry recovery")
    external_events = [e for e in by_key.get(("external_mutation", "LOCAL_MARKERS"), {}).get("events", [])]
    if not any(e.get("kind") == "STALE_GENERATION_REFUSED" for e in external_events):
        errors.append("external mutation control missing stale-generation refusal")
    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python -B audit.py RAW.json", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    raw = json.loads(path.read_text(encoding="utf-8"))
    errors = validate(raw)
    result = {"status": "PASS_READONLY" if not errors else "FAIL_AUDIT",
              "cell_count": raw.get("cell_count"), "errors": errors}
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
