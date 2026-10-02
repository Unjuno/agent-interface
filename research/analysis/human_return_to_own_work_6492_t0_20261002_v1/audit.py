import argparse
import copy
import hashlib
import json
from pathlib import Path


ARMS = ("timing_only", "preserved_view", "optional_cue")
ROW_KEYS = {"case_id", "arm", "task_id", "window_id", "surface_id", "interrupt_id",
            "question", "answers", "priority", "delay_ms", "before_version", "current_version",
            "state_change_warning", "source_view", "cue", "automated_actions", "source_view_digest"}


def expected_view(case):
    if case is None:
        return None
    changed = case["before_version"] != case["after_version"]
    return {"task_id": case["task_id"], "window_id": case["window_id"],
            "surface_id": case["surface_id"], "version": case["before_version"],
            "sha256": case["source_view_sha256"], "historical": changed}


def expected_cue(case, arm):
    if arm != "optional_cue":
        return {"offered": False, "status": "not_offered", "author": None, "text": None}
    source = case["cue"]
    if source["status"] == "not_written":
        return {"offered": True, "status": "unused", "author": None, "text": None}
    if source["version"] != case["after_version"]:
        return {"offered": True, "status": "stale_withheld", "author": "user", "text": None}
    return {"offered": True, "status": "used", "author": "user", "text": source["text"]}


def validate(fixture, oracle, raw, fixture_hash):
    errors = []
    cards = {case["case_id"]: case for case in fixture["cases"]}
    truths = {case["case_id"]: case for case in oracle["cases"]}
    expected_ids = [case["case_id"] for case in fixture["cases"]]
    if raw.get("schema") != "return-to-work-candidate-raw-v1": errors.append("schema")
    if raw.get("fixture_sha256") != fixture_hash: errors.append("fixture_hash")
    if raw.get("case_order") != expected_ids or raw.get("arms") != list(ARMS): errors.append("denominator_or_arm_order")
    rows = raw.get("rows", [])
    if len(rows) != len(expected_ids) * len(ARMS): errors.append("row_count")
    keys = [(row.get("case_id"), row.get("arm")) for row in rows]
    wanted = [(cid, arm) for cid in expected_ids for arm in ARMS]
    if keys != wanted: errors.append("row_identity_order")
    by_pair = {(row.get("case_id"), row.get("arm")): row for row in rows}
    shared_fields = ("question", "answers", "priority", "delay_ms", "before_version", "current_version", "state_change_warning")
    for cid in expected_ids:
        case, truth = cards[cid], truths.get(cid)
        if truth is None: errors.append(cid + ":missing_oracle"); continue
        if (truth["task_id"], truth["window_id"]) != (case["task_id"], case["window_id"]): errors.append(cid + ":oracle_identity")
        common_rows = [by_pair.get((cid, arm), {}) for arm in ARMS]
        for row in common_rows:
            if set(row) != ROW_KEYS: errors.append(cid + ":field_set")
            if row.get("task_id") != case["task_id"] or row.get("window_id") != case["window_id"]: errors.append(cid + ":source_binding")
            if row.get("surface_id") != case["surface_id"] or row.get("interrupt_id") != case["interrupt_id"]: errors.append(cid + ":surface_or_interrupt_binding")
            if row.get("before_version") != case["before_version"] or row.get("current_version") != case["after_version"]: errors.append(cid + ":version_binding")
            if row.get("state_change_warning") != (case["before_version"] != case["after_version"]): errors.append(cid + ":state_change_warning")
            if row.get("automated_actions") != []: errors.append(cid + ":automatic_effect")
            if row.get("delay_ms") != (0 if case["priority"] == "emergency_release" else 1000): errors.append(cid + ":interrupt_delay")
        for field in shared_fields:
            if len({json.dumps(row.get(field), sort_keys=True) for row in common_rows}) != 1: errors.append(cid + ":arm_mismatch:" + field)
            if common_rows[0].get(field) != (0 if field == "delay_ms" and case["priority"] == "emergency_release" else 1000 if field == "delay_ms" else case["question"] if field == "question" else case["answers"] if field == "answers" else case["priority"] if field == "priority" else case["before_version"] if field == "before_version" else case["after_version"] if field == "current_version" else case["before_version"] != case["after_version"]):
                errors.append(cid + ":fixture_fact_mismatch:" + field)
        for arm, row in zip(ARMS, common_rows):
            view = row.get("source_view")
            if arm == "timing_only":
                if view is not None: errors.append(cid + ":unexpected_view")
            elif view != expected_view(case): errors.append(cid + ":view_provenance")
            expected_digest = hashlib.sha256((case["task_id"] + "\n" + case["window_id"] + "\n" + case["source_view_sha256"]).encode("utf-8")).hexdigest()
            if row.get("source_view_digest") != expected_digest: errors.append(cid + ":view_digest")
            if row.get("cue") != expected_cue(case, arm): errors.append(cid + ":cue_provenance_or_offer")
        if truth["correct_return_action"] in json.dumps(common_rows): errors.append(cid + ":oracle_leak")
    return errors


def main():
    parser = argparse.ArgumentParser()
    for name in ("fixture", "oracle", "raw", "freeze", "output"): parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    fixture_b, oracle_b, raw_b = (Path(p).read_bytes() for p in (args.fixture, args.oracle, args.raw))
    fixture, oracle, raw = (json.loads(b) for b in (fixture_b, oracle_b, raw_b))
    freeze = json.loads(Path(args.freeze).read_text(encoding="utf-8"))
    digest = hashlib.sha256(fixture_b).hexdigest()
    errors = []
    for name, blob in (("fixture.json", fixture_b), ("oracle.json", oracle_b), ("candidate.py", Path(__file__).with_name("candidate.py").read_bytes()), ("audit.py", Path(__file__).read_bytes())):
        if hashlib.sha256(blob).hexdigest() != freeze["sha256"][name]: errors.append(name + ":hash_mismatch")
    errors.extend(validate(fixture, oracle, raw, digest))
    mutations = {}
    def rejected(label, mutate):
        altered = copy.deepcopy(raw); mutate(altered)
        mutations[label] = bool(validate(fixture, oracle, altered, digest))
    rejected("swapped_task_window", lambda x: x["rows"][1]["window_id"] == "window-evil" or x["rows"][1].update(window_id="window-evil"))
    rejected("stale_cue_after_external_edit", lambda x: x["rows"][5]["cue"].update(status="used", text="confirm the Tuesday slot"))
    rejected("forged_agent_authored_cue", lambda x: x["rows"][2]["cue"].update(author="agent"))
    rejected("duplicate_save_effect", lambda x: x["rows"][17].update(automated_actions=["save"]))
    rejected("offered_cue_field_absent", lambda x: x["rows"][2].pop("cue"))
    rejected("emergency_release_delayed", lambda x: x["rows"][9].update(delay_ms=1000))
    status = "METHOD_PASS_SCOPED" if not errors and all(mutations.values()) and len(raw.get("rows", [])) == 18 else "METHOD_FAIL"
    report = {"status": status, "errors": errors, "cases_per_arm": len(fixture["cases"]), "rows": len(raw.get("rows", [])),
              "arms": list(ARMS), "corruptions_rejected": mutations,
              "scope": "finite synthetic protocol/provenance method only; no participant, human memory, GUI, effect, or product evidence",
              "sha256": {"fixture": digest, "oracle": hashlib.sha256(oracle_b).hexdigest(), "raw": hashlib.sha256(raw_b).hexdigest()}}
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__": main()
