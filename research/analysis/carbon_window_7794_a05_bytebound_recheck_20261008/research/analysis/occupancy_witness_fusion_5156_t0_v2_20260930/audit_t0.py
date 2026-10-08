"""Independent raw-only audit using explicit hidden-time enumeration."""

import json
import sys
from pathlib import Path


FIELDS = ("owner_id", "actuation_id", "keycode", "display_id", "clock_id")


def ints_between(interval):
    if not isinstance(interval, list) or len(interval) != 2:
        return []
    if any(type(x) is not int for x in interval) or interval[0] > interval[1]:
        return []
    return list(range(interval[0], interval[1] + 1))


def oracle(record):
    if not isinstance(record, dict):
        return None
    down, up, release = (record.get("down_query"), record.get("up_query"), record.get("owner_release"))
    identity = record.get("identity")
    if not all(isinstance(x, dict) for x in (down, up, release, identity)):
        return None
    if (
        not isinstance(identity.get("owner_id"), str)
        or not identity["owner_id"]
        or not isinstance(identity.get("actuation_id"), str)
        or not identity["actuation_id"]
        or type(identity.get("keycode")) is not int
        or not isinstance(identity.get("display_id"), str)
        or not identity["display_id"]
        or not isinstance(identity.get("clock_id"), str)
        or not identity["clock_id"]
    ):
        return None
    if any(
        not isinstance(source.get("owner_id"), str)
        or not source["owner_id"]
        or not isinstance(source.get("actuation_id"), str)
        or not source["actuation_id"]
        or type(source.get("keycode")) is not int
        or not isinstance(source.get("display_id"), str)
        or not source["display_id"]
        or not isinstance(source.get("clock_id"), str)
        or not source["clock_id"]
        or any(source.get(k) != identity[k] for k in FIELDS)
        for source in (down, up, release)
    ):
        return None
    d_times, u_times = ints_between(down.get("query")), ints_between(up.get("query"))
    if not d_times or not u_times:
        return None
    start, returned, sync = (release.get("request_start"), release.get("request_return"), release.get("sync_return"))
    if any(type(x) is not int for x in (start, returned, sync)) or not start <= returned <= sync:
        return None
    if type(release.get("release_count")) is not int or release["release_count"] != 1:
        return None
    if type(release.get("repress_count")) is not int or release["repress_count"] != 0:
        return None
    possible = set()
    for down_snapshot in d_times:
        for release_time in range(min(d_times + u_times + [start, sync]), max(d_times + u_times + [start, sync]) + 1):
            for up_snapshot in u_times:
                if down_snapshot < release_time <= up_snapshot and start < release_time <= sync:
                    possible.add(release_time)
    return possible


def main(path):
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    errors = []
    checks = 0
    strictly_narrower_than_both = 0
    seen_ids = set()
    for row in raw.get("rows", []):
        checks += 1
        case_id = row.get("case_id")
        if not isinstance(case_id, str) or case_id in seen_ids:
            errors.append({"case_id": case_id, "error": "missing or duplicate case id"})
        seen_ids.add(case_id)
        possible = oracle(row.get("record"))
        result = row.get("candidate", {})
        if result.get("authority") is not False:
            errors.append({"case_id": case_id, "error": "authority was not false"})
        if possible is None:
            if result.get("decision") != "UNKNOWN":
                errors.append({"case_id": row.get("case_id"), "error": "invalid evidence emitted a bound"})
        elif not possible:
            if result.get("decision") != "UNKNOWN":
                errors.append({"case_id": row.get("case_id"), "error": "empty feasible set emitted a bound"})
        else:
            lo, hi = result.get("lower_open"), result.get("upper_closed")
            represented = set(range(lo + 1, hi + 1)) if result.get("decision") == "BOUNDED" and type(lo) is int and type(hi) is int else set()
            if result.get("decision") != "BOUNDED" or represented != possible:
                errors.append({"case_id": row.get("case_id"), "error": "candidate interval differs from hidden-time oracle", "possible": sorted(possible), "represented": sorted(represented)})
            record_data = row["record"]
            query_width = record_data["up_query"]["query"][1] - record_data["down_query"]["query"][0]
            owner_width = record_data["owner_release"]["sync_return"] - record_data["owner_release"]["request_start"]
            fused_width = hi - lo
            if fused_width < query_width and fused_width < owner_width:
                strictly_narrower_than_both += 1
    expected_total = raw.get("valid_case_count", -1) + raw.get("corruption_case_count", -1)
    if len(raw.get("rows", [])) != expected_total:
        errors.append({"error": "row denominator mismatch"})
    if raw.get("valid_case_count") != 7875 or raw.get("corruption_case_count") != 14 or checks != 7889:
        errors.append({"error": "frozen finite-domain denominator mismatch"})
    if strictly_narrower_than_both < 1:
        errors.append({"error": "no case strictly narrowed by both evidence sources"})
    print(json.dumps({"decision": "PASS_INTERVAL_FUSION_CONSTRUCTION_ONLY" if not errors else "FAIL_INTERVAL_FUSION_AUDIT", "checks": checks, "strictly_narrower_than_both": strictly_narrower_than_both, "errors": errors}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python audit_t0.py path/to/raw.json")
    raise SystemExit(main(sys.argv[1]))
