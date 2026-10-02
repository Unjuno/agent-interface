"""Finite source-bound communicative-force gate for Issue #6424; no model or effects."""
import json
from pathlib import Path

ROOT = Path(__file__).parent
FORCES = {"EXECUTE_REQUEST", "INFORMATION_REQUEST", "PREPARE_ONLY", "HYPOTHETICAL", "QUOTED_OR_REPORTED", "UNKNOWN_FORCE"}


def decide(case):
    turns = {turn["id"]: turn for turn in case["turns"]}
    errors = []
    if any(not turn.get("authenticated") or turn.get("author") != "user" for turn in turns.values()):
        errors.append("UNAUTHENTICATED_TURN")
    if case["force"] not in FORCES:
        errors.append("UNKNOWN_FORCE_LABEL")
    for span in case["source_spans"]:
        turn = turns.get(span["turn"])
        if turn is None or turn["text"][span["start"]:span["end"]] != span["text"]:
            errors.append("SOURCE_SPAN_MISMATCH")
    effect = case["effect"]
    force = case["force"]
    if force in {"INFORMATION_REQUEST", "HYPOTHETICAL", "QUOTED_OR_REPORTED"}:
        transition = "EXPLAIN"
    elif force == "PREPARE_ONLY":
        transition = "PREPARE"
    elif force == "UNKNOWN_FORCE":
        transition = "ASK"
    else:
        transition = "EXECUTE"
    # A later authenticated source turn must itself carry the execution request.
    if force == "EXECUTE_REQUEST" and len(turns) > 1:
        latest = turns[max(turns, key=lambda key: list(turns).index(key))]
        if latest["id"] not in {span["turn"] for span in case["source_spans"] if not span.get("quoted")}:
            errors.append("EXECUTION_SOURCE_NOT_ADOPTED")
    if "DO_NOT_SEND" in case["prohibitions"] and transition == "EXECUTE":
        errors.append("PROHIBITION_IGNORED")
    if "DO_NOT_DELETE" in case["prohibitions"] and effect == "delete_archive" and transition == "EXECUTE":
        errors.append("PROHIBITION_IGNORED")
    if transition == "EXECUTE" and case["world"] != "eligible":
        transition = "YIELD"
    # Communicative force never substitutes for normal authority/effect admission.
    if transition == "EXECUTE":
        transition = "EXECUTE_AFTER_ORDINARY_GATES"
    return {"case_id": case["id"], "transition": transition, "errors": sorted(set(errors))}


def main():
    corpus = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
    rows = [decide(case) for case in corpus["cases"]]
    (ROOT / "candidate.raw.json").write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(rows, sort_keys=True))


if __name__ == "__main__":
    main()
