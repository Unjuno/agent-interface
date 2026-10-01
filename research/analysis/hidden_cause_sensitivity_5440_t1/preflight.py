from __future__ import annotations

import argparse
import hashlib
import json
from fractions import Fraction
from pathlib import Path


def validate(data: dict) -> None:
    assert data.get("schema") == "hidden-cause-sensitivity-t1-input-v1"
    claims = data.get("claims")
    assert isinstance(claims, list) and len(claims) == 16
    assert data.get("pair_count") == 8 and data.get("case_count") == 16
    pairs: dict[str, list[str]] = {}
    for claim in claims:
        case_id = claim["case_id"]
        pair = claim["matched_pair"]
        pairs.setdefault(pair, []).append(case_id[-1])
        evidence = claim["evidence"]
        causes = claim["latent_causes"]
        assert len(evidence) == 2 and all(x["provenance"] == "ATTESTED" for x in evidence)
        assert len(causes) == 3 and len({x["cause_id"] for x in causes}) == 3
        evidence_ids = {x["evidence_id"] for x in evidence}
        cause_ids = {x["cause_id"] for x in causes}
        assert all(Fraction(x["margin"]) > 0 for x in evidence)
        assert all(Fraction(x["bound"]) >= 0 for x in causes)
        for edge in claim["influence_edges"]:
            assert edge["cause_id"] in cause_ids and edge["evidence_id"] in evidence_ids
            assert Fraction(edge["adverse_weight"]) >= 0
        shared = [x for x in claim["influence_edges"] if x["cause_id"] == "shared-clock"]
        assert {x["evidence_id"] for x in shared} == evidence_ids
    assert len(pairs) == 8 and all(sorted(v) == ["A", "B"] for v in pairs.values())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    data_bytes = args.input.read_bytes()
    candidate_bytes = args.input.with_name("candidate.py").read_bytes()
    if hashlib.sha256(data_bytes).hexdigest() != "02ba32c8f1a4c8ab3d65e7fa138f459602a22a8ab2224859d9b916315a14f20e":
        raise SystemExit("STOP_FROZEN_INPUT_SHA256")
    if hashlib.sha256(candidate_bytes).hexdigest() != "ec6adc9966d439a247f30ccb50b42f1185f7522393e60f2b65daabaf36e1a680":
        raise SystemExit("STOP_FROZEN_CANDIDATE_SHA256")
    validate(json.loads(data_bytes))
    print("PASS_T1_INPUT_STRUCTURE_ONLY claims=16 pairs=8 scientific_result=NONE")


if __name__ == "__main__":
    main()
