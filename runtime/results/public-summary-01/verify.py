"""Verify retained presentation evidence using the exact archived implementation."""
import hashlib
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent


def require(ok, message):
    if not ok:
        raise ValueError(message)


def main():
    manifest = json.loads((ROOT / "manifest.json").read_text())
    digest = lambda b: hashlib.sha256(b).hexdigest()
    archive = ROOT / "raw.tar.gz"
    require(digest(archive.read_bytes()) == manifest["archive_sha256"], "archive hash")
    data = {}
    with tarfile.open(archive, "r:gz") as tar:
        for member in tar:
            require(member.isfile() and member.name not in data, "member type/duplicate")
            data[member.name] = tar.extractfile(member).read()
    require(set(data) == set(manifest["files"]), "file set")
    for name, expected in manifest["files"].items():
        require(digest(data[name]) == expected, "file hash: " + name)
    read = lambda name: json.loads(data[name])
    view = lambda i: json.loads(next(b["text"] for b in read(f"primary/host/reply-{i}.json")["result"]["content"] if b["type"] == "text"))
    with tempfile.TemporaryDirectory(prefix="public-summary-verify-") as temporary:
        build = Path(temporary) / "runtime.pyz"
        build.write_bytes(data["final-build/runtime.pyz"])
        require(digest(build.read_bytes()) == read("final-build/manifest.json")["sha256"], "build hash")
        with zipfile.ZipFile(build) as zipped:
            require(digest(zipped.read("runtime/cli_v1/public_summary.py")) == manifest["summary_module_sha256"], "summary source")
        sys.path.insert(0, str(build))
        from runtime.cli_v1.public_summary import summarize_public_dispatch, encoded
        from runtime.cli_v1.public_presentation import brief_public_report
        import runtime.cli_v1.public_summary as implementation
        require(str(implementation.__file__).startswith(str(build)), "wrong implementation")
        rows = []
        for attempt in (2, 3):
            full, actual = read(f"full-{attempt}.json"), view(attempt)
            require(summarize_public_dispatch(full) == actual, "live projection changed")
            rows.append({"attempt": attempt, "full_bytes": len(encoded(full)),
                         "prior_brief_bytes": len(encoded(brief_public_report(full))),
                         "summary_bytes": len(encoded(actual))})
        result = json.loads((ROOT / "result.json").read_text())
        require(rows == result["rows"], "byte rows")
        require({key: sum(row[key] for row in rows) for key in result["totals"]} == result["totals"], "byte totals")
    restored = view(4)
    raw = read("primary/mcp/" + view(3)["call_id"] + "/report.json")
    require(restored["operation_invoked"] is False and restored["receipt"]["source"]["raw_report"] == raw, "full lookup")
    refused = view(5)["receipt"]["source"]["raw_report"]["result"]
    require(refused["status"] == "refused" and refused["program_execution_started"] is False and refused["program_emissions"] == 0, "refusal")
    require(read("primary/effect.json") == {"saved": True, "text": "http://v_w"}, "saved effect")
    require(read("primary/evaluation.json")["success"] is True, "evaluation")
    require(view(6)["status"] == "closed" and view(6)["release"]["verified"] is True, "close")
    require(read("primary/host/exit.json") == {"code": 0, "signal": None}, "transport exit")
    require(all(p["returncode"] is not None for p in read("primary/cleanup.json")), "cleanup")
    require(read("native-after/result.json")["status"] == "PASS", "native checks")
    require(read("retained-presentation-pass/result.json")["status"] == "PASS", "retained presentation")
    print(json.dumps({"status": "PASS", "files": len(data), "rows": rows,
                      "scope": "retained projection, retrieval, refusal and final effect; not tokens or latency"}))


if __name__ == "__main__":
    main()
