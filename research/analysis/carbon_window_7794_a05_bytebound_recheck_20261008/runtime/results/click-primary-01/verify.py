"""Check retained primary-use evidence without replaying input."""
import base64
import hashlib
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parent


def check(value, message):
    if not value:
        raise ValueError(message)


def main():
    manifest = json.loads((ROOT / "manifest.json").read_text())
    archive = ROOT / "raw.tar.gz"
    digest = lambda data: hashlib.sha256(data).hexdigest()
    check(digest(archive.read_bytes()) == manifest["archive_sha256"], "archive hash")
    data = {}
    with tarfile.open(archive, "r:gz") as tar:
        for member in tar:
            check(member.isfile() and member.name not in data, "member type/duplicate")
            data[member.name] = tar.extractfile(member).read()
    check(set(data) == set(manifest["files"]), "file set")
    for name, expected in manifest["files"].items():
        check(digest(data[name]) == expected, "file hash: " + name)
    read = lambda name: json.loads(data[name])
    check(digest(data["build/runtime.pyz"]) == read("build/manifest.json")["sha256"], "portable build")
    expected = {"left": {"saved": True, "text": "http://p_q"},
                "right": {"saved": True, "text": "http://s_t"}}
    check(read("evaluation.json")["actual"] == expected and read("evaluation.json")["success"] is True, "evaluation")
    for name in expected:
        check(read(name + "-effect.json") == expected[name], "independent file")
    check(read("host/exit.json") == {"code": 0, "signal": None}, "transport exit")
    check(all(p["returncode"] is not None for p in read("cleanup.json")), "process cleanup")
    events = [json.loads(line) for line in data["host/host-events.jsonl"].splitlines()]
    order = lambda kind, attempt: next(i for i, e in enumerate(events) if e["kind"] == kind and e.get("attempt") == attempt)
    total_wait = 0
    for attempt in range(1, 7):
        request = read(f"host/request-{attempt}.json")
        reply_bytes = data[f"host/reply-{attempt}.json"]
        reply = json.loads(reply_bytes)
        check(reply["status"] == "returned" and reply["id"] == request["id"] == attempt, "reply identity")
        view = json.loads(next(b["text"] for b in reply["result"]["content"] if b["type"] == "text"))
        if attempt <= 5:
            review = read(f"host/review-{attempt}.json")
            check(review["reply_sha256"] == digest(reply_bytes) and review["call_id"] == view["call_id"], "review binding")
            images = [b for b in reply["result"]["content"] if b["type"] == "image"]
            check(len(images) == 1 and digest(base64.b64decode(images[0]["data"], validate=True)) == review["images"][0]["sha256"], "image binding")
            check(order("presentation_callbacks_completed", attempt) < order("review_recorded", attempt), "review ordering")
        if attempt in (2, 3, 4, 5):
            check(request["tool"] == "interface_dispatch", "dispatch")
            program = request["arguments"]["program"]
            target = "left" if attempt in (2, 3) else "right"
            check(program["ops"][0] == {"op": "focus", "target": target}, "target")
            report = read("mcp/" + view["call_id"] + "/report.json")
            check(report["normalization"]["source_program"] == program, "executed source")
            check(report["result"]["status"] == "completed", "execution")
            execution = report["result"]["execution"]
            check(execution["releases"][-1]["verified"] is True, "release")
            total_wait += sum(w["requested_ms"] for w in execution["waits"])
            if attempt in (2, 4):
                check(program["ops"][4] == {"op": "wait_update", "timeout_ms": 50}, "post-click wait")
                check(program["ops"][5] == {"op": "text", "text": expected[target]["text"], "gap_ms": 20}, "text")
                check(not any(op["op"] == "key_chord" for op in program["ops"]), "save before review")
                check(view["receipt"]["schema"] == "agent-interface/receipt-view-paced-brief-v1", "brief input")
            else:
                check(program["ops"][1] == {"op": "key_chord", "keys": ["CTRL", "S"]}, "explicit save")
                check(order("review_recorded", attempt - 1) < order("send_requested", attempt), "save preceded value review")
        if attempt == 6:
            check(request["tool"] == "interface_close" and view["status"] == "closed" and view["release"]["verified"] is True, "close")
    check(len([name for name in data if name.startswith("host/request-")]) == 6, "call count")
    check(total_wait == 760, "fixed waits")
    check(read("host-timing.json") == json.loads((ROOT / "host-timing.json").read_text()), "timing copy")
    check(read("host-timing.json")["timeline_status"] == "complete", "host timeline")
    print(json.dumps({"status": "PASS", "files": len(data), "calls": 6, "saved_files": 2,
                      "requested_wait_ms": total_wait, "scope": "evidence identity, ordering and saved effects; not semantic-model or speed proof"}))


if __name__ == "__main__":
    main()
