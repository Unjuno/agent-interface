"""Reviewer-owned raw reference; imports no runtime, producer or author auditor."""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parent
PKG = ROOT / "head/runtime/results/lineage-json-01a0ff58"
RFIELDS = ("receipt_id", "role", "currentness", "point", "observation_seq", "binding_revision", "source_receipt_id")
SFIELDS = ("program_digest", "evidence_receipt_digest", "role", "currentness", "point", "observation_seq", "binding_revision")

def check(condition, message):
    if not condition:
        raise ValueError(message)

def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()

def hash_of(value):
    return hashlib.sha256(encoded(value)).hexdigest()

def exact(a, b):
    if type(a) is not type(b):
        return False
    if type(a) is dict:
        return a.keys() == b.keys() and all(exact(a[k], b[k]) for k in a)
    if type(a) is list:
        return len(a) == len(b) and all(exact(x, y) for x, y in zip(a, b))
    if type(a) is float:
        check(math.isfinite(a) and math.isfinite(b), "non-finite value outside frozen parsed-JSON domain")
        return struct.pack(">d", a) == struct.pack(">d", b)
    return a == b

def seal(v):
    p, r, s = (v[k] for k in ("program", "receipt", "sidecar"))
    r["digest"] = hash_of({k: r[k] for k in RFIELDS})
    s["program_digest"] = hash_of(p)
    s["evidence_receipt_digest"] = r["digest"]
    s["digest"] = hash_of({k: s[k] for k in SFIELDS})

def seed():
    return {"program": {"source": {"observation_seq": 1, "binding_revision": 1},
            "ops": [{"op": "pointer_move", "x": 1, "y": 0}]},
        "receipt": {"receipt_id": "synthetic-r1", "role": "ADMISSION_DEPENDENCY", "currentness": "CURRENT",
            "point": [1, 0], "observation_seq": 1, "binding_revision": 1, "source_receipt_id": "synthetic-s1"},
        "sidecar": {"role": "ADMISSION_DEPENDENCY", "currentness": "CURRENT", "point": [1, 0],
            "observation_seq": 1, "binding_revision": 1},
        "current": {"current_observation_seq": 1, "current_binding_revision": 1}}

def declared_cases():
    paths = [(owner, "point", axis) for owner in ("sidecar", "receipt") for axis in (0, 1)]
    # Preserve the original ordered roster: two points then two generations per owner.
    paths = [path for owner in ("sidecar", "receipt") for path in
        ((owner, "point", 0), (owner, "point", 1), (owner, "observation_seq"), (owner, "binding_revision"))]
    paths.extend([("program", "source", "observation_seq"), ("program", "source", "binding_revision"),
        ("program", "ops", 0, "x"), ("program", "ops", 0, "y"),
        ("current", "current_observation_seq"), ("current", "current_binding_revision")])
    cases = []
    for path in paths:
        base = seed()
        original = base
        for key in path:
            original = original[key]
        values = (original, float(original), bool(original), original + 1, str(original), None, [], {})
        for index, replacement in enumerate(values):
            v = seed()
            target = v
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = deepcopy(replacement)
            seal(v)
            cases.append({"id": ".".join(map(str, path)) + ":" + str(index), "input": v})
    reordered = seed()
    reordered["program"]["source"] = {"binding_revision": 1, "observation_seq": 1}
    seal(reordered)
    cases.append({"id": "reordered-control", "input": reordered})
    for owner in ("receipt", "sidecar", "program"):
        v = seed()
        seal(v)
        if owner == "program":
            v[owner]["ops"][0]["x"] = 2
        else:
            v[owner]["digest"] = "0" * 64
        cases.append({"id": "corrupt-" + owner + "-digest", "input": v})
    return cases

def first_error(v, candidate):
    p, r, s, current = (v[k] for k in ("program", "receipt", "sidecar", "current"))
    digest_gates = [(r["digest"], hash_of({k: r[k] for k in RFIELDS}), "EVIDENCE_RECEIPT_DIGEST_MISMATCH"),
        (s["digest"], hash_of({k: s[k] for k in SFIELDS}), "SIDECAR_DIGEST_MISMATCH"),
        (s["program_digest"], hash_of(p), "PROGRAM_DIGEST_MISMATCH"),
        (s["evidence_receipt_digest"], r["digest"], "EVIDENCE_DIGEST_MISMATCH")]
    for left, right, error in digest_gates:
        if left != right:
            return error
    equal = exact if candidate else lambda a, b: a == b
    for key in ("role", "currentness", "point", "observation_seq", "binding_revision"):
        if not equal(s[key], r[key]):
            return "SIDECAR_RECEIPT_MISMATCH"
    if (r["role"], r["currentness"]) != ("ADMISSION_DEPENDENCY", "CURRENT"):
        return "LINEAGE_NOT_CURRENT_ADMISSION"
    ordered = [(r["observation_seq"], current["current_observation_seq"], "STALE_OBSERVATION"),
        (r["binding_revision"], current["current_binding_revision"], "STALE_BINDING"),
        (p["source"], {k: r[k] for k in ("observation_seq", "binding_revision")}, "PROGRAM_SOURCE_MISMATCH"),
        ([p["ops"][0]["x"], p["ops"][0]["y"]], r["point"], "PROGRAM_POINT_MISMATCH")]
    return next((error for left, right, error in ordered if not equal(left, right)), None)

def inspect(raw):
    cases = declared_cases()
    retained = json.loads((PKG / "corpus.json").read_bytes())
    check(exact(cases, retained), "complete ordered frozen corpus mismatch")
    frozen = json.loads((PKG / "freeze.json").read_bytes())
    check(raw["schema"] == "lineage-json-matrix-v1", "raw schema")
    check(raw["freeze_sha256"] == hashlib.sha256((PKG / "freeze.json").read_bytes()).hexdigest(), "freeze identity")
    check(type(raw["backend_calls"]) is int and raw["backend_calls"] == 0, "backend count")
    check(type(raw["rows"]) is list and len(raw["rows"]) == 232, "row count")
    check(frozen["case_count"] == 116 and type(frozen["case_count"]) is int, "frozen count")
    mismatches = {"baseline": [], "candidate": []}
    source_specific = {"baseline": 0, "candidate": 0}
    dispatches = {"baseline": 0, "candidate": 0}
    index = 0
    for arm in ("baseline", "candidate"):
        for item in cases:
            row = raw["rows"][index]
            index += 1
            check((row["arm"], row["id"]) == (arm, item["id"]), "ordered arm/case coverage")
            check(row["input_sha256"] == hash_of(item["input"]), "input bytes")
            check(row["input_unchanged"] is True, "input mutation")
            error = first_error(item["input"], arm == "candidate")
            wanted = {"status": "lineage_rejected" if error else "delegated", "error": error}
            check(exact(row["observed"], wanted), "source-specific result: " + arm + "/" + item["id"])
            check(type(row["dispatch_calls"]) is int and row["dispatch_calls"] == (0 if error else 1), "dispatch count")
            dispatches[arm] += row["dispatch_calls"]
            source_specific[arm] += 1
            intended = first_error(item["input"], True)
            if error != intended:
                mismatches[arm].append(item["id"])
    check(len(mismatches["baseline"]) == 28 and mismatches["candidate"] == [], "semantic totals")
    return {"ordered_rows": index, "source_specific_matches": source_specific,
        "semantic_mismatch_counts": {k: len(v) for k, v in mismatches.items()}, "dispatches": dispatches}

if __name__ == "__main__":
    raw = json.loads((PKG / "raw.json").read_bytes())
    result = inspect(raw)
    controls = []
    for name in ("missing", "duplicate", "input-hash", "dispatch-bool", "input-mutation", "wrong-verdict", "dispatch-float", "backend-bool"):
        v = deepcopy(raw)
        if name == "missing": v["rows"].pop()
        elif name == "duplicate": v["rows"][1] = deepcopy(v["rows"][0])
        elif name == "input-hash": v["rows"][0]["input_sha256"] = "0" * 64
        elif name == "dispatch-bool": v["rows"][0]["dispatch_calls"] = True
        elif name == "input-mutation": v["rows"][0]["input_unchanged"] = False
        elif name == "wrong-verdict": v["rows"][-1]["observed"] = {"status": "delegated", "error": None}
        elif name == "dispatch-float": v["rows"][0]["dispatch_calls"] = 1.0
        else: v["backend_calls"] = False
        try:
            inspect(v)
        except ValueError as error:
            controls.append({"control": name, "rejected": True, "reason": str(error), "copy_sha256": hash_of(v)})
        else:
            raise ValueError("ineffective reference control: " + name)
    result.update(raw_sha256=hashlib.sha256((PKG / "raw.json").read_bytes()).hexdigest(), controls=controls,
        reference_scope="Finite canonical parsed JSON; float identity uses IEEE bits including signed zero. No runtime/producer/author-oracle import or execution.")
    (ROOT / "reference-result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
