"""Saved-row-only auditor for Fake X release-order A01."""
import argparse
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
EXPECTED = {"healthy", "same_connection_sync_block", "separate_up_before_send",
            "separate_up_before_sync", "server_wide_stop"}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def audit_record(record):
    require(record["schema"] == "fake-x-release-order-a01-v1", "schema mismatch")
    require({row["case"] for row in record["rows"]} == EXPECTED,
            "case set mismatch")
    by_name = {row["case"]: row for row in record["rows"]}

    healthy = by_name["healthy"]
    require(healthy["final_down"] == [], "healthy case left a key down")
    require(healthy["final_ledger"] == {}, "healthy case left ledger state")
    require(healthy["release"]["verified"] is True,
            "healthy release was not verified")

    same = by_name["same_connection_sync_block"]
    require(same["before_resume"]["writer_alive"] is True,
            "same-connection writer returned before resume")
    require(same["before_resume"]["release_alive"] is True,
            "same-connection release returned before resume")
    require(same["before_resume"]["release_returned"] is False,
            "same-connection release receipt returned before resume")
    require(same["final_down"] == [], "same-connection cleanup left a key down")
    same_apply = [event["kind"] for event in same["server_events"]
                  if event["phase"] == "apply"]
    require(same_apply == [2, 3], f"same-connection apply order was {same_apply}")

    for name in ("separate_up_before_send", "separate_up_before_sync"):
        row = by_name[name]
        require(row["before_resume"]["release_returned"] is True,
                f"{name}: separate release did not return")
        require(row["before_resume"]["release"]["verified"] is True,
                f"{name}: separate release was not reported verified")
        require(row["before_resume"]["server_down"] == [],
                f"{name}: server was not empty before writer resumed")
        require(row["final_down"] == [37],
                f"{name}: pending writer did not leave the key down")
        require(row["final_ledger"] == {}, f"{name}: expected false-clear ledger")
        applied = [(event["connection"], event["kind"])
                   for event in row["server_events"] if event["phase"] == "apply"]
        require(applied[-2:] == [("control", 3), ("writer", 2)],
                f"{name}: unexpected apply order {applied}")

    stopped = by_name["server_wide_stop"]
    require(stopped["before_resume"]["release_returned"] is False,
            "server-wide stop returned an early release receipt")
    require(stopped["before_resume"]["release_alive"] is True,
            "server-wide stop did not block release")
    require(stopped["before_resume"]["server_down"] == [37],
            "server-wide stop lost the held key before resume")
    require(stopped["final_down"] == [], "server-wide stop cleanup failed after resume")
    require(stopped["writer_outcomes"][-1]["verified"] is True,
            "server-wide stop did not return verified cleanup after resume")
    return {"decision": "COUNTEREXAMPLE_SEPARATE_UP_FALSE_CLEAR",
            "cases": len(EXPECTED), "false_clear_cases": 2,
            "same_connection_waited_for_resume": True,
            "server_wide_stop_produced_no_early_receipt": True,
            "scope": "synthetic Fake X interleaving only"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("raw", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("refuse to overwrite an existing audit")
    record = json.loads(args.raw.read_text(encoding="utf-8"))
    decision = audit_record(record)
    result = {"raw_sha256": hashlib.sha256(args.raw.read_bytes()).hexdigest(),
              "source_freeze_sha256": hashlib.sha256((HERE / "SOURCE_FREEZE.json").read_bytes()).hexdigest(),
              "audit": decision}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
