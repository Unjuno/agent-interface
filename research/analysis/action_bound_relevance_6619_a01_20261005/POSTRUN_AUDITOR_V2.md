# Versioned read-only auditor repair

The frozen auditor `audit.py` was invoked once after the candidate completed. It exited 1 before reading any case rows because it looked up `FREEZE.json["sha256"]`, while the frozen schema records package pins under `source_sha256`. The original source, hash, traceback, empty stdout file and exit record are preserved unchanged.

`audit_v2.py` corrects only the frozen-key lookup and additionally checks the frozen repository-context hashes. It is a separately versioned raw-only audit of the already retained `candidate.raw.json`; it does not import or invoke `candidate.py`, alter inputs, thresholds or decision rules, or replace the first candidate outcome. It will be invoked at most once. Its outcome cannot make the original auditor pass retroactively.
