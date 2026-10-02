import json
import sys

from candidate import evaluate_trace
from fixtures import MODES, TRACES


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: run_candidate.py RAW.jsonl")
    with open(sys.argv[1], "x", encoding="utf-8", newline="\n") as stream:
        for trace in TRACES.values():
            for row in evaluate_trace(trace, MODES):
                stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
