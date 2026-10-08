"""CPU-only consumer for multiple same-key V39 measurement episodes."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def need(ok, message):
    if not ok:
        raise ValueError(message)


def pair_identity(row):
    return (row["id"], row["step"], row["owner_id"], row["intent_token"], row["key"])


def reconstruct(rows):
    need(type(rows) is list and len(rows) == 4, "exactly two down/up episodes required")
    grouped = {}
    for row in rows:
        need(type(row) is dict, "row must be object")
        measure = row.get("physical_key_measurement")
        need(type(measure) is dict, "measurement missing")
        aid = measure.get("actuation_id")
        need(type(aid) is str and aid, "actuation_id required")
        grouped.setdefault(aid, []).append(row)
    need(len(grouped) == 2, "exactly two distinct actuation identities required")
    episodes = []
    for aid, pair in grouped.items():
        need(len(pair) == 2, "actuation must have exactly two edges")
        down = [r for r in pair if r.get("event") == "input_admission"]
        up = [r for r in pair if r.get("event") == "input_release_measurement"]
        need(len(down) == len(up) == 1, "one down and one up required per actuation")
        down, up = down[0], up[0]
        need(pair_identity(down) == pair_identity(up), "episode context mismatch")
        dm, um = down["physical_key_measurement"], up["physical_key_measurement"]
        de, ue = dm["adapter_edge"], um["adapter_edge"]
        need(dm.get("identity_status") == "MINTED" and um.get("identity_status") == "RETIRED",
             "actuation lifecycle mismatch")
        need(de.get("edge") == "down" and ue.get("edge") == "up", "edge direction mismatch")
        need(de.get("actuation_id") == ue.get("actuation_id") == aid, "actuation identity mismatch")
        need(all(x is False for x in (dm.get("grants_input_authority"), um.get("grants_input_authority"),
                                      dm.get("application_consumption_observed"),
                                      um.get("application_consumption_observed"))),
             "authority/effect scope changed")
        di, ui = de.get("interval"), ue.get("interval")
        need(type(di) is list and len(di) == 2 and all(type(v) is int for v in di), "bad down interval")
        need(type(ui) is list and len(ui) == 2 and all(type(v) is int for v in ui), "bad up interval")
        need(di[0] <= di[1] <= ui[0] <= ui[1], "episode timing invalid")
        need(dm["bracket"].get("physical_down_interval") == di
             and um["bracket"].get("physical_up_interval") == ui, "source bracket mismatch")
        episodes.append({"actuation_id": aid, "context": dict(zip(
            ("id", "step", "owner_id", "intent_token", "key"), pair_identity(down))),
            "down_state_interval_ns": di, "up_state_interval_ns": ui,
            "hold_duration_lower_bound_ns": ui[0] - di[1],
            "hold_duration_upper_bound_ns": ui[1] - di[0]})
    episodes.sort(key=lambda x: x["down_state_interval_ns"][0])
    need(all(episodes[i]["up_state_interval_ns"][1] < episodes[i+1]["down_state_interval_ns"][0]
             for i in range(len(episodes)-1)), "same-key episodes overlap or lack an observed gap")
    need(len({tuple(x["context"].items()) for x in episodes}) == 1,
         "episodes must share action/step/owner/intent/key context")
    return {"schema": "map01-v39-perkey-repeat-episode-a01",
            "episodes": episodes, "episode_count": len(episodes),
            "same_key": episodes[0]["context"]["key"],
            "authority_granted": False, "application_effect_observed": False,
            "scope": "deterministic duplicated fake-display rows; not physical/task occupancy"}


def main():
    raw = (HERE / "INPUT_EVENTS.jsonl").read_bytes()
    freeze_bytes = (HERE / "FREEZE.json").read_bytes()
    freeze = json.loads(freeze_bytes)
    need(hashlib.sha256(raw).hexdigest() == freeze.get("source_input_sha256"), "frozen input hash mismatch")
    for name, expected in freeze["source_sha256"].items():
        path = HERE.parent / "map01_v39_perkey_measurement_consumer_a03_20261005" / "candidate.py" if name == "baseline_A03_candidate.py" else HERE / name
        need(hashlib.sha256(path.read_bytes()).hexdigest() == expected, "frozen source hash mismatch: " + name)
    rows = [json.loads(x) for x in raw.decode().splitlines() if x]
    result = reconstruct(rows)
    out = {"status": "PASS_MULTI_EPISODE_CONSTRUCTION_SCOPED", "candidate": result,
           "input_sha256": hashlib.sha256(raw).hexdigest(),
           "freeze_sha256": hashlib.sha256(freeze_bytes).hexdigest()}
    path = HERE / "results" / "a01" / "RESULT.json"
    path.write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()
