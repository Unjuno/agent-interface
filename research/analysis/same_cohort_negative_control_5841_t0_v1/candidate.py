"""Small synthetic route-comparison diagnostic for Issue #5841 T0."""

import json
from pathlib import Path


def analyze(fixture):
    routes = fixture["routes"]
    episodes = fixture["episodes"]
    assigned = {episode["id"]: episode["seal"] for episode in episodes}
    output = {"schema": "issue-5841-negative-control-t0-result-v1", "cases": []}

    for scenario in fixture["scenarios"]:
        missing = {(item["route"], item["episode"]) for item in scenario["missing"]}
        overrides = scenario["join_overrides"]
        ledger = []
        known = {route: [] for route in routes}
        missing_by_route = {route: 0 for route in routes}
        missing_by_episode = {episode["id"]: set() for episode in episodes}
        join_mismatch = False
        actual_sentinel_change = False
        export_snapshot_mismatch = False

        for route in routes:
            for index, episode in enumerate(episodes):
                episode_id = episode["id"]
                key = f"{route}:{episode_id}"
                override = overrides.get(key, {})
                joined_id = override.get("joined_id", episode_id)
                joined_seal = override.get("joined_seal", assigned[episode_id])
                value = scenario["primary"][route][index]
                is_missing = (route, episode_id) in missing
                if is_missing:
                    value = None
                    missing_by_route[route] += 1
                    missing_by_episode[episode_id].add(route)
                else:
                    known[route].append(value)

                before = 0
                after = scenario["sentinel_after"][route][index]
                exported = scenario["sentinel_export"][route][index]
                join_mismatch |= joined_id != episode_id or joined_seal != assigned[episode_id]
                actual_sentinel_change |= before != after
                export_snapshot_mismatch |= after != exported
                ledger.append(
                    {
                        "route": route,
                        "episode": episode_id,
                        "assigned_seal": assigned[episode_id],
                        "joined_id": joined_id,
                        "joined_seal": joined_seal,
                        "primary_value": value,
                        "primary_present": not is_missing,
                        "sentinel_before": before,
                        "sentinel_after_snapshot": after,
                        "sentinel_after_export": exported,
                    }
                )

        route_rates = {
            route: sum(values) / len(values) if values else None
            for route, values in known.items()
        }
        delta = route_rates["guarded"] - route_rates["direct"]
        reference_deck = (
            "PASS"
            if scenario["deck_pre"] == fixture["deck_expected"]
            and scenario["deck_post"] == fixture["deck_expected"]
            else "HOLD"
        )
        route_specific_missingness = (
            len(set(missing_by_route.values())) > 1
            or any(len(missing_routes) == 1 for missing_routes in missing_by_episode.values())
        )
        any_primary_outcome_missing = any(missing_by_route.values()) > 0
        flags = {
            "any_primary_outcome_missing": any_primary_outcome_missing,
            "route_specific_missingness": route_specific_missingness,
            "foreign_join_or_seal_mismatch": join_mismatch,
            "actual_sentinel_change": actual_sentinel_change,
            "sentinel_export_snapshot_mismatch": export_snapshot_mismatch,
        }

        if actual_sentinel_change:
            disposition = "COLLATERAL_FAIL"
        elif reference_deck == "HOLD":
            disposition = "ORACLE_DRIFT_HOLD"
        elif join_mismatch:
            disposition = "JOIN_INTEGRITY_HOLD"
        elif any_primary_outcome_missing:
            disposition = "ASCERTAINMENT_HOLD"
        elif export_snapshot_mismatch:
            disposition = "ASCERTAINMENT_HOLD"
        else:
            disposition = "NO_CONTROL_SIGNAL"

        output["cases"].append(
            {
                "id": scenario["id"],
                "primary_only_guarded_minus_direct": delta,
                "known_rows_by_route": {route: len(known[route]) for route in routes},
                "assigned_rows_by_route": {route: len(episodes) for route in routes},
                "reference_deck": reference_deck,
                "control_flags": flags,
                "disposition": disposition,
                "ledger": ledger,
            }
        )
    return output


if __name__ == "__main__":
    root = Path(__file__).parent
    frozen_fixture = json.loads((root / "fixture.json").read_text(encoding="utf-8"))
    print(json.dumps(analyze(frozen_fixture), sort_keys=True, indent=2))
