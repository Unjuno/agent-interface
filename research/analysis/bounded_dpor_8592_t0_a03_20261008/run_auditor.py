"""Verify the frozen package and independently audit candidate raw output once."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from auditor import audit
from runner_utils import verify_manifest, write_json_once


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    package = Path(__file__).resolve().parent
    manifest = json.loads((package / "FREEZE.json").read_text(encoding="utf-8"))
    verify_manifest(package, {"files": manifest["all_files"]})
    public = json.loads((package / "input.json").read_text(encoding="utf-8"))
    truth = json.loads((package / "truth.json").read_text(encoding="utf-8"))
    raw = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    result = audit(public, truth, raw)
    write_json_once(args.output, result)
    return 0 if result["status"] == "PASS_DPOR_METHOD_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
