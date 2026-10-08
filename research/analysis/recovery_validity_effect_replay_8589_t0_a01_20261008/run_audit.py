"""One-shot raw-only auditor entrypoint for the frozen finite corpus."""

import json
import sys

from auditor import audit_formal


def main():
    with open(sys.argv[1], "r", encoding="utf-8") as stream:
        inputs = json.load(stream)
    with open(sys.argv[2], "r", encoding="utf-8") as stream:
        truth = json.load(stream)
    with open(sys.argv[3], "r", encoding="utf-8") as stream:
        raw = json.load(stream)
    result = audit_formal(inputs, truth, raw)
    rendered = json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n"
    if len(sys.argv) > 4:
        with open(sys.argv[4], "w", encoding="utf-8", newline="\n") as stream:
            stream.write(rendered)
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
