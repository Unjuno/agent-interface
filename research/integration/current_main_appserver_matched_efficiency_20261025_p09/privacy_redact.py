"""Record privacy-only redactions and preserve before/after hashes."""

import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
PRIVATE_PATH = re.compile(r"(?i)\b[A-Z]:\\(?:[^\\/:*?\"<>|\r\n]+\\)*[^\\/:*?\"<>|\r\n]*")
SENSITIVE_KEYS = {"servername", "installationid", "authorization"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def scrub(value):
    if type(value) is dict:
        result = {}
        for key, child in value.items():
            if key.lower() in SENSITIVE_KEYS:
                result[key] = "<redacted>"
            else:
                result[key] = scrub(child)
        return result
    if type(value) is list:
        return [scrub(item) for item in value]
    if type(value) is str:
        return PRIVATE_PATH.sub("<private-path>", value)
    return value


def redact_run(run_root):
    run_root = Path(run_root)
    rows = []
    for path in sorted(run_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() in {".png", ".rgb", ".bgrx"}:
            continue
        before = path.read_bytes()
        try:
            if path.suffix.lower() == ".jsonl":
                values = [json.loads(line) for line in before.splitlines() if line]
                after = b"".join((json.dumps(scrub(row), sort_keys=True,
                    separators=(",", ":")) + "\n").encode("utf-8") for row in values)
            elif path.suffix.lower() in {".json", ".bin"}:
                value = json.loads(before)
                is_json = path.suffix.lower() == ".json"
                encoded = json.dumps(scrub(value), indent=2 if is_json else None,
                                     sort_keys=True,
                                     separators=None if is_json else (",", ":"))
                after = (encoded + ("\n" if is_json else "")).encode("utf-8")
            else:
                text = before.decode("utf-8")
                after = PRIVATE_PATH.sub("<private-path>", text).encode("utf-8")
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        if before != after:
            path.write_bytes(after)
            rows.append({"path": path.relative_to(run_root).as_posix(),
                         "original_sha256": sha(before),
                         "redacted_sha256": sha(after),
                         "fields": ["serverName", "installationId", "authorization",
                                    "Windows absolute paths"]})
    report = {
        "schema": "agent-interface/appserver-visual-grounding-p09-redactions-v1",
        "scope": "privacy-only; original and sanitized SHA-256 retained",
        "redactions": rows,
    }
    (run_root / "REDACTIONS.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n")
    return report


if __name__ == "__main__":
    print(json.dumps(redact_run(ROOT / "run"), indent=2, sort_keys=True))
