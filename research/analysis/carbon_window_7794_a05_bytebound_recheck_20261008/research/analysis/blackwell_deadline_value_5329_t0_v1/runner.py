import hashlib
import json
from pathlib import Path


OUT = Path("/out/formal01")
DEADLINE = 3
SAFE_PREPARE_UTILITY = 2
COMMIT_UTILITY = 10
STATES = ("safe", "blocked")
RAW_SIGNAL = {"safe": "CLEAR", "blocked": "BLOCKED"}
GARBLE = {"CLEAR": "TARGET_PRESENT", "BLOCKED": "TARGET_PRESENT"}
ARMS = {
    "RAW_NOW": ("raw", 1),
    "RAW_DELAYED": ("raw", 6),
    "COMPRESSED_NOW": ("compressed", 1),
    "COMPRESSED_DELAYED": ("compressed", 6),
}


def observation(state, channel):
    raw = RAW_SIGNAL[state]
    return raw if channel == "raw" else GARBLE[raw]


def choose(obs, channel, arrival):
    if arrival > DEADLINE:
        return "WAIT"
    if channel == "raw" and obs == "CLEAR":
        return "IRREVERSIBLE_COMMIT"
    return "SAFE_REVERSIBLE_PREPARE"


def admit(action, channel, obs, arrival):
    if action == "IRREVERSIBLE_COMMIT":
        return channel == "raw" and obs == "CLEAR" and arrival <= DEADLINE
    return action == "SAFE_REVERSIBLE_PREPARE" and arrival <= DEADLINE


def utility(state, action, admitted):
    if not admitted or action == "WAIT":
        return 0
    if action == "SAFE_REVERSIBLE_PREPARE":
        return SAFE_PREPARE_UTILITY
    if action == "IRREVERSIBLE_COMMIT" and state == "safe":
        return COMMIT_UTILITY
    raise AssertionError("unsafe or undefined effect reached scoring")


def build_raw():
    rows = []
    for arm, (channel, arrival) in ARMS.items():
        for state in STATES:
            obs = observation(state, channel)
            action = choose(obs, channel, arrival)
            admitted = admit(action, channel, obs, arrival)
            rows.append({"arm": arm, "channel": channel, "arrival": arrival,
                         "deadline": DEADLINE, "state": state, "observation": obs,
                         "action": action, "admitted": admitted,
                         "unsafe_effect": action == "IRREVERSIBLE_COMMIT" and state != "safe",
                         "utility": utility(state, action, admitted)})
    safety = []
    for state in STATES:
        obs = observation(state, "compressed")
        admitted = admit("IRREVERSIBLE_COMMIT", "compressed", obs, 1)
        safety.append({"state": state, "channel": "compressed", "arrival": 1,
                       "observation": obs, "requested_action": "IRREVERSIBLE_COMMIT",
                       "admitted": admitted, "unsafe_effect": admitted and state != "safe",
                       "reason": "INSUFFICIENT_INFORMATION" if not admitted else "ADMITTED"})
    return {"schema": "issue5329-blackwell-deadline-raw-v1",
            "allocation": "5329-blackwell-deadline-t0-20261001-01",
            "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "deadline": DEADLINE, "safe_prepare_utility": SAFE_PREPARE_UTILITY,
            "commit_utility": COMMIT_UTILITY, "state_prior": {"safe": 0.5, "blocked": 0.5},
            "raw_signal": RAW_SIGNAL, "garble": GARBLE,
            "arms": {name: list(spec) for name, spec in ARMS.items()},
            "rows": rows, "compressed_irreversible_probes": safety}


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    doc = build_raw()
    encoded = json.dumps(doc, sort_keys=True, separators=(",", ":")) + "\n"
    (OUT / "raw.json").write_text(encoded, encoding="utf-8")
    print(json.dumps({"allocation": doc["allocation"], "rows": len(doc["rows"]),
                      "raw_sha256": hashlib.sha256(encoded.encode()).hexdigest()}, sort_keys=True))


if __name__ == "__main__":
    main()
