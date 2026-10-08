"""Verify lossless ledger and recalculate metrics; no receiver trials or DB audit."""
import hashlib
import json
import lzma
from collections import Counter
from pathlib import Path
from audit import inspect_row

HERE = Path(__file__).resolve().parent
parts = [("000", "ce75bf181bd2c42bdd2f4a48b3f594baba8cf195"),
         ("001", "7cfa696bcc5db3466c2d51360f00d1400a71fd97")]
data = b""
for name, expected in parts:
    b = (HERE / "ledger.xz.parts" / name).read_bytes()
    actual = hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()
    if actual != expected:
        raise ValueError("ledger part hash mismatch: " + name)
    data += b
if hashlib.sha256(data).hexdigest() != "7722b740a086b9342d7bec56d0a281bd60ba0e9c02b76f338e2b6cc775ec0464":
    raise ValueError("archive hash mismatch")
raw = lzma.decompress(data)
if hashlib.sha256(raw).hexdigest() != "1cbab8ee2e32f99891d66472eaf41bc940555d86bfed1208bb3ea5f93bd8ad8a":
    raise ValueError("raw ledger hash mismatch")
rows = [json.loads(line) for line in raw.splitlines()]
if len(rows) != 80:
    raise ValueError("incomplete ledger")
counts = {p: Counter() for p in ("validate_first", "outcome_first")}
for row in rows:
    counts[row["policy"]].update({"cases": 1, **inspect_row(row)})
expected = json.loads((HERE / "SUMMARY.json").read_text())["policies"]
if counts != expected:
    raise ValueError("summary disagrees with raw measurement ledger")
print(json.dumps({"status": "PASS_LEDGER_ONLY", "rows": len(rows), "policies": counts,
                  "original_database_audit": "requires full conversation ZIP"}, indent=2, sort_keys=True))
