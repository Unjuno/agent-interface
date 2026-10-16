"""Emit an immutable manifest for every input used by the v2 recount."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path


EVIDENCE = Path("research/live_control/results/integrated-efficiency-live-01")
V1_FREEZE = Path("research/live_control/integrated_efficiency_live_audit_20260928/FREEZE.json")
ARMS = ("plain", "ephemeral", "persistent")


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("input_main_commit")
    args = parser.parse_args()
    root = args.root.resolve()
    commit = args.input_main_commit
    if git(root, "rev-parse", "--verify", f"{commit}^{{commit}}") != commit:
        raise SystemExit("input commit is not available exactly")

    paths = [V1_FREEZE]
    paths.extend(EVIDENCE / name for name in
                 ("preregistration.json", "trace.json", "report.json", "audit.json"))
    for arm in ARMS:
        paths.append(EVIDENCE / "preflight" / arm / "gate" / "gate-report.json")
        paths.append(EVIDENCE / "arms" / arm / "task-details.json")
        paths.append(EVIDENCE / "arms" / arm / "runtime" / "submission-history.jsonl")
        paths.extend(sorted((EVIDENCE / "model-calls" / arm).rglob("result.json")))

    expected = set(paths)
    if len(expected) != len(paths):
        raise SystemExit("duplicate input path in manifest inventory")
    raw_paths = [p for p in paths if p.name == "result.json"]
    if len(raw_paths) != 14:
        raise SystemExit(f"expected 14 raw result files, found {len(raw_paths)}")
    call_ids = []
    for rel in raw_paths:
        data = json.loads((root / rel).read_text(encoding="utf-8"))
        call_id = data.get("call_id")
        if not isinstance(call_id, str) or not call_id:
            raise SystemExit(f"raw result lacks call_id: {rel.as_posix()}")
        call_ids.append(call_id)
    if len(call_ids) != len(set(call_ids)):
        raise SystemExit("duplicate raw result call_id in frozen input")
    missing = [p.as_posix() for p in paths if not (root / p).is_file()]
    if missing:
        raise SystemExit("missing inputs: " + ", ".join(missing))

    files = []
    for rel in sorted(paths, key=lambda p: p.as_posix()):
        blob = git(root, "rev-parse", f"{commit}:{rel.as_posix()}")
        data = (root / rel).read_bytes()
        files.append({
            "path": rel.as_posix(),
            "sha256": hashlib.sha256(data).hexdigest(),
            "git_blob": blob,
        })
    print(json.dumps({
        "schema": "integrated-efficiency-recount-v2-input-manifest-v1",
        "input_main_commit": commit,
        "raw_result_files": len(raw_paths),
        "file_count": len(files),
        "files": files,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
