"""Build two controlled synthetic episodes from one retained fake-display pair."""
import copy
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def shifted(value, delta, key=None):
    if isinstance(value, dict):
        return {k: shifted(v, delta, k) for k, v in value.items()}
    if isinstance(value, list):
        if key in {"interval", "physical_down_interval", "physical_up_interval"}:
            return [v + delta if type(v) is int else v for v in value]
        return [shifted(v, delta) for v in value]
    if type(value) is int and (key or "").endswith("_ns"):
        return value + delta
    if key == "actuation_id" and isinstance(value, str):
        return value.replace(":g1:", ":g2:")
    if key == "press_id" and isinstance(value, str):
        return value.replace(":r1:", ":r3:")
    if key == "release_id" and isinstance(value, str):
        return value.replace(":r2:", ":r4:")
    return value


def main():
    base = [json.loads(x) for x in (HERE / "BASE_PAIR.jsonl").read_text().splitlines() if x]
    second = [shifted(copy.deepcopy(row), 1_000_000) for row in base]
    rows = base + second
    target = HERE / "INPUT_EVENTS.jsonl"
    target.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows))
    print(json.dumps({"event_count": len(rows), "episode_actuation_ids": sorted({
        row["physical_key_measurement"]["actuation_id"] for row in rows}),
        "same_outer_context": len({(r["id"], r["step"], r["owner_id"], r["intent_token"], r["key"]) for r in rows}) == 1,
        "second_episode_shift_ns": 1_000_000}, sort_keys=True))


if __name__ == "__main__":
    main()
