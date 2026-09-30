"""T2 toy gate: never call a claim robust when declared-family completeness is unknown."""
import hashlib
import json
import os
from fractions import Fraction
from pathlib import Path


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def q(value):
    return Fraction(value)


def enc(value):
    return f"{value.numerator}/{value.denominator}"


def model_graph(pair, data):
    return {
        "pair_id": pair["pair_id"],
        "nominal": pair["nominal"],
        "declared_risk": pair["declared_risk"],
        "family_id": data["declared_family_id"],
    }


def decide(pair, data, mode):
    graph = model_graph(pair, data)
    digest = hashlib.sha256(canon(graph)).hexdigest()
    attestation = {
        "issuer": data["trusted_issuer"],
        "scope_sha256": digest,
        "verified": True,
    }
    if mode == "missing_attestation":
        attestation = None
    elif mode == "unverified_family":
        attestation = None
    elif mode == "unverified_attestation":
        attestation["verified"] = False
    elif mode == "wrong_scope_digest":
        attestation["scope_sha256"] = "0" * 64
    elif mode == "wrong_issuer":
        attestation["issuer"] = "untrusted-issuer"

    declared_worst = q(pair["nominal"]) - q(pair["declared_risk"])
    valid_complete = (
        attestation is not None
        and attestation.get("verified") is True
        and attestation.get("issuer") == data["trusted_issuer"]
        and attestation.get("scope_sha256") == digest
    )
    if not valid_complete:
        decision = "UNIDENTIFIED"
    elif declared_worst > 0:
        decision = "ROBUST"
    else:
        decision = "SENSITIVE"
    return {
        "case_id": pair["pair_id"] + ":" + mode,
        "pair_id": pair["pair_id"],
        "mode": mode,
        "declared_family_sha256": digest,
        "declared_worst_margin": enc(declared_worst),
        "decision": decision,
        "authority": False,
    }


def run(data, input_bytes, source_bytes):
    rows = []
    for pair in data["pairs"]:
        rows.append(decide(pair, data, "attested_complete"))
        # The same observed graph is evaluated in an unverified-world row. The
        # omitted cause is audit-only truth; it is never disclosed to candidate.
        rows.append(decide(pair, data, "unverified_family"))
    control_pair = data["pairs"][0]
    rows.extend(decide(control_pair, data, mode) for mode in data["candidate_controls"])
    return {
        "schema": "hidden-cause-sensitivity-t2-raw-v1",
        "base_main_sha": os.environ["EXPERIMENT_BASE_SHA"],
        "container": {
            "image": os.environ["EXPERIMENT_IMAGE"],
            "platform": os.environ["EXPERIMENT_PLATFORM"],
            "network": "none",
        },
        "input_sha256": hashlib.sha256(input_bytes).hexdigest(),
        "candidate_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "rows": rows,
        "authority_grants": 0,
        "network_calls": 0,
        "model_calls": 0,
        "gui_input_calls": 0,
    }


def main():
    root = Path(__file__).parent
    input_bytes = (root / "cases.json").read_bytes()
    source_bytes = Path(__file__).read_bytes()
    raw = run(json.loads(input_bytes), input_bytes, source_bytes)
    out = Path("/out/raw.json")
    out.write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(raw["rows"]), "decisions": {
        key: sum(row["decision"] == key for row in raw["rows"])
        for key in ("ROBUST", "SENSITIVE", "UNIDENTIFIED")
    }}))


if __name__ == "__main__":
    main()
