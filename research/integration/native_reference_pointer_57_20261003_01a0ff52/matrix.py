"""Input-free engineering comparison of exact baseline and repaired source."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import platform
import time
import types


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("fixtures", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source = args.source.read_bytes()
    fixtures = args.fixtures.read_bytes()
    module = types.ModuleType("isolated_receipt_references")
    exec(compile(source, str(args.source), "exec"), module.__dict__)
    started = time.time_ns()
    rows = []
    for fixture in json.loads(fixtures):
        value = copy.deepcopy(fixture["view"])
        before = copy.deepcopy(value)
        try:
            output = module.expand_native_receipt(value)
            result = {"status": "returned", "output": output}
        except Exception as error:
            result = {"status": "exception", "exception": type(error).__name__}
        rows.append({"id": fixture["id"], "input_unchanged": value == before, **result})
    result = {"format": "native-reference-boundary-v1", "rows": rows,
              "source_sha256": hashlib.sha256(source).hexdigest(),
              "fixture_sha256": hashlib.sha256(fixtures).hexdigest(),
              "started_utc_ns": started, "ended_utc_ns": time.time_ns(),
              "environment": {"python": platform.python_version(),
                              "platform": platform.platform(),
                              "machine": platform.machine()},
              "scope": "ordinary input-free engineering; no formal allocation"}
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"rows": len(rows), "source_sha256": result["source_sha256"]}))


if __name__ == "__main__":
    main()
