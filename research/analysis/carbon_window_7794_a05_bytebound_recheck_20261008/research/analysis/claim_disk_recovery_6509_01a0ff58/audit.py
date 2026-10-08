"""Independent retained-file oracle; imports neither writer nor reconstructor."""
import copy
import hashlib
import json
from pathlib import Path
import sys

EXPECTED = {
    "c01": ("PARTIAL_UNKNOWN", ["identity"], ["freshness", "effect"]),
    "c02": ("PARTIAL_UNKNOWN", ["identity", "freshness"], ["effect"]),
    "c03": ("COMPLETE_VERDICT", ["identity", "freshness", "effect"], []),
    "c04": ("COMPLETE_VERDICT", ["identity", "freshness", "effect"], []),
    "c05": ("COMPLETE_VERDICT", ["identity", "freshness", "effect"], []),
    "c06": ("PARTIAL_UNKNOWN", ["identity", "freshness"], ["effect"]),
    "c07": ("COUNTEREXAMPLE", ["identity"], ["freshness", "effect"]),
    "c08": ("PARTIAL_UNKNOWN", [], ["identity", "freshness", "effect"]),
    "c09": ("PARTIAL_UNKNOWN", [], ["identity", "freshness", "effect"]),
}

def audit(raw, folder):
    if raw["schema"] != "disk-prefix-process-boundary-v1":
        raise ValueError("schema")
    here = Path(__file__).resolve().parent
    frozen = json.loads((here / "FREEZE.json").read_text())
    specs = {item["id"]: item for item in json.loads((here / "cases.json").read_text())}
    actual_sources = {name: hashlib.sha256((here / name).read_bytes()).hexdigest()
                      for name in frozen["sources"]}
    if raw["sources"] != frozen["sources"] or actual_sources != frozen["sources"]:
        raise ValueError("source freeze")
    remaining = set(EXPECTED)
    cached_false_completions = 0
    reused_checks = 0
    for row in raw["rows"]:
        case = row["case"]
        name = case["id"]
        if name not in remaining:
            raise ValueError("duplicate/unexpected case")
        if case != specs[name] or type(case["generation"]) is not int or any(
            type(case[key]) is not bool for key in ("negative", "duplicate")
        ):
            raise ValueError("case identity")
        remaining.remove(name)
        journal = (folder / name / "receipts.jsonl").read_bytes()
        if hashlib.sha256(journal).hexdigest() != row["journal_sha256"]:
            raise ValueError("journal hash")
        segments = journal.split(b"\n")
        count = len(segments) - 1
        wanted_count = {"receipt_1": 1, "receipt_2": 2, "receipt_3": 3, "before_commit": 3, "after_commit": 3, "torn_third": 2}[case["cut"]] + int(case["duplicate"])
        if count != wanted_count:
            raise ValueError("journal row count")
        for index, encoded in enumerate(segments[:-1]):
            event = json.loads(encoded)
            wanted = dict(sequence=index + 1, check=("identity", "freshness", "effect", "effect")[index],
                value=not (case["negative"] and index == 0), generation=1, scope="synthetic-claim")
            if event != wanted or type(event["sequence"]) is not int or type(event["value"]) is not bool:
                raise ValueError("receipt truth/order")
        if segments[-1] != (b'{"sequence":3' if name == "c06" else b""):
            raise ValueError("torn bytes")
        processes = row["processes"]
        if len(processes) != 3 or [p["mode"] for p in processes] != ["write", "read", "read"] or [p["exit_code"] for p in processes] != [73, 0, 0] or any(p["stderr"] for p in processes):
            raise ValueError("process exits")
        result = row["recovery"]
        if result != json.loads(processes[1]["stdout"]) or row["second_recovery"] != json.loads(processes[2]["stdout"]) or result != row["second_recovery"]:
            raise ValueError("separate recovery outputs")
        disposition, completed, missing = EXPECTED[name]
        if (result["disposition"], result["completed"], result["missing"]) != (disposition, completed, missing):
            raise ValueError("finite verdict oracle")
        if result["consumer_authority"] is not False or result["journal_sha256"] != row["journal_sha256"]:
            raise ValueError("authority/evidence binding")
        if row["always_unknown"] != "PARTIAL_UNKNOWN":
            raise ValueError("conservative baseline")
        cached_path = folder / name / "cached-verdict.json"
        wanted_cached = "COMPLETE_VERDICT" if name in ("c05", "c08", "c09") else "PARTIAL_UNKNOWN"
        if row["trust_cached"] != wanted_cached or cached_path.exists() != (name in ("c05", "c08", "c09")):
            raise ValueError("cached baseline")
        if cached_path.exists() and json.loads(cached_path.read_text()) != {"disposition": "COMPLETE_VERDICT"}:
            raise ValueError("marker contents")
        cached_false_completions += row["trust_cached"] == "COMPLETE_VERDICT" and disposition != "COMPLETE_VERDICT"
        reused_checks += len(completed)
    if remaining:
        raise ValueError("missing cases")
    return dict(status="PASS_PROCESS_EXIT_BOUNDARY_SCOPED", cases=9,
        child_invocations=27, complete=3, counterexamples=1, partial_unknown=5,
        reusable_current_checks=reused_checks, cached_false_completions=cached_false_completions,
        consumer_authority=False)

if __name__ == "__main__":
    folder = Path(sys.argv[1])
    raw = json.loads((folder / "raw.json").read_text())
    result = audit(raw, folder)
    rejected = []
    for kind in ("drop", "duplicate", "promote-partial", "stale-reuse", "exit-flip", "hash-flip"):
        changed = copy.deepcopy(raw)
        if kind == "drop": changed["rows"].pop()
        elif kind == "duplicate": changed["rows"].append(changed["rows"][0])
        elif kind == "promote-partial": changed["rows"][0]["recovery"]["disposition"] = "COMPLETE_VERDICT"
        elif kind == "stale-reuse": changed["rows"][7]["recovery"]["completed"] = ["identity"]
        elif kind == "exit-flip": changed["rows"][0]["processes"][0]["exit_code"] = 0
        else: changed["rows"][0]["journal_sha256"] = "0" * 64
        try:
            audit(changed, folder)
        except ValueError:
            rejected.append(kind)
        else:
            raise RuntimeError("mutation survived: " + kind)
    result["rejected_raw_mutations"] = rejected
    with Path(sys.argv[2]).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps(result))
