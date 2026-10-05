"""Read-only CLI for the retained A03 audit; results are emitted to stdout."""
from __future__ import annotations

import json

from audit import audit


def main() -> int:
    result = audit()
    print(json.dumps(result, sort_keys=True))
    return int(bool(result["errors"]))


if __name__ == "__main__":
    raise SystemExit(main())
