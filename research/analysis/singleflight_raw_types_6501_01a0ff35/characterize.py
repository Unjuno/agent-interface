"""Supplemental audit of retained raw; never invokes the scheduler candidate."""
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform

import legacy_auditor
import auditor_v2

ROOT = Path(__file__).resolve().parent


def main():
    started = datetime.now(timezone.utc).isoformat()
    raw_bytes = (ROOT / "retained-raw.json").read_bytes()
    fixture_bytes = (ROOT / "fixtures.json").read_bytes()
    raw, fixtures = json.loads(raw_bytes), json.loads(fixture_bytes)
    digest = hashlib.sha256(fixture_bytes).hexdigest()
    # Independent traversal from the unittest implementation.
    pending = [((), raw)]
    rows = []
    while pending:
        path, value = pending.pop()
        if isinstance(value, dict):
            pending.extend((path + (key,), child) for key, child in sorted(value.items(), reverse=True))
        elif type(value) is int:
            replacements = [float(value)]
            if value in (0, 1):
                replacements.append(bool(value))
            for replacement in replacements:
                variant = copy.deepcopy(raw)
                parent = variant
                for key in path[:-1]:
                    parent = parent[key]
                parent[path[-1]] = replacement
                encoded = json.dumps(variant, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
                rows.append({
                    "path": list(path), "original": value,
                    "replacement": replacement, "replacement_type": type(replacement).__name__,
                    "variant_sha256": hashlib.sha256(encoded).hexdigest(),
                    "legacy": legacy_auditor.audit(variant, fixtures, digest),
                    "strict": auditor_v2.audit(variant, fixtures, digest),
                })
    result = {
        "schema": "singleflight-retained-json-types-v1",
        "started_utc": started, "ended_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(), "os": platform.platform(),
        "original_raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "fixture_sha256": digest,
        "original_legacy": legacy_auditor.audit(raw, fixtures, digest),
        "original_strict": auditor_v2.audit(raw, fixtures, digest),
        "mutations": rows,
    }
    with (ROOT / "matrix.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"mutations": len(rows), "legacy_accepted": sum(r["legacy"]["status"] == "PASS_METHOD_SCOPED" for r in rows), "strict_rejected": sum(r["strict"]["status"] == "FAIL_RAW_AUDIT" for r in rows)}))


if __name__ == "__main__":
    main()
