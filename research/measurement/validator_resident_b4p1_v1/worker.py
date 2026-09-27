"""Finite, serial research entry to unchanged inspect_file; no result cache."""
import importlib.util
import json
from pathlib import Path
import sys


def main():
    root = Path(__file__).resolve().parent / 'baseline'
    sys.path.insert(0, str(root))
    spec = importlib.util.spec_from_file_location('static_validator_b4p1', root / 'validator.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for index in range(64):
        line = sys.stdin.buffer.readline(4097)
        if not line:
            return 0
        if len(line) > 4096 or not line.endswith(b'\n'):
            return 3
        path = json.loads(line)
        if not isinstance(path, str) or len(path) > 1024:
            return 3
        report = module.inspect_file(Path(path))
        print(json.dumps(report, ensure_ascii=True, sort_keys=True), flush=True)
    return 3  # This finite experiment never sends more than 32 requests.


if __name__ == '__main__':
    raise SystemExit(main())
