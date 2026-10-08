"""Verify the frozen package and create the candidate raw output once."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from candidate import run
from runner_utils import verify_manifest, write_json_once


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    package = Path(__file__).resolve().parent
    manifest = json.loads((package / "CANDIDATE_FREEZE.json").read_text(encoding="utf-8"))
    verify_manifest(package, manifest)
    public = json.loads((package / "input.json").read_text(encoding="utf-8"))
    write_json_once(args.output, run(public))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
