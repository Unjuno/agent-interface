"""Independent finite-trace oracle; does not import candidate or Lease."""
import copy
import json
import sys
from pathlib import Path


ARMS = ("current_perf_lease", "boottime_deadline", "wake_fence")


def expected(s: dict, ttl: int) -> list[dict]:
    mono = s["mono_elapsed_ns"]
    boot = s["boottime_elapsed_ns"]
    complete = s["clock_coverage"] == "complete"
    perf = "UNKNOWN_CLOCK" if mono is None or not complete else ("LIVE" if mono < ttl else "EXPIRED")
    boottime = "UNKNOWN_CLOCK" if boot is None or not complete else ("LIVE" if boot < ttl else "EXPIRED")
    if not complete or s["wake_notice"] in ("missing", "late_after_first_admission"):
        fence = {"outcome":"UNKNOWN_WAKE_COVERAGE","release_requested":bool(s["held_input"]),
                 "release_ack_observed":False,"old_generation_admitted":False,
                 "fresh_lease_created":False,"first_action":"SUPPRESS_UNKNOWN_WAKE",
                 "new_lease_outcome":"NOT_CREATED"}
    elif s["wake_notice"] == "on_time":
        if s["held_input"] and not s["release_ack"]:
            status = "SUPPRESS_PENDING_RELEASE"
        elif not s["fresh_rebind"]:
            status = "BLOCK_STALE_GENERATION"
        else:
            status = "ADMIT_FRESH_LEASE"
        admitted_new = status == "ADMIT_FRESH_LEASE"
        fence = {"outcome":status,"release_requested":bool(s["held_input"]),
                 "release_ack_observed":bool(s["held_input"] and s["release_ack"]),
                 "old_generation_admitted":False,"fresh_lease_created":admitted_new,
                 "first_action":"ADMIT_NEW_AUTHORITY" if admitted_new else "SUPPRESS",
                 "new_lease_outcome":"LIVE" if admitted_new and mono is not None else
                    "UNKNOWN_CLOCK" if admitted_new else "NOT_CREATED"}
    else:
        fence = {"outcome":"ADMIT_CURRENT_GENERATION" if perf == "LIVE" else perf,
                 "release_requested":False,"release_ack_observed":False,
                 "old_generation_admitted":perf == "LIVE","fresh_lease_created":False,
                 "first_action":"ADMIT_OLD_AUTHORITY" if perf == "LIVE" else "SUPPRESS",
                 "new_lease_outcome":"NOT_CREATED"}
    rows = []
    rows.append({"scenario":s["id"],"arm":ARMS[0],"outcome":perf,
                 "release_requested":False,"release_ack_observed":False,
                 "old_generation_admitted":perf == "LIVE","fresh_lease_created":False,
                 "first_action":"ADMIT_OLD_AUTHORITY" if perf == "LIVE" else "SUPPRESS",
                 "new_lease_outcome":"NOT_CREATED"})
    rows.append({"scenario":s["id"],"arm":ARMS[1],"outcome":boottime,
                 "release_requested":False,"release_ack_observed":False,
                 "old_generation_admitted":boottime == "LIVE","fresh_lease_created":False,
                 "first_action":"ADMIT_OLD_AUTHORITY" if boottime == "LIVE" else "SUPPRESS",
                 "new_lease_outcome":"NOT_CREATED"})
    rows.append({"scenario":s["id"],"arm":ARMS[2],**fence})
    return rows


def audit(fixture: dict, raw: dict) -> dict:
    expected_rows = [row for s in fixture["scenarios"] for row in expected(s, fixture["ttl_ns"])]
    got = raw.get("rows", [])
    identities = [(r.get("scenario"), r.get("arm")) for r in got]
    required = [(r["scenario"], r["arm"]) for r in expected_rows]
    integrity = len(got) == len(required) and identities == required
    row_checks = []
    expmap = {(r["scenario"],r["arm"]):r for r in expected_rows}
    gotmap = {(r.get("scenario"),r.get("arm")):r for r in got}
    for key in required:
        row_checks.append({"scenario":key[0],"arm":key[1],
                           "matches_oracle":gotmap.get(key) == expmap[key]})
    mutation_checks = []
    for m in fixture["mutations"]:
        altered = copy.deepcopy(raw)
        for row in altered.get("rows", []):
            if row.get("scenario") == m["scenario"] and row.get("arm") == m["arm"]:
                row[m["field"]] = m["value"]
        matches = altered.get("rows", []) == expected_rows
        mutation_checks.append({"id":m["id"],"rejected":not matches})
    passed = integrity and all(r["matches_oracle"] for r in row_checks) and all(m["rejected"] for m in mutation_checks)
    return {"status":"PASS_METHOD_SCOPED" if passed else "HOLD_AUDIT",
            "rows_expected":len(required),"rows_observed":len(got),"identity_order_exact":integrity,
            "row_checks":row_checks,"mutation_controls":mutation_checks,
            "interpretation":{"long_wake_current_perf":gotmap.get(("long_wake",ARMS[0]),{}).get("outcome"),
                "long_wake_boottime":gotmap.get(("long_wake",ARMS[1]),{}).get("outcome"),
                "missed_notice_fence":gotmap.get(("missed_notice_held",ARMS[2]),{}).get("outcome"),
                "held_release_claim":"request_only_until_ack"}}


def main() -> int:
    fixture= json.loads(Path(sys.argv[1]).read_text())
    raw=json.loads(Path(sys.argv[2]).read_text())
    Path(sys.argv[3]).write_text(json.dumps(audit(fixture,raw),sort_keys=True,separators=(",",":"))+"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
