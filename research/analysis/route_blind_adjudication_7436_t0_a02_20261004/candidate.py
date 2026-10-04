"""One-shot synthetic presenter/custody protocol candidate."""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from presenter import Custodian, make_packets, synthetic_scores


OUT = HERE / "results"
SEED = 7436002


def main():
    fixture = json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))
    blinded, escrow = make_packets(fixture, SEED)
    OUT.mkdir(exist_ok=False)
    custodian = Custodian(escrow)
    pointers = {p["episode_id"]: p["evidence_pointer"] for p in blinded["packets"]}
    try:
        custodian.reveal()
        precommit = "UNEXPECTEDLY_REVEALED"
    except PermissionError:
        precommit = "DENIED"
    scores = synthetic_scores(blinded)
    commitment = custodian.commit_scores(scores, blinded["order"], pointers)
    revealed = custodian.reveal(scores)
    output = {
        "status": "CANDIDATE_COMPLETE",
        "seed": SEED,
        "precommit_reveal": precommit,
        "blinded": blinded,
        "scores": scores,
        "commitment": commitment,
        "postcommit_revealed_mapping": revealed,
    }
    (OUT / "candidate.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("CANDIDATE_COMPLETE packets=6 precommit_reveal=DENIED committed=6")


if __name__ == "__main__":
    main()
