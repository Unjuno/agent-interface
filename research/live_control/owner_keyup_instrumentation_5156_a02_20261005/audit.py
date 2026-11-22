"""Independent raw JSON/source-hash auditor; imports no candidate code."""
import copy, hashlib, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULT = Path(sys.argv[1])
FREEZE = json.loads((HERE / "FREEZE.json").read_text())
raw = json.loads(RESULT.read_text())
errors = []
def check(condition, message):
    if not condition: errors.append(message)
def sha(path): return hashlib.sha256((HERE / path).read_bytes()).hexdigest()
for rel, expected in FREEZE["sha256"].items(): check(sha(rel) == expected, "hash mismatch: " + rel)
check(raw.get("runner_error") is None, "runner reported error")
cases = raw.get("cases")
expected_names = ["single", "ordered_two", "bulk", "cancel", "sync_error"]
check(isinstance(cases, list) and [c.get("name") for c in cases] == expected_names, "case set/order mismatch")
mutation_rejections = 0

def inspect(doc):
    issues = []
    case_rows = doc.get("cases", [])
    for case in case_rows:
        name, keys = case.get("name"), case.get("keys", [])
        codes = {"A": 38, "B": 56, "C": 54}
        expected_calls = []
        def add_input(event, code): expected_calls.append(["input", event, code])
        def add_sync(): expected_calls.append(["sync", sum(1 for x in expected_calls if x[0] == "sync") + 1])
        for key in keys:
            add_input(2, codes[key]); add_sync()
        if name in ("single", "ordered_two"):
            for key in keys:
                add_input(3, codes[key]); add_sync()
        elif name == "sync_error":
            add_input(3, codes[keys[0]]); add_sync()
            add_input(3, codes[keys[0]]); add_sync()
        else:
            for key in keys: add_input(3, codes[key])
            add_sync()
        if name != "sync_error":
            add_sync()
        if case.get("calls") != expected_calls: issues.append(name + ": XTest/sync order differs from baseline contract")
        rows = [r for r in case.get("records", []) if r.get("event") == "owner_keyup"]
        expected_count = len(keys) + (1 if name == "sync_error" else 0)
        if len(rows) != expected_count: issues.append(name + ": receipt count")
        if not any(r.get("event") == "owner_release" and r.get("verified") is True
                   and r.get("keys_down") == [] and r.get("buttons_down") == []
                   for r in case.get("records", [])):
            issues.append(name + ": no verified neutral owner cleanup")
        good = [r for r in rows if r.get("xsync_completed") is True]
        if name == "sync_error":
            failed = [r for r in rows if r.get("sync_error")]
            if len(failed) != 1 or failed[0].get("owner_sync_returned_ns") is not None or failed[0].get("xsync_completed") is not False:
                issues.append(name + ": failed sync falsely completed")
            expected_code = codes[keys[0]]
            for row in rows:
                if row.get("owner_id") != case.get("owner_id") or row.get("intent_token") != "token-" + name or row.get("keycode") != expected_code:
                    issues.append(name + ": failed/cleanup receipt identity")
                if row.get("physical_verification_authoritative") is not False or row.get("grants_input_authority") is not False:
                    issues.append(name + ": failed/cleanup authority overclaim")
            if len(good) != 1 or good[0].get("reason") != "close": issues.append(name + ": cleanup success receipt missing")
            elif type(good[0].get("owner_keyup_started_ns")) is not int or good[0]["owner_keyup_started_ns"] > good[0].get("owner_sync_returned_ns", -1):
                issues.append(name + ": cleanup success interval invalid")
            if case.get("final_down"): issues.append(name + ": cleanup left key down")
            continue
        if len(good) != len(keys): issues.append(name + ": completion count")
        for i, key in enumerate(keys):
            code = codes[key]
            matches = [r for r in good if r.get("intent_token") == "token-" + name
                       and (r.get("key") == key if name in ("single", "ordered_two") else r.get("keycode") == code)]
            if len(matches) != 1: issues.append(name + ": identity/duplicate " + key); continue
            row = matches[0]
            if row.get("owner_id") != case.get("owner_id"):
                issues.append(name + ": owner identity mismatch")
            if row.get("keycode") != code: issues.append(name + ": keycode mismatch")
            allowed_reasons = ({"release", "close"} if name == "sync_error" else
                               {"explicit_up"} if name in ("single", "ordered_two") else
                               {"cancelled"} if name == "cancel" else {"release"})
            if row.get("reason") not in allowed_reasons:
                issues.append(name + ": release reason mismatch")
            a, b = row.get("owner_keyup_started_ns"), row.get("owner_sync_returned_ns")
            if type(a) is not int or type(b) is not int or a > b: issues.append(name + ": timestamp interval")
            if row.get("physical_verification_authoritative") is not False or row.get("grants_input_authority") is not False:
                issues.append(name + ": authority overclaim")
        if case.get("final_down"): issues.append(name + ": non-neutral fake keymap")
        if name in ("bulk", "cancel"):
            if len({r.get("batch_release_id") for r in good}) != 1: issues.append(name + ": batch identity")
            if len({r.get("owner_sync_returned_ns") for r in good}) != 1: issues.append(name + ": not one shared sync")
            inputs = [x for x in case.get("calls", []) if x[0] == "input" and x[1] == 3]
            sync_positions = [i for i, x in enumerate(case.get("calls", [])) if x[0] == "sync"]
            release_positions = [i for i, x in enumerate(case.get("calls", [])) if x[0] == "input" and x[1] == 3]
            after_release_syncs = [i for i in sync_positions if release_positions and i > max(release_positions)]
            if len(inputs) < len(keys) or not after_release_syncs:
                issues.append(name + ": release calls not before shared sync")
        if name in ("single", "ordered_two"):
            for transition in case.get("receipts", []):
                if transition.get("owner_keyup_join") != "MATCHED_EXPLICIT_KEYUP" or transition.get("owner_keyup_interval_ordered") is not True:
                    issues.append(name + ": caller receipt join/order")
                nested = transition.get("owner_keyup_receipt", {})
                if not (type(transition.get("release_call_started_ns")) is int and type(transition.get("release_call_returned_ns")) is int
                        and transition["release_call_started_ns"] <= nested.get("owner_keyup_started_ns", -1)
                        <= nested.get("owner_sync_returned_ns", -1) <= transition["release_call_returned_ns"]):
                    issues.append(name + ": caller/owner bracket nesting")
    return issues

base_issues = inspect(raw)
errors.extend(base_issues)
mutations = []
if cases:
    def altered(fn):
        doc = copy.deepcopy(raw); fn(doc); mutations.append(doc)
    altered(lambda d: d["cases"][0]["records"][0].update(owner_sync_returned_ns=-1))
    altered(lambda d: d["cases"][0]["records"].__setitem__(slice(None), [r for r in d["cases"][0]["records"] if r.get("event") != "owner_keyup"]))
    altered(lambda d: d["cases"][0]["records"].append(copy.deepcopy(next(r for r in d["cases"][0]["records"] if r.get("event") == "owner_keyup"))))
    altered(lambda d: next(r for r in d["cases"][0]["records"] if r.get("event") == "owner_keyup").update(intent_token="wrong"))
    altered(lambda d: next(r for r in d["cases"][0]["records"] if r.get("event") == "owner_keyup").update(physical_verification_authoritative=True))
    altered(lambda d: next(r for r in d["cases"][4]["records"] if r.get("event") == "owner_keyup").update(xsync_completed=True, owner_sync_returned_ns=1))
    altered(lambda d: next(r for r in d["cases"][0]["records"] if r.get("event") == "owner_keyup").update(owner_id="wrong"))
    altered(lambda d: next(r for r in d["cases"][1]["records"] if r.get("event") == "owner_keyup").update(keycode=999))
for i, mutation in enumerate(mutations):
    if inspect(mutation): mutation_rejections += 1
check(mutation_rejections == len(mutations), "mutation suite failed to reject all controls")
report = {"schema":"owner-keyup-audit-v1", "result_sha256":hashlib.sha256(RESULT.read_bytes()).hexdigest(),
          "base_error_count":len(base_issues), "mutation_count":len(mutations),
          "mutation_rejections":mutation_rejections, "errors":errors,
          "decision":"PASS_OWNER_KEYUP_INSTRUMENTATION_SCOPED" if not errors else "FAIL"}
out = RESULT.parent / "AUDIT.json"
out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
print(json.dumps(report, sort_keys=True))
raise SystemExit(0 if not errors else 1)
