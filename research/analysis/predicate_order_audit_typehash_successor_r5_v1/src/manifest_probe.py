"""Exact-path source/output digest verifier with in-memory negative controls."""
import hashlib
import json
import re
from pathlib import Path


SOURCE_PATHS = (
    "/src/audit_hardened.py", "/src/candidate.py", "/src/runner.py",
    "/src/independent_audit.py", "/src/manifest_probe.py", "/src/test_protocol.py",
    "/src/formal_entry.sh", "/src/audit_entry.sh", "/src/manifest_entry.sh",
    "/src/probe_baseline.py", "/src/allocation_entry.sh",
)
OUTPUT_PATHS = (
    "/input/RAW.json", "/input/AUDIT.json", "/evidence/runner_result.json",
    "/audit/AUDIT.json",
)
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class Reject(ValueError):
    pass


def exact_digest_map(value, expected_paths, label):
    if type(value) is not dict or set(value) != set(expected_paths):
        raise Reject(label + ":path-set")
    for path in expected_paths:
        digest = value[path]
        if type(digest) is not str or not HEX64.fullmatch(digest):
            raise Reject(label + ":digest-shape:" + path)
    return value


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(manifest):
    sources = exact_digest_map(manifest.get("source_sha256"), SOURCE_PATHS, "source")
    outputs = exact_digest_map(manifest.get("output_sha256"), OUTPUT_PATHS, "output")
    for path, expected in sources.items():
        if digest(path) != expected:
            raise Reject("source:hash:" + path)
    for path, expected in outputs.items():
        if digest(path) != expected:
            raise Reject("output:hash:" + path)
    return {"status": "PASS_EXACT_PATH_MANIFEST", "sources": len(sources),
            "outputs": len(outputs), "errors": []}


def main():
    manifest = json.loads(Path("/audit/manifest.json").read_text(encoding="utf-8"))
    positive = verify(manifest)
    controls = []
    for label, edit in (
        ("empty-maps", lambda m: (m.update(source_sha256={}), m.update(output_sha256={}))),
        ("omitted-path", lambda m: m["source_sha256"].pop(SOURCE_PATHS[0])),
        ("changed-digest", lambda m: m["output_sha256"].__setitem__(
            OUTPUT_PATHS[2], "0" * 64)),
    ):
        changed = json.loads(json.dumps(manifest))
        edit(changed)
        try:
            verify(changed)
            controls.append({"control": label, "rejected": False})
        except Reject as exc:
            controls.append({"control": label, "rejected": True, "reason": str(exc)})
    result = {"positive": positive, "negative_controls": controls,
              "decision": "PASS_MANIFEST_BINDING_SCOPED"
              if all(row["rejected"] for row in controls) else "FAIL_MANIFEST_CONTROL",
              "errors": []}
    Path("/audit/manifest_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(result["decision"])


if __name__ == "__main__":
    main()
