"""Reconstruct this scoped comparison from retained raw records, without GUI input."""
import hashlib
import json
from pathlib import Path
import statistics
import tarfile

ROOT = Path(__file__).resolve().parent


def require(ok, message):
    if not ok:
        raise ValueError(message)


def main():
    manifest = json.loads((ROOT / "manifest.json").read_text())
    archive = ROOT / "raw.tar.gz"
    require(hashlib.sha256(archive.read_bytes()).hexdigest() == manifest["archive_sha256"], "archive hash")
    data = {}
    with tarfile.open(archive, "r:gz") as tar:
        for member in tar:
            require(member.isfile() and member.name not in data, "member type/duplicate")
            data[member.name] = tar.extractfile(member).read()
    require(set(data) == set(manifest["files"]), "member set")
    for name, digest in manifest["files"].items():
        require(hashlib.sha256(data[name]).hexdigest() == digest, "member hash: " + name)
    read = lambda name: json.loads(data[name])
    plan = read("plan.json")
    require(plan["schedule_ms"] == [0, 50, 50, 0] * 3, "schedule")
    require(hashlib.sha256(data["runner.py"]).hexdigest() == plan["runner_sha256"], "runner identity")
    require(read("execution.json")["observed_exit_code"] == 0, "runner exit")
    require(all(p["returncode"] is not None for p in read("cleanup.json")), "live process")
    rows = read("results.json")
    require(len(rows) == 12, "denominator")
    normalized = []
    for i, gap in enumerate(plan["schedule_ms"]):
        base = f"case-{i:02d}/"
        row = read(base + "result.json")
        require(row == rows[i] and row["case"] == i and row["post_click_wait_ms"] == gap, "row identity")
        requests = [read(name) for name in data if name.startswith(base + "mcp/") and name.endswith("/request.json")]
        require(sorted(q["operation"] for q in requests) == ["close", "dispatch", "observe"], "retained call set")
        program = read(base + "program.json")
        ops = program["ops"][:]
        if gap:
            require(ops.pop(4) == {"op": "wait_update", "timeout_ms": 50}, "explicit pause")
        require(ops[4] == {"op": "text", "text": plan["payload"], "gap_ms": 20}, "payload")
        normalized.append(ops)
        effect = read(base + "effect.json")
        correct = effect == {"saved": True, "text": plan["payload"]}
        require(row["effect"] == effect and row["correct"] is correct, "effect mismatch")
        require(effect["text"] in ("http://m_n", "ttp://m_n"), "unexpected saved effect")
        report = read(base + "raw-report.json")
        require(report["normalization"]["source_program"] == program, "source program")
        execution = report["result"]["execution"]
        require(report["result"]["status"] == row["status"] == "completed", "execution outcome")
        require(execution == row["execution"] and execution["program_emissions"] == 29, "execution identity")
        require(execution["releases"][-1]["verified"] is True, "release")
        require(sum(w["requested_ms"] for w in execution["waits"]) == 280 + gap, "requested waits")
        require(all(w["completed"] is True and w["kind"] == "fixed_delay" and w["update_observed"] is None for w in execution["waits"]), "wait contract")
        closed = read(base + "close.json")
        view = json.loads(next(x["text"] for x in closed["content"] if x["type"] == "text"))
        require(view["status"] == "closed" and view["release"]["verified"] is True, "session close")
        require(read(base + "app-exit.json")["returncode"] == -15, "fixture termination")
        events = [json.loads(line) for line in data[base + "events.jsonl"].splitlines()]
        h = [e for e in events if e.get("char") == "h"]
        require(h and all(e["widget"] == (".!entry" if correct else ".") for e in h), "first-character recipient")
        require(type(row["tool_return_ns"]) is int and row["tool_return_ns"] > 0, "tool timing")
        require(row["mcp_calls"] == 3 and row["repair_calls"] == 0, "call counts")
    require(all(ops == normalized[0] for ops in normalized), "non-wait program drift")
    arms = []
    for gap in (0, 50):
        selected = [r for r in rows if r["post_click_wait_ms"] == gap]
        arms.append({"post_click_wait_ms": gap, "cases": len(selected),
                     "correct": sum(r["correct"] for r in selected),
                     "missing_prefix": sum(r["effect"] == {"saved": True, "text": "ttp://m_n"} for r in selected),
                     "tool_return_median_ms": statistics.median(r["tool_return_ns"] / 1e6 for r in selected),
                     "program_emissions_per_case": 29, "mcp_calls_per_case": 3, "repair_calls": 0})
    require(arms == json.loads((ROOT / "result.json").read_text())["arms"], "derived metrics")
    print(json.dumps({"status": "PASS", "files": len(data), "cases": len(rows), "arms": arms,
                      "scope": "retained fixed-task comparison; no model-speed or general readiness proof"}))


if __name__ == "__main__":
    main()
