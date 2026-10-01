"""Independent raw-only audit; does not import runner.py."""
import json
import pathlib
import re
import sys

IDS = ["V1", "V2", "V3"]
EDGES = [("V1", "V2"), ("V1", "V3"), ("V2", "V3")]
CASE_ID = re.compile(r"t([01])-v([01]{3})-e([0-7])\\Z")


def decode_case_id(value):
    match = CASE_ID.fullmatch(value) if isinstance(value, str) else None
    if not match:
        return None
    truth_bit, votes, edge_bits = match.groups()
    return bool(int(truth_bit)), [bool(int(bit)) for bit in votes], int(edge_bits)


def expected_receipts(votes, edge_bits):
    incoming = {verifier: [] for verifier in IDS}
    for bit, (source, target) in enumerate(EDGES):
        if edge_bits & (1 << bit):
            incoming[target].append(source)
    return [{"id": verifier, "verdict": vote,
             "visible_peer_ids": incoming[verifier]}
            for verifier, vote in zip(IDS, votes)]


def expected_result(truth, receipts, flags):
    if flags != (True, True, True):
        return {"count_only": "UNAVAILABLE",
                "exposure_aware": "UNKNOWN_INDEPENDENCE", "independent_ids": []}
    if not isinstance(receipts, list) or len(receipts) != 3:
        return {"count_only": "UNAVAILABLE",
                "exposure_aware": "UNKNOWN_INDEPENDENCE", "independent_ids": []}
    if [row.get("id") if isinstance(row, dict) else None for row in receipts] != IDS:
        return {"count_only": "UNAVAILABLE",
                "exposure_aware": "UNKNOWN_INDEPENDENCE", "independent_ids": []}
    for row in receipts:
        if type(row.get("verdict")) is not bool or not isinstance(row.get("visible_peer_ids"), list):
            return {"count_only": "UNAVAILABLE",
                    "exposure_aware": "UNKNOWN_INDEPENDENCE", "independent_ids": []}
    position = {name: index for index, name in enumerate(IDS)}
    edge_set = set()
    for row in receipts:
        for source in row["visible_peer_ids"]:
            edge = (source, row["id"])
            if (source not in position or position[source] >= position[row["id"]]
                    or edge not in EDGES or edge in edge_set):
                return {"count_only": "UNAVAILABLE",
                        "exposure_aware": "UNKNOWN_INDEPENDENCE", "independent_ids": []}
            edge_set.add(edge)

    votes = [int(row["verdict"]) for row in receipts]
    yes = sum(votes)
    if max(yes, 3 - yes) < 2:
        ordinary = "NO_QUORUM"
    else:
        ordinary = ("CORRECT_QUORUM_PASS" if bool(yes >= 2) == truth
                    else "INCORRECT_QUORUM_PASS")

    independent = [row for row in receipts if not row["visible_peer_ids"]]
    independent_ids = [row["id"] for row in independent]
    independent_yes = sum(int(row["verdict"]) for row in independent)
    independent_no = len(independent) - independent_yes
    if max(independent_yes, independent_no) < 2:
        aware = "NO_QUORUM"
    else:
        consensus = independent_yes >= 2
        aware = ("CORRECT_QUORUM_PASS" if consensus == truth
                 else "INCORRECT_QUORUM_PASS")
    return {"count_only": ordinary, "exposure_aware": aware,
            "independent_ids": independent_ids}


def audit(raw):
    errors = []
    rows = raw.get("rows") if isinstance(raw, dict) else None
    if not isinstance(rows, list) or len(rows) != 128 or raw.get("case_count") != 128:
        count = len(rows) if isinstance(rows, list) else 0
        return {"status": "FAIL_RAW_INCOMPLETE", "errors": ["row_count_not_128"],
                "rows": count, "incorrect_count_only": 0,
                "incorrect_exposure_aware": 0, "double_credit_cases": 0}

    ids = [row.get("case_id") for row in rows if isinstance(row, dict)]
    expected_ids = {f"t{truth}-v{votes:03b}-e{edge}" for truth in range(2)
                    for votes in range(8) for edge in range(8)}
    if set(ids) != expected_ids or len(ids) != 128 or len(set(ids)) != 128:
        errors.append("case_id_inventory_mismatch")

    result_counts = {"incorrect_count_only": 0,
                     "incorrect_exposure_aware": 0, "double_credit_cases": 0}
    for row in rows:
        if not isinstance(row, dict):
            errors.append("row_not_object")
            continue
        decoded = decode_case_id(row.get("case_id"))
        if decoded is None:
            errors.append("malformed_case_id")
            continue
        truth, votes, edge_bits = decoded
        expected_input = expected_receipts(votes, edge_bits)
        if (row.get("truth") is not truth or row.get("receipts") != expected_input):
            errors.append("case_input_does_not_match_case_id")
            continue
        flags = (row.get("history_complete"), row.get("commitment_valid"),
                 row.get("reported_edges_match_capture"))
        expected = expected_result(truth, expected_input, flags)
        if row.get("result") != expected:
            errors.append(f"result_mismatch:{row['case_id']}")
            continue
        result_counts["incorrect_count_only"] += expected["count_only"] == "INCORRECT_QUORUM_PASS"
        result_counts["incorrect_exposure_aware"] += expected["exposure_aware"] == "INCORRECT_QUORUM_PASS"
        if (expected["count_only"] == "INCORRECT_QUORUM_PASS"
                and expected["exposure_aware"] != "INCORRECT_QUORUM_PASS"):
            result_counts["double_credit_cases"] += 1

    controls = raw.get("unknown_controls")
    required = {"incomplete_history", "invalid_commitment", "capture_mismatch"}
    if (not isinstance(controls, list)
            or {row.get("name") for row in controls if isinstance(row, dict)} != required
            or len(controls) != 3
            or any(not isinstance(row, dict)
                   or row.get("result", {}).get("exposure_aware") != "UNKNOWN_INDEPENDENCE"
                   for row in controls)):
        errors.append("unknown_controls_not_fail_closed")

    status = "PASS_T0_ENUMERATION" if not errors else (
        "FAIL_RAW_INCOMPLETE" if any(error.endswith("inventory_mismatch")
                                     or error == "unknown_controls_not_fail_closed"
                                     for error in errors)
        else "FAIL_RESULT_MISMATCH")
    return {"status": status, "errors": errors, "rows": len(rows), **result_counts}


if __name__ == "__main__":
    source = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("RAW.json")
    destination = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path("AUDIT.json")
    result = audit(json.loads(source.read_text(encoding="utf-8")))
    destination.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS_T0_ENUMERATION" else 1)
