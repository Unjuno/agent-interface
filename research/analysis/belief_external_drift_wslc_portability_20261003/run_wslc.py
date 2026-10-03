"""Stage and invoke the frozen #5368 source inside one disposable WSLc run."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


SOURCE = Path("/source")
INPUT = Path("/input")
OUTPUT = Path("/out")
SOURCE_HASHES = {
    "fixture.json": "cbdcf96771291e4889fbb1d8b4777f0210ddc9f64457ee48e5fec31aeb8b2420",
    "candidate.py": "51646ed62c3eb47c7bb38b8023ebe1fcc3cdf809002e09ee201427bfe6364a4b",
    "runner.py": "72b9424e267514cf2f1e4f6fbe91a0b73e92dca8af694bd22c813c1006c22aea",
    "audit.py": "eede51ff282657cea78569d70cbf2f1efa29f0add6500ab046b15b289aa7c77d",
}
CANDIDATE_OUTPUTS = ("formal_raw.jsonl", "sticky_baseline.jsonl", "age_baseline.jsonl")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_source(path: Path, name: str) -> str:
    actual = sha256(path)
    expected = SOURCE_HASHES[name]
    if actual != expected:
        raise ValueError(f"source_hash_mismatch:{name}:{actual}:{expected}")
    return actual


def copy_exclusive(source: Path, destination: Path) -> str:
    with source.open("rb") as src, destination.open("xb") as dst:
        shutil.copyfileobj(src, dst)
    return sha256(destination)


def stage_source(work: Path, names: tuple[str, ...]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for name in names:
        source = SOURCE / name
        hashes[name] = verify_source(source, name)
        staged = work / name
        shutil.copyfile(source, staged)
        if verify_source(staged, name) != hashes[name]:
            raise ValueError(f"staged_source_hash_mismatch:{name}")
    return hashes


def copy_outputs(work: Path, names: tuple[str, ...]) -> list[dict[str, object]]:
    if not OUTPUT.is_dir():
        raise FileNotFoundError("output_mount_missing")
    result: list[dict[str, object]] = []
    for name in names:
        source = work / name
        if not source.is_file():
            continue
        digest = copy_exclusive(source, OUTPUT / name)
        result.append({"name": name, "bytes": source.stat().st_size, "sha256": digest})
    return result


def invoke(mode: str) -> int:
    if not OUTPUT.is_dir() or any(OUTPUT.iterdir()):
        raise FileExistsError("output_mount_must_be_new_and_empty")
    if mode not in {"candidate", "audit"}:
        raise ValueError("mode_must_be_candidate_or_audit")

    with tempfile.TemporaryDirectory(prefix="belief-external-wslc-") as temp:
        work = Path(temp)
        if mode == "candidate":
            staged_hashes = stage_source(work, ("fixture.json", "candidate.py", "runner.py"))
            command = [sys.executable, "-B", "runner.py"]
            input_hashes: dict[str, str] = {}
        else:
            staged_hashes = stage_source(work, ("fixture.json", "audit.py"))
            input_hashes = {}
            for name in CANDIDATE_OUTPUTS:
                source = INPUT / name
                if not source.is_file():
                    raise FileNotFoundError(f"candidate_output_missing:{name}")
                shutil.copyfile(source, work / name)
                input_hashes[name] = sha256(work / name)
            command = [sys.executable, "-B", "audit.py"]

        child = subprocess.run(command, cwd=work, check=False, capture_output=True, text=True)
        output_names = CANDIDATE_OUTPUTS if mode == "candidate" else ("audit.json",)
        artifacts = copy_outputs(work, output_names)
        audit_status = None
        if mode == "audit" and (work / "audit.json").is_file():
            audit_status = json.loads((work / "audit.json").read_text(encoding="utf-8"))["status"]

        receipt = {
            "mode": mode,
            "staged_source_sha256": staged_hashes,
            "input_sha256": input_hashes,
            "child_returncode": child.returncode,
            "child_stdout": child.stdout,
            "child_stderr": child.stderr,
            "audit_status": audit_status,
            "outputs": artifacts,
        }
        print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
        return child.returncode


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: run_wslc.py candidate|audit", file=sys.stderr)
        return 2
    try:
        return invoke(args[0])
    except Exception as exc:  # preserve one bounded invocation; never retry here
        print(json.dumps({"wrapper_error": type(exc).__name__, "message": str(exc)}, sort_keys=True), file=sys.stderr)
        return 70


if __name__ == "__main__":
    raise SystemExit(main())
