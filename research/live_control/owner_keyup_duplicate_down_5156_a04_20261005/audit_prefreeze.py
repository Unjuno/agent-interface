"""Raw-only auditor for repeated DOWN while a key is already held."""
import copy
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULT = Path(sys.argv[1])
freeze = json.loads((HERE / "FREEZE_PREFREEZE.json").read_text(encoding="utf-8"))
raw = json.loads(RESULT.read_text(encoding="utf-8"))
errors = []


def sha(path):
    return hashlib.sha256((HERE / path).read_bytes()).hexdigest()


for path, expected in freeze["sha256"].items():
    if sha(path) != expected:
        errors.append("frozen source mismatch: " + path)


def inspect(doc):
    bad = []
    if doc.get("schema") != "owner-keyup-duplicate-down-result-v1":
        bad.append("result schema")
    if doc.get("runner_error") is not None:
        bad.append("runner error")
    cases = doc.get("cases")
    if not isinstance(cases, list) or len(cases) != 1:
        return bad + ["case count"]
    case = cases[0]
    if (case.get("name"), case.get("identifier"), case.get("step")) != (
        "duplicate_down", "trial-duplicate-down", 13
    ):
        bad.append("case context")
    owner_id = case.get("owner_id")
    token = case.get("intent_token")
    if not isinstance(owner_id, str) or not owner_id or token != "token-duplicate-down":
        bad.append("owner/token identity")
    if case.get("final_down") != []:
        bad.append("fake keymap not neutral")
    owner_records = case.get("owner_records", [])
    if not any(
        row.get("event") == "owner_release" and row.get("verified") is True
        and row.get("keys_down") == [] and row.get("buttons_down") == []
        for row in owner_records
    ):
        bad.append("verified neutral owner cleanup absent")

    events = case.get("events", [])
    admissions = [row for row in events if row.get("event") == "input_admission"]
    releases = [row for row in events if row.get("event") == "input_release_transition"]
    owner_rows = [row for row in owner_records if row.get("event") == "owner_keyup"]
    if (len(admissions), len(releases), len(owner_rows)) != (2, 1, 1):
        bad.append("expected two admissions but one release/owner receipt")
    admission_ids = []
    for sequence, row in enumerate(admissions, start=1):
        expected_id = owner_id + ":admission:" + str(sequence) if isinstance(owner_id, str) else None
        if (row.get("key"), row.get("admission_sequence"), row.get("owner_id"), row.get("admission_id")) != (
            "A", sequence, owner_id, expected_id
        ):
            bad.append("admission key/sequence/id")
        if (row.get("id"), row.get("step"), row.get("intent_token")) != (
            "trial-duplicate-down", 13, token
        ):
            bad.append("admission context")
        admission_ids.append(row.get("admission_id"))
    if len(admission_ids) != 2 or admission_ids[0] == admission_ids[1]:
        bad.append("two admissions did not receive distinct IDs")

    if releases:
        row = releases[0]
        nested = row.get("owner_keyup_receipt")
        if not isinstance(nested, dict):
            bad.append("nested owner receipt absent")
        else:
            latest_id = admission_ids[-1] if admission_ids else None
            if row.get("admission_identity_status") != "ambiguous_multiple_admissions":
                bad.append("ambiguous admission inventory not reported")
            if row.get("owner_keyup_join") != "MATCHED_EXPLICIT_KEYUP":
                bad.append("owner KeyRelease receipt not joined")
            if row.get("admission_id") != latest_id or nested.get("admission_id") != latest_id:
                bad.append("release did not retain the latest held-key ID")
            if (row.get("key"), nested.get("key"), nested.get("reason")) != (
                "A", "A", "explicit_up"
            ):
                bad.append("release key/reason")
            if (row.get("owner_id"), nested.get("owner_id"), row.get("intent_token"), nested.get("intent_token")) != (
                owner_id, owner_id, token, token
            ):
                bad.append("release owner/token identity")
            if (row.get("release_batch_identifier"), row.get("release_batch_step")) != (
                "trial-duplicate-down", 13
            ):
                bad.append("release context")
            if (row.get("release_batch_size"), row.get("release_batch_position")) != (1, 0):
                bad.append("release batch cardinality/position")
            if row.get("physical_verification_authoritative") is not False or row.get("grants_input_authority") is not False:
                bad.append("release authority overclaim")
            if nested.get("physical_verification_authoritative") is not False or nested.get("grants_input_authority") is not False:
                bad.append("owner receipt authority overclaim")
            owner_receipt_ids = {item.get("receipt_id") for item in owner_rows}
            if nested.get("receipt_id") not in owner_receipt_ids:
                bad.append("nested receipt absent from owner history")
            a, b = nested.get("owner_keyup_started_ns"), nested.get("owner_sync_returned_ns")
            c, d = row.get("release_call_started_ns"), row.get("release_call_returned_ns")
            if not (
                nested.get("xsync_completed") is True
                and type(a) is int and type(b) is int and type(c) is int and type(d) is int
                and c <= a <= b <= d
            ):
                bad.append("caller/owner interval nesting")
            if row.get("owner_transition_verified") is not True:
                bad.append("owner batch outcome")

    wanted = [
        ["input", 2, 38], ["sync", 1],
        ["input", 2, 38], ["sync", 2],
        ["input", 3, 38], ["sync", 3],
        ["sync", 4],
    ]
    if case.get("calls") != wanted:
        bad.append("XTest/XSync call sequence")
    return bad


base_errors = inspect(raw)
errors.extend(base_errors)
mutations = []


def add(label, mutate):
    doc = copy.deepcopy(raw)
    mutate(doc)
    mutations.append((label, doc))


if raw.get("cases"):
    add("missing first admission", lambda d: d["cases"][0]["events"].pop(0))
    add("duplicate admission IDs", lambda d: d["cases"][0]["events"][1].update(admission_id=d["cases"][0]["events"][0]["admission_id"]))
    add("false exact-match status", lambda d: next(r for r in d["cases"][0]["events"] if r.get("event") == "input_release_transition").update(admission_identity_status="matched_explicit_id"))
    add("wrong release ID", lambda d: next(r for r in d["cases"][0]["events"] if r.get("event") == "input_release_transition").update(admission_id="wrong"))
    add("authority overclaim", lambda d: next(r for r in d["cases"][0]["events"] if r.get("event") == "input_release_transition").update(grants_input_authority=True))
    add("missing second KeyPress", lambda d: d["cases"][0]["calls"].pop(2))

rejected = [label for label, doc in mutations if inspect(doc)]
missed = [label for label, doc in mutations if not inspect(doc)]
if len(mutations) != 6 or missed:
    errors.append("mutation controls did not all reject: " + repr(missed))

scientific = (
    "FAIL_DUPLICATE_DOWN_RELEASE_IDENTITY_AMBIGUOUS"
    if not base_errors and raw.get("runner_error") is None
    else "UNRESOLVED_RAW_OR_RUNNER_MISMATCH"
)
report = {
    "schema": "owner-keyup-duplicate-down-audit-v1",
    "result_sha256": hashlib.sha256(RESULT.read_bytes()).hexdigest(),
    "audit_status": "PASS_AUDIT_SCOPED" if not errors else "FAIL_AUDIT",
    "scientific_outcome": scientific,
    "base_error_count": len(base_errors),
    "mutation_count": len(mutations),
    "mutation_rejections": len(rejected),
    "rejected_controls": rejected,
    "missed_controls": missed,
    "errors": errors,
    "decision": "RETAINED_FAIL" if scientific.startswith("FAIL_") and not errors else "STOP",
}
(RESULT.parent / "AUDIT.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, sort_keys=True))
raise SystemExit(0 if not errors and scientific.startswith("FAIL_") else 1)
