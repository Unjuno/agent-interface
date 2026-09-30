"""Independent Draft 2020-12 meta-schema and positive/negative conformance audit."""
import copy
import hashlib
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, SchemaError, ValidationError

ROOT = Path(__file__).resolve().parent
SCHEMA = ROOT / "event-schema.json"
CASES = ROOT / "trace-cases.json"
OUT = Path("/out/audit.json")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    raw = json.loads(CASES.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)

    valid_cases = []
    for case in raw["cases"]:
        envelope = {
            "schema_version": "useful-control-trace-v2",
            "trace_id": case["case_id"],
            "clock_domains": case["clock_domains"],
            "events": case["events"],
        }
        validator.validate(envelope)
        valid_cases.append(case["case_id"])

    # Each copied-schema mutation is invalid under the official Draft 2020-12 metaschema.
    mutations = [
        ("unknown-type", lambda s: s["properties"]["trace_id"].update(type="nonsense")),
        ("required-not-array", lambda s: s.update(required="events")),
        ("enum-not-array", lambda s: s["$defs"]["event"]["properties"]["event_type"].update(enum="INPUT")),
        ("minimum-not-number", lambda s: s["$defs"]["time"]["properties"]["lower_ns"].update(minimum="zero")),
        ("invalid-items-shape", lambda s: s["properties"]["events"].update(items=7)),
        ("invalid-ref-type", lambda s: s["properties"]["events"]["items"].update(**{"$ref": 12})),
        ("invalid-type-union", lambda s: s["$defs"]["time"]["properties"]["upper_ns"].update(type=["integer", "void"])),
    ]
    rejected_schema_mutations = []
    for name, mutate in mutations:
        changed = copy.deepcopy(schema)
        mutate(changed)
        try:
            Draft202012Validator.check_schema(changed)
        except SchemaError:
            rejected_schema_mutations.append(name)
        else:
            raise AssertionError("metaschema accepted invalid mutation: " + name)

    # Positive base is known-valid; each instance mutation must fail the actual schema.
    base_case = raw["cases"][0]
    base = {"schema_version": "useful-control-trace-v2", "trace_id": base_case["case_id"],
            "clock_domains": base_case["clock_domains"], "events": base_case["events"]}
    instance_mutations = [
        ("missing-required", lambda x: x.pop("events")),
        ("extra-root-field", lambda x: x.update(unregistered=True)),
        ("wrong-version", lambda x: x.update(schema_version="useful-control-trace-v3")),
        ("empty-trace-id", lambda x: x.update(trace_id="")),
        ("extra-event-field", lambda x: x["events"][0].update(unregistered=True)),
        ("bad-event-enum", lambda x: x["events"][0].update(event_type="NOT_REGISTERED")),
        ("bad-clock-unit", lambda x: x["clock_domains"][0].update(unit="ms")),
    ]
    rejected_instance_mutations = []
    for name, mutate in instance_mutations:
        changed = copy.deepcopy(base)
        mutate(changed)
        try:
            validator.validate(changed)
        except ValidationError:
            rejected_instance_mutations.append(name)
        else:
            raise AssertionError("schema accepted invalid instance mutation: " + name)

    result = {
        "schema": "o2-useful-control-trace-v2-jsonschema-draft2020-12-audit-v1",
        "disposition": "PASS_DRAFT2020_12_METASCHEMA_AND_TRACE_CONFORMANCE_SCOPED",
        "validator": {"package": "jsonschema", "version": "4.25.1",
                      "dialect": schema.get("$schema")},
        "identities": {"schema_sha256": sha(SCHEMA), "cases_sha256": sha(CASES)},
        "valid_trace_cases": valid_cases,
        "schema_mutations_rejected": rejected_schema_mutations,
        "instance_mutations_rejected": rejected_instance_mutations,
        "limits": ["JSON Schema conformance does not replace cross-event semantic/clock invariants",
                   "No cross-clock calibration, runtime, model, GUI, input, or formal allocation",
                   "Does not resolve external Worker returns or inherited leases"],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        raise SystemExit("refusing to overwrite prior audit output")
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": result["disposition"], "valid_cases": len(valid_cases),
                      "schema_mutations_rejected": len(rejected_schema_mutations),
                      "instance_mutations_rejected": len(rejected_instance_mutations)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BaseException as exc:
        print(type(exc).__name__ + ": " + str(exc), file=sys.stderr)
        raise
