"""One measurement stage: stage immutable source, run one child, retain outputs."""
from __future__ import annotations

import hashlib
import json
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

EXPECTED = {
    "fixture.json": "374a6136bc5a0b5cfe39cce915625505c6a56cade870b20fb2e749aa4e7fe9d7",
    "candidate.py": "972b711c3a6c57e09d48652884c96491a70c5ef7ea183e96b052692c6bddee0a",
    "runner.py": "31a13ac9dee59d4d7d58fa7cb5c94afc9418477ca22d644459d6d01acf76ccdc",
    "audit.py": "81fe3dc715afb4f9e2039a513157f608fddfef950643e0bdd6431350f3a4ad4d",
}
CANDIDATE_OUTPUTS = ("formal_raw.jsonl", "sticky_baseline.jsonl", "age_baseline.jsonl")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_verified(src: Path, dst: Path, expected: str | None = None) -> str:
    digest = sha256(src)
    if expected is not None and digest != expected:
        raise ValueError(f"source_hash_mismatch:{src.name}:{digest}:{expected}")
    with src.open("rb") as source_stream, dst.open("xb") as output:
        shutil.copyfileobj(source_stream, output)
    copied = sha256(dst)
    if copied != digest:
        raise ValueError(f"staged_hash_mismatch:{src.name}")
    return digest


def main() -> int:
    if len(sys.argv) not in (4, 5):
        print("usage: stage_and_run.py candidate|audit SOURCE OUTPUT [INPUT]", file=sys.stderr)
        return 2
    mode, source_arg, output_arg = sys.argv[1:4]
    if mode not in {"candidate", "audit"} or (mode == "audit") != (len(sys.argv) == 5):
        print("invalid_mode_or_input", file=sys.stderr)
        return 2
    source, output = Path(source_arg), Path(output_arg)
    input_dir = Path(sys.argv[4]) if len(sys.argv) == 5 else None
    if not source.is_dir() or not output.is_dir() or any(output.iterdir()):
        print("source_or_empty_output_gate_failed", file=sys.stderr)
        return 70
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="wsl2-wslc-6389-") as tmp:
        work = Path(tmp)
        names = ("fixture.json", "candidate.py", "runner.py") if mode == "candidate" else ("fixture.json", "audit.py")
        copied = {name: copy_verified(source / name, work / name, EXPECTED[name]) for name in names}
        if mode == "audit":
            assert input_dir is not None
            for name in CANDIDATE_OUTPUTS:
                copy_verified(input_dir / name, work / name)
            command = [sys.executable, "-B", "audit.py"]
            outputs = ("audit.json",)
        else:
            command = [sys.executable, "-B", "runner.py"]
            outputs = CANDIDATE_OUTPUTS
        child = subprocess.run(command, cwd=work, text=True, capture_output=True, check=False)
        out_hashes = {}
        for name in outputs:
            path = work / name
            if path.is_file():
                copy_verified(path, output / name)
                out_hashes[name] = sha256(output / name)
        receipt = {
            "mode": mode,
            "runtime_python": sys.version,
            "platform": platform.platform(),
            "staged_source_sha256": copied,
            "child_command": command,
            "child_exit": child.returncode,
            "child_stdout": child.stdout,
            "child_stderr": child.stderr,
            "output_sha256": out_hashes,
            "stage_elapsed_seconds": time.perf_counter() - started,
        }
        with (output / "receipt.json").open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(receipt, stream, sort_keys=True, indent=2)
            stream.write("\n")
        print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
        return child.returncode


if __name__ == "__main__":
    raise SystemExit(main())
