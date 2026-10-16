"""Independent raw-result audit for frozen A03; never executes candidate code."""
import copy, hashlib, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULT = Path(sys.argv[1])
freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
raw = json.loads(RESULT.read_text(encoding="utf-8"))
errors = []

def sha(path):
    return hashlib.sha256((HERE / path).read_bytes()).hexdigest()

for path, expected in freeze["sha256"].items():
    if sha(path) != expected:
        errors.append("frozen hash mismatch: " + path)

specs = {
    "single": {"identifier": "trial-single", "step": 3,
               "admissions": [("A", 1)], "releases": [("A", 1)],
               "ops": [("down", "A"), ("up", "A")]},
    "reverse": {"identifier": "trial-reverse", "step": 7,
                "admissions": [("A", 1), ("B", 2)],
                "releases": [("B", 2), ("A", 1)],
                "ops": [("down", "A"), ("down", "B"),
                        ("up", "B"), ("up", "A")]},
    "cycles": {"identifier": "trial-cycles", "step": 11,
               "admissions": [("C", 1), ("C", 2)],
               "releases": [("C", 1), ("C", 2)],
               "ops": [("down", "C"), ("up", "C"),
                       ("down", "C"), ("up", "C")]},
}
codes = {"A": 38, "B": 56, "C": 54}


def inspect(doc):
    bad = []
    cases = doc.get("cases")
    if not isinstance(cases, list) or [c.get("name") for c in cases] != ["single", "reverse", "cycles"]:
        return ["case set/order"]
    if doc.get("schema") != "owner-keyup-admission-id-result-v1" or doc.get("runner_error") is not None:
        bad.append("result schema/runner error")
    for case in cases:
        name = case.get("name")
        s = specs[name]
        ident, step = s["identifier"], s["step"]
        owner_id, token = case.get("owner_id"), case.get("intent_token")
        if (case.get("identifier"), case.get("step")) != (ident, step):
            bad.append(name + ": case context")
        if not isinstance(owner_id, str) or not owner_id or not isinstance(token, str) or not token:
            bad.append(name + ": owner/token absent")
        if case.get("final_down") != []:
            bad.append(name + ": final fake keymap not neutral")
        owner_records = case.get("owner_records", [])
        if not any(r.get("event") == "owner_release" and r.get("verified") is True
                   and r.get("keys_down") == [] and r.get("buttons_down") == []
                   for r in owner_records):
            bad.append(name + ": verified neutral owner cleanup missing")
        admissions = [r for r in case.get("events", []) if r.get("event") == "input_admission"]
        releases = [r for r in case.get("events", []) if r.get("event") == "input_release_transition"]
        owner_rows = [r for r in owner_records if r.get("event") == "owner_keyup"]
        if (len(admissions), len(releases), len(owner_rows)) != (len(s["admissions"]), len(s["releases"]), len(s["releases"])):
            bad.append(name + ": admission/release/owner receipt cardinality")
        by_id = {}
        for pos, row in enumerate(admissions):
            key, seq = s["admissions"][pos]
            expected_id = owner_id + ":admission:" + str(seq) if isinstance(owner_id, str) else None
            actual_id = row.get("admission_id")
            if (row.get("key"), row.get("admission_sequence"), row.get("owner_id"), row.get("admission_id")) != (key, seq, owner_id, expected_id):
                bad.append(name + ": owner-issued admission identity/sequence")
            if not isinstance(actual_id, str) or actual_id in by_id:
                bad.append(name + ": missing or duplicate admission ID")
            else:
                by_id[actual_id] = row
            if (row.get("id"), row.get("step"), row.get("intent_token")) != (ident, step, token):
                bad.append(name + ": admission context")
        actual_release_order = [(r.get("key"), r.get("admission_sequence")) for r in releases]
        if actual_release_order != s["releases"]:
            bad.append(name + ": release order/sequence")
        owner_by_receipt = {r.get("receipt_id"): r for r in owner_rows}
        for pos, row in enumerate(releases):
            key, seq = s["releases"][pos]
            admission = next((a for a in admissions if a.get("key") == key and a.get("admission_sequence") == seq), None)
            nested = row.get("owner_keyup_receipt")
            if not isinstance(admission, dict) or not isinstance(nested, dict):
                bad.append(name + ": admission or nested receipt missing")
                continue
            admission_id = admission.get("admission_id")
            if (row.get("admission_id"), nested.get("admission_id"), admission_id) != (admission_id,) * 3:
                bad.append(name + ": admission ID differs across three surfaces")
            if row.get("admission_identity_status") != "matched_explicit_id":
                bad.append(name + ": explicit identity not matched")
            if (row.get("key"), nested.get("key"), nested.get("keycode"), nested.get("reason")) != (key, key, codes[key], "explicit_up"):
                bad.append(name + ": release key/owner receipt mismatch")
            if (row.get("owner_id"), nested.get("owner_id"), row.get("intent_token"), nested.get("intent_token")) != (owner_id, owner_id, token, token):
                bad.append(name + ": release owner/lease identity mismatch")
            if (row.get("id"), row.get("step"), row.get("release_batch_identifier"), row.get("release_batch_step")) != (ident, step, ident, step):
                bad.append(name + ": release context mismatch")
            receipt = owner_by_receipt.get(nested.get("receipt_id"))
            if receipt is not nested and (not isinstance(receipt, dict) or receipt != nested):
                bad.append(name + ": nested receipt not present in owner history")
            start, finish = nested.get("owner_keyup_started_ns"), nested.get("owner_sync_returned_ns")
            cstart, cfinish = row.get("release_call_started_ns"), row.get("release_call_returned_ns")
            if (nested.get("xsync_completed") is not True or type(start) is not int or type(finish) is not int
                    or type(cstart) is not int or type(cfinish) is not int
                    or not cstart <= start <= finish <= cfinish):
                bad.append(name + ": caller/owner interval nesting invalid")
            if row.get("owner_transition_verified") is not True:
                bad.append(name + ": existing owner batch outcome changed")
            if row.get("physical_verification_authoritative") is not False or row.get("grants_input_authority") is not False:
                bad.append(name + ": release authority overclaim")
            if nested.get("physical_verification_authoritative") is not False or nested.get("grants_input_authority") is not False:
                bad.append(name + ": owner authority overclaim")
        wanted = []
        sync_n = 0
        for operation, key in s["ops"]:
            wanted.append(["input", 2 if operation == "down" else 3, codes[key]])
            sync_n += 1
            wanted.append(["sync", sync_n])
        sync_n += 1  # close() performs one empty cleanup sync
        wanted.append(["sync", sync_n])
        if case.get("calls") != wanted:
            bad.append(name + ": XTest/XSync operation order changed")
    return bad

base_errors = inspect(raw)
errors.extend(base_errors)
mutations = []
def add(label, mutate):
    doc = copy.deepcopy(raw)
    mutate(doc)
    mutations.append((label, doc))

if raw.get("cases"):
    add("missing admission id", lambda d: d["cases"][0]["events"][0].pop("admission_id", None))
    add("blank admission id", lambda d: d["cases"][0]["events"][0].update(admission_id=""))
    add("duplicate admission id", lambda d: d["cases"][1]["events"][1].update(admission_id=d["cases"][1]["events"][0]["admission_id"]))
    add("wrong admission sequence", lambda d: next(r for r in d["cases"][2]["events"] if r.get("event")=="input_admission" and r.get("admission_sequence")==2).update(admission_sequence=99))
    add("wrong explicit release id", lambda d: next(r for r in d["cases"][0]["events"] if r.get("event")=="input_release_transition").update(admission_id="wrong"))
    add("wrong nested receipt id", lambda d: next(r for r in d["cases"][0]["events"] if r.get("event")=="input_release_transition")["owner_keyup_receipt"].update(admission_id="wrong"))
    add("swapped release ids", lambda d: (next(r for r in d["cases"][1]["events"] if r.get("event")=="input_release_transition").update(admission_id=d["cases"][1]["events"][0].get("admission_id"))))
    add("wrong owner id", lambda d: d["cases"][0].update(owner_id="other-owner"))
    add("wrong release key", lambda d: next(r for r in d["cases"][0]["events"] if r.get("event")=="input_release_transition").update(key="B"))
    add("wrong step context", lambda d: next(r for r in d["cases"][0]["events"] if r.get("event")=="input_release_transition").update(step=999))
    add("authority overclaim", lambda d: next(r for r in d["cases"][0]["events"] if r.get("event")=="input_release_transition").update(physical_verification_authoritative=True))
    add("missing owner receipt", lambda d: next(r for r in d["cases"][0]["events"] if r.get("event")=="input_release_transition").update(owner_keyup_receipt=None))

rejected = [label for label, doc in mutations if inspect(doc)]
missed = [label for label, doc in mutations if not inspect(doc)]
if len(mutations) != 12 or missed:
    errors.append("mutation controls: expected 12 rejections; missed=" + repr(missed))
report = {
    "schema": "owner-keyup-admission-id-audit-v1",
    "result_sha256": hashlib.sha256(RESULT.read_bytes()).hexdigest(),
    "base_error_count": len(base_errors),
    "mutation_count": len(mutations),
    "mutation_rejections": len(rejected),
    "rejected_controls": rejected,
    "missed_controls": missed,
    "errors": errors,
    "decision": "PASS_OWNER_ADMISSION_ID_SCOPED" if not errors else "FAIL",
}
(RESULT.parent / "AUDIT.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, sort_keys=True))
raise SystemExit(0 if not errors else 1)
