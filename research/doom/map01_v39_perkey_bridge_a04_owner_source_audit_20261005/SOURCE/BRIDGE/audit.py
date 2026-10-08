from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "results/a03"


def main() -> int:
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    raw_bytes = (OUT / "RAW.json").read_bytes()
    raw = json.loads(raw_bytes)
    result = json.loads((OUT / "RESULT.json").read_text(encoding="utf-8"))
    rows = raw["events"]
    downs = [r for r in rows if r.get("event") == "input_admission"]
    ups = [r for r in rows if r.get("event") == "input_release_measurement"]
    errors = []
    if raw.get("run_id") != freeze["run_id"] or result.get("run_id") != freeze["run_id"]:
        errors.append("run_id")
    if hashlib.sha256(raw_bytes).hexdigest() != result.get("raw_sha256"):
        errors.append("raw_digest")
    if len(downs) != 1 or len(ups) != 1:
        errors.append("event_cardinality")
    else:
        down, up = downs[0], ups[0]
        dm = down.get("physical_key_measurement", {})
        um = up.get("physical_key_measurement", {})
        aid = dm.get("actuation_id")
        edge = um.get("adapter_edge") or {}
        interval = edge.get("interval")
        if (down.get("id"), down.get("step"), up.get("id"), up.get("step")) != (freeze["run_id"], 3, freeze["run_id"], 3):
            errors.append("context")
        if not aid or um.get("actuation_id") != aid:
            errors.append("actuation_identity")
        if um.get("classification") != "CONFIRMED_PHYSICAL_UP":
            errors.append("classification")
        if (edge.get("edge") != "up" or edge.get("status") != "CONFIRMED_PHYSICAL_UP"
                or edge.get("actuation_id") != aid or edge.get("key") != "F8"
                or type(interval) is not list or len(interval) != 2
                or any(type(v) is not int for v in interval) or interval[0] > interval[1]):
            errors.append("adapter_edge")
        if up.get("owner_cleanup_record", {}).get("verified") is not True:
            errors.append("cleanup_source")
        if edge.get("grants_input_authority") is not False or up.get("grants_input_authority") is not False:
            errors.append("authority_boundary")
        if up.get("application_consumption_observed") is not False:
            errors.append("effect_boundary")
    if raw.get("fake_physical_keys") != []:
        errors.append("fake_display_not_neutral")
    consumer_path = HERE.parents[0] / "map01_v39_perkey_measurement_consumer_a03_20261005/audit.py"
    spec = importlib.util.spec_from_file_location("v39_consumer_a03_auditor", consumer_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        consumer_result = module.independently_reconstruct(rows)
    except Exception as exc:
        consumer_result = None
        errors.append("strict_consumer:" + type(exc).__name__)
    audit = {"schema": "map01-v39-perkey-bridge-a02-audit-v1",
             "run_id": freeze["run_id"], "status": "PASS" if not errors else "FAIL",
             "errors": errors, "event_count": len(rows),
             "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
             "strict_consumer_result": consumer_result,
             "scope": freeze["scope"]}
    (OUT / "AUDIT.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n",
                                     encoding="utf-8")
    print(json.dumps(audit, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
