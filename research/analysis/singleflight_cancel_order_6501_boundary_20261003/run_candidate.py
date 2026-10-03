"""New finite construction assay; never invokes retained T0b.run/main."""
import hashlib
import importlib.util
import itertools
import json
import sys
from pathlib import Path

from boundary import ordered_verdict


ROOT = Path(__file__).resolve().parent


def fixtures():
    rows = []
    for truth, cancel_a, cancel_b, order in itertools.product(
        ("TRUE", "FALSE"), (None, 4, 5, 6), (None, 4, 5, 6),
        itertools.permutations(("cancel_a", "cancel_b", "return")),
    ):
        times = {"cancel_a": cancel_a, "cancel_b": cancel_b, "return": 5}
        events = [[name, times[name], seq] for seq, name in enumerate(order) if times[name] is not None]
        rows.append({"id": len(rows), "truth": truth, "cancel_a": cancel_a, "cancel_b": cancel_b, "events": events})
    return rows


def run():
    spec = importlib.util.spec_from_file_location("retained_candidate", ROOT / "retained_candidate.py")
    retained = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(retained)
    scope = {"target_generation": 1, "valid_from_ms": 0, "valid_until_ms": 20}
    rows = []
    for fixture in fixtures():
        row = dict(fixture, outcomes={})
        for caller in ("a", "b"):
            cancel = fixture["cancel_" + caller]
            request = {"cancel_at_ms": cancel, "deadline_ms": 10, "truth": fixture["truth"]}
            row["outcomes"][caller] = {
                "retained_timestamp_lt": retained._classify(request, scope, fixture["truth"], 5),
                "conservative_timestamp_le": "CANCELLED_WAITER" if cancel is not None and cancel <= 5 else "ADMISSIBLE_" + fixture["truth"],
                "ordered": ordered_verdict(fixture["events"], caller, fixture["truth"]),
            }
        rows.append(row)
    return {"schema": "6501-cancel-order-boundary-v1", "source_sha256": hashlib.sha256((ROOT / "retained_candidate.py").read_bytes()).hexdigest(), "rows": rows}


if __name__ == "__main__":
    with Path(sys.argv[1]).open("x", encoding="utf-8", newline="\n") as output:
        json.dump(run(), output, sort_keys=True, indent=2)
        output.write("\n")
    print("candidate: 192 finite assignments, 384 waiter decisions")
