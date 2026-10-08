import argparse
import json
from pathlib import Path

from candidate import run
from fixtures import build_fixtures


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    rows = run(build_fixtures())
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"rows": len(rows), "output": str(destination)}, sort_keys=True))


if __name__ == "__main__":
    main()
