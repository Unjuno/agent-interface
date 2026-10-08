"""Run the independent raw-output reconstruction in one separate process."""

import argparse
import json
import sys
from pathlib import Path

import audit_core


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("policy_input")
    parser.add_argument("scoring_key")
    parser.add_argument("raw_output")
    parser.add_argument("score_output")
    parser.add_argument("--freeze", default=str(Path(__file__).with_name("FREEZE.json")))
    args = parser.parse_args(argv)
    try:
        root = Path(__file__).parent
        policy_bytes = Path(args.policy_input).read_bytes()
        key_bytes = Path(args.scoring_key).read_bytes()
        freeze_file = json.loads(Path(args.freeze).read_text())
        freeze = {**freeze_file, "policy_input_bytes": policy_bytes, "scoring_key_bytes": key_bytes}
        verdict = audit_core.audit(json.loads(policy_bytes), json.loads(key_bytes),
                                   json.loads(Path(args.raw_output).read_text()),
                                   json.loads(Path(args.score_output).read_text()),
                                   freeze, root)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(verdict, sort_keys=True))
    return 0 if verdict["disposition"] == "PASS_LABEL_BLIND_METHOD_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
