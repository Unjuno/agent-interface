"""One-shot wrapper for one candidate and one raw-only auditor; no retry path."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


def _write(path: Path, data: bytes) -> None:
    path.write_bytes(data)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: run_once.py OUTPUT_DIRECTORY")
    out = Path(sys.argv[1])
    if out.exists() and any(out.iterdir()):
        raise SystemExit("STOP_OUTPUT_NOT_EMPTY")
    out.mkdir(parents=True, exist_ok=True)
    src = Path(__file__).resolve().parent

    candidate = subprocess.run(
        [sys.executable, "-B", str(src / "candidate.py")],
        cwd=src,
        capture_output=True,
        check=False,
    )
    _write(out / "candidate.raw.json", candidate.stdout)
    _write(out / "candidate.stderr", candidate.stderr)
    _write(out / "candidate.exit", f"{candidate.returncode}\n".encode("ascii"))
    is_one_json_line = (
        candidate.stdout.endswith(bytes((10,)))
        and candidate.stdout.count(bytes((10,))) == 1
    )
    audit = None
    if candidate.returncode == 0 and is_one_json_line:
        json.loads(candidate.stdout.decode("utf-8"))
        audit = subprocess.run(
            [sys.executable, "-B", str(src / "auditor.py"),
             str(src / "fixture.json"), str(out / "candidate.raw.json")],
            cwd=src,
            capture_output=True,
            check=False,
        )
        _write(out / "auditor.stdout.json", audit.stdout)
        _write(out / "auditor.stderr", audit.stderr)
        _write(out / "auditor.exit", f"{audit.returncode}\n".encode("ascii"))

    manifest = {
        "allocation_id": "TYPED-QUANTITY-EFFECT-6524-T0-20261002-01",
        "candidate_invocations": 1,
        "candidate_exit": candidate.returncode,
        "candidate_stdout_bytes": len(candidate.stdout),
        "candidate_stdout_sha256": _sha(candidate.stdout),
        "candidate_newlines": candidate.stdout.count(bytes((10,))),
        "candidate_single_json_line": is_one_json_line,
        "auditor_invocations": int(audit is not None),
        "auditor_exit": audit.returncode if audit is not None else None,
        "auditor_stdout_sha256": _sha(audit.stdout) if audit is not None else None,
        "retry_count": 0,
    }
    encoded = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode("utf-8")
    _write(out / "RUN_MANIFEST.json", encoded)
    print(encoded.decode("utf-8"), end="")
    if candidate.returncode != 0 or not is_one_json_line:
        return 20
    return audit.returncode


if __name__ == "__main__":
    raise SystemExit(main())
