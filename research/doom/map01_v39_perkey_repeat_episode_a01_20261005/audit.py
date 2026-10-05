"""Independent raw-only reconstruction for repeated same-key episodes."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def audit_rows(rows):
    by_id = {}
    for row in rows:
        edge = row["physical_key_measurement"]["adapter_edge"]
        by_id.setdefault(edge["actuation_id"], []).append(row)
    if len(by_id) != 2:
        raise ValueError("two distinct actuation identities required")
    out = []
    outer = set()
    for aid, pair in by_id.items():
        if len(pair) != 2:
            raise ValueError("actuation cardinality mismatch")
        down = next((r for r in pair if r.get("event") == "input_admission"), None)
        up = next((r for r in pair if r.get("event") == "input_release_measurement"), None)
        if down is None or up is None:
            raise ValueError("edge pair incomplete")
        identity = tuple(down.get(k) for k in ("id", "step", "owner_id", "intent_token", "key"))
        if identity != tuple(up.get(k) for k in ("id", "step", "owner_id", "intent_token", "key")):
            raise ValueError("outer context differs within pair")
        outer.add(identity)
        dm, um = down["physical_key_measurement"], up["physical_key_measurement"]
        de, ue = dm["adapter_edge"], um["adapter_edge"]
        if (de.get("edge"), ue.get("edge"), dm.get("identity_status"), um.get("identity_status")) != (
                "down", "up", "MINTED", "RETIRED"):
            raise ValueError("edge/lifecycle mismatch")
        if not (aid and de.get("actuation_id") == dm.get("actuation_id") ==
                ue.get("actuation_id") == um.get("actuation_id")):
            raise ValueError("actuation identity mismatch")
        if any(x is not False for x in (dm.get("grants_input_authority"), um.get("grants_input_authority"),
                                        dm.get("application_consumption_observed"),
                                        um.get("application_consumption_observed"))):
            raise ValueError("authority/effect scope mismatch")
        di, ui = de["interval"], ue["interval"]
        if (dm["bracket"].get("physical_down_interval") != di or
                um["bracket"].get("physical_up_interval") != ui or
                not (type(di) is list and type(ui) is list and len(di) == len(ui) == 2) or
                not all(type(v) is int for v in di + ui) or
                not (di[0] <= di[1] <= ui[0] <= ui[1])):
            raise ValueError("raw interval/bracket invalid")
        out.append({"actuation_id": aid, "context": dict(zip(
            ("id", "step", "owner_id", "intent_token", "key"), identity)),
            "down_state_interval_ns": di, "up_state_interval_ns": ui,
            "hold_duration_lower_bound_ns": ui[0]-di[1],
            "hold_duration_upper_bound_ns": ui[1]-di[0]})
    if len(outer) != 1:
        raise ValueError("episodes do not share one outer action context")
    out.sort(key=lambda x: x["down_state_interval_ns"][0])
    if any(out[i]["up_state_interval_ns"][1] >= out[i+1]["down_state_interval_ns"][0]
           for i in range(len(out)-1)):
        raise ValueError("episodes overlap or lack a gap")
    return out


def main():
    raw = (HERE / "INPUT_EVENTS.jsonl").read_bytes()
    freeze_bytes = (HERE / "FREEZE.json").read_bytes()
    freeze = json.loads(freeze_bytes)
    if hashlib.sha256(raw).hexdigest() != freeze.get("source_input_sha256"):
        raise ValueError("frozen input hash mismatch")
    for name, expected_hash in freeze["source_sha256"].items():
        path = HERE.parent / "map01_v39_perkey_measurement_consumer_a03_20261005" / "candidate.py" if name == "baseline_A03_candidate.py" else HERE / name
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected_hash:
            raise ValueError("frozen source mismatch: " + name)
    rows = [json.loads(x) for x in raw.decode().splitlines() if x]
    result = json.loads((HERE / "results" / "a01" / "RESULT.json").read_text())
    expected = audit_rows(rows)
    errors = []
    if result.get("status") != "PASS_MULTI_EPISODE_CONSTRUCTION_SCOPED": errors.append("status")
    if result.get("input_sha256") != hashlib.sha256(raw).hexdigest(): errors.append("input hash")
    if result.get("freeze_sha256") != hashlib.sha256(freeze_bytes).hexdigest(): errors.append("freeze hash")
    candidate = result.get("candidate", {})
    if candidate.get("episode_count") != 2 or candidate.get("episodes") != expected: errors.append("raw reconstruction")
    report = {"status": "PASS_RAW_RECONSTRUCTION_SCOPED" if not errors else "FAIL_AUDIT",
              "input_sha256": hashlib.sha256(raw).hexdigest(), "episode_count": len(expected),
              "independent_episodes": expected, "errors": errors,
              "auditor_imports_candidate": False,
              "scope": "synthetic CPU fixture; fake-display fields cloned and shifted, no hardware/game/task effect"}
    dest = HERE / "results" / "a01" / "AUDIT.json"
    dest.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps(report, sort_keys=True))
    if errors: raise SystemExit(1)


if __name__ == "__main__":
    main()
