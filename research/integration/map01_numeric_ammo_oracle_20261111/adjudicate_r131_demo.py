"""Run the retained-only R131 MAP01 expiry/demo adjudicator."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from .gzdoom_expiry_adjudication import adjudicate_expiry_demo
except ImportError:
    from gzdoom_expiry_adjudication import adjudicate_expiry_demo


def adjudicate_trial_directory(trial: Path) -> dict:
    trial = Path(trial)
    submission = json.loads((trial / "action-submission.json").read_text(
        encoding="utf-8"))
    program = submission["program"]
    expiry = program["authority"]["expires_at_ns"]
    raw_result = json.loads((trial / "terminal-interface-results-raw.json").read_text(
        encoding="utf-8"))
    samples = json.loads((trial / "expiry-boundary-key-samples.json").read_text(
        encoding="utf-8"))
    if type(samples) is not dict or type(samples.get("samples")) is not list:
        raise ValueError("expiry boundary sample receipt has an invalid shape")
    action = raw_result.get("action")
    if type(action) is not dict:
        raise ValueError("terminal public action row is missing")
    result = adjudicate_expiry_demo(
        demo_bytes=(trial / "r131.lmp").read_bytes(),
        key_samples=samples["samples"], lease_expiry_ns=expiry,
        public_result=raw_result,
        expected_call_id=raw_result.get("call_id"),
        expected_operation_id=action.get("operation_id"),
        expected_generation=action.get("target_generation"))
    output = trial / "application-demo-adjudication.json"
    if output.exists():
        raise FileExistsError(output)
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
        encoding="utf-8", newline="\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("trial_directory", type=Path)
    args = parser.parse_args()
    print(json.dumps(adjudicate_trial_directory(args.trial_directory),
        sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
