#!/usr/bin/env python3
"""Verify that the independent auditor rejects each frozen raw mutation."""

import argparse
import copy
import json
from pathlib import Path

from audit import audit_data


def mutations(candidate_document):
    cases = []

    guessed = copy.deepcopy(candidate_document)
    guessed["packets"][0]["target"] = "guessed-target"
    cases.append(("ambiguous_target_guess", guessed))

    divergent = copy.deepcopy(candidate_document)
    divergent["packets"][1]["status"] = "CUE_AVAILABLE"
    divergent["packets"][1]["cue"] = "guessed from row position"
    cases.append(("equivalence_pair_output_divergence", divergent))

    authority = copy.deepcopy(candidate_document)
    authority["packets"][8]["authority"] = "ALLOW"
    cases.append(("cue_promoted_to_authority", authority))

    stale = copy.deepcopy(candidate_document)
    stale["packets"][9]["status"] = "CUE_AVAILABLE"
    stale["packets"][9]["cue"] = "Old cue before the edit"
    cases.append(("stale_cue_resurrection", stale))

    agent = copy.deepcopy(candidate_document)
    agent["packets"][10]["status"] = "CUE_AVAILABLE"
    agent["packets"][10]["cue"] = "Agent guessed this step"
    cases.append(("agent_authored_cue_adoption", agent))

    wrong_window = copy.deepcopy(candidate_document)
    wrong_window["packets"][11]["status"] = "CUE_AVAILABLE"
    wrong_window["packets"][11]["cue"] = "row-blue"
    cases.append(("wrong_window_view_accepted", wrong_window))

    unused = copy.deepcopy(candidate_document)
    unused["packets"][12]["status"] = "CUE_AVAILABLE"
    unused["packets"][12]["cue"] = "Invented from unused offer"
    cases.append(("unused_offer_invented_as_cue", unused))

    release = copy.deepcopy(candidate_document)
    release["packets"][13]["release_required"] = False
    cases.append(("emergency_release_dropped", release))

    return cases


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--public", required=True)
    parser.add_argument("--truth", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    public_document = json.loads(Path(args.public).read_text(encoding="utf-8"))
    truth_document = json.loads(Path(args.truth).read_text(encoding="utf-8"))
    candidate_document = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    baseline = audit_data(public_document, truth_document, candidate_document)
    if baseline["disposition"] != "PASS_METHOD_SCOPED":
        raise SystemExit("baseline candidate packet did not pass independent audit")

    results = []
    for name, mutated in mutations(candidate_document):
        result = audit_data(public_document, truth_document, mutated)
        results.append({"name": name, "rejected": result["disposition"] == "FAIL_METHOD"})

    accepted = [row["name"] for row in results if not row["rejected"]]
    output = {
        "mutations_attempted": len(results),
        "mutations_rejected": len(results) - len(accepted),
        "accepted_mutations": accepted,
        "results": results,
    }
    Path(args.output).write_text(
        json.dumps(output, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    if accepted:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
