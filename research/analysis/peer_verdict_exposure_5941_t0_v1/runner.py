"""Finite T0 candidate for peer-verdict independence credit."""
import itertools
import json
import pathlib
import sys

VERIFIERS = ("V1", "V2", "V3")
POSSIBLE_EDGES = (("V1", "V2"), ("V1", "V3"), ("V2", "V3"))


def enumerate_cases():
    cases = []
    for truth in (False, True):
        for votes in itertools.product((False, True), repeat=3):
            for edge_mask in range(8):
                incoming = {verifier: [] for verifier in VERIFIERS}
                for bit, (source, target) in enumerate(POSSIBLE_EDGES):
                    if edge_mask & (1 << bit):
                        incoming[target].append(source)
                cases.append({
                    "case_id": f"t{int(truth)}-v{''.join(str(int(v)) for v in votes)}-e{edge_mask}",
                    "truth": truth,
                    "receipts": [
                        {"id": verifier, "verdict": vote,
                         "visible_peer_ids": incoming[verifier]}
                        for verifier, vote in zip(VERIFIERS, votes)
                    ],
                    "history_complete": True,
                    "commitment_valid": True,
                    "reported_edges_match_capture": True,
                })
    return cases


def adjudicate(case):
    invalid = {"count_only": "UNAVAILABLE",
               "exposure_aware": "UNKNOWN_INDEPENDENCE", "independent_ids": []}
    receipts = case.get("receipts")
    if (type(case.get("truth")) is not bool
            or case.get("history_complete") is not True
            or case.get("commitment_valid") is not True
            or case.get("reported_edges_match_capture") is not True
            or not isinstance(receipts, list) or len(receipts) != 3):
        return invalid
    by_id = {}
    for receipt in receipts:
        if not isinstance(receipt, dict) or receipt.get("id") not in VERIFIERS:
            return invalid
        if receipt["id"] in by_id or type(receipt.get("verdict")) is not bool:
            return invalid
        visible = receipt.get("visible_peer_ids")
        if not isinstance(visible, list) or len(set(visible)) != len(visible):
            return invalid
        by_id[receipt["id"]] = receipt
    if set(by_id) != set(VERIFIERS):
        return invalid

    position = {verifier: index for index, verifier in enumerate(VERIFIERS)}
    for receipt in receipts:
        for peer in receipt["visible_peer_ids"]:
            if peer not in position or position[peer] >= position[receipt["id"]]:
                return invalid

    votes = [by_id[verifier]["verdict"] for verifier in VERIFIERS]
    true_votes = sum(votes)
    if max(true_votes, 3 - true_votes) < 2:
        count_only = "NO_QUORUM"
    elif (true_votes >= 2) == case["truth"]:
        count_only = "CORRECT_QUORUM_PASS"
    else:
        count_only = "INCORRECT_QUORUM_PASS"

    independent = [verifier for verifier in VERIFIERS
                   if not by_id[verifier]["visible_peer_ids"]]
    independent_votes = [by_id[verifier]["verdict"] for verifier in independent]
    independent_true = sum(independent_votes)
    independent_false = len(independent_votes) - independent_true
    if max(independent_true, independent_false) < 2:
        exposure_aware = "NO_QUORUM"
    else:
        consensus = independent_true >= 2
        exposure_aware = ("CORRECT_QUORUM_PASS" if consensus == case["truth"]
                          else "INCORRECT_QUORUM_PASS")
    return {"count_only": count_only, "exposure_aware": exposure_aware,
            "independent_ids": independent}


def run():
    rows = []
    for case in enumerate_cases():
        rows.append({**case, "result": adjudicate(case)})
    sample = enumerate_cases()[0]
    controls = []
    for name, changes in (
        ("incomplete_history", {"history_complete": False}),
        ("invalid_commitment", {"commitment_valid": False}),
        ("capture_mismatch", {"reported_edges_match_capture": False}),
    ):
        controls.append({"name": name,
                         "result": adjudicate({**sample, **changes})})
    return {"schema": "peer-verdict-exposure-t0-raw-v1",
            "case_count": len(rows), "rows": rows,
            "unknown_controls": controls}


if __name__ == "__main__":
    destination = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("RAW.json")
    raw = run()
    destination.write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({"case_count": len(raw["rows"]), "output": str(destination)}))
