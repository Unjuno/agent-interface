"""Independent check of the frozen/candidate terminal outcomes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
LIVE = HERE.parents[1] / "live_control"
RUN = json.loads((HERE / "RUN.json").read_text(encoding="utf-8"))
PAYLOAD = RUN["custody_payload"]
baseline_terminal = RUN["baseline"]["terminal"]
candidate_terminal = RUN["candidate"]["terminal"]
checks = {
    "freeze_bytes_match_run_record": hashlib.sha256((HERE / "FREEZE.json").read_bytes()).hexdigest() == RUN["freeze_sha256"],
    "frozen_baseline_source_matches_record": hashlib.sha256((HERE / "baseline_executor_v13.py").read_bytes()).hexdigest() == RUN["baseline_source_sha256"],
    "candidate_source_matches_record": hashlib.sha256((LIVE / "executor_v13.py").read_bytes()).hexdigest() == RUN["candidate_source_sha256"],
    "baseline_emits_false_completed_status": baseline_terminal.get("status") == "completed",
    "baseline_omits_custody_receipt": baseline_terminal.get("release_batch_publication") is None,
    "baseline_keyboard_interrupt_escapes_worker": any(error["exception_type"] == "KeyboardInterrupt" for error in RUN["baseline"]["thread_errors"]),
    "candidate_fails_terminal_closed": candidate_terminal.get("status") == "failed",
    "candidate_preserves_exact_custody": candidate_terminal.get("release_batch_publication") == PAYLOAD,
    "candidate_custody_identifier_matches_terminal_id": candidate_terminal.get("release_batch_publication", {}).get("identifier") == candidate_terminal.get("id"),
    "candidate_reports_exception": "KeyboardInterrupt" in str(candidate_terminal.get("error")),
    "candidate_does_not_emit_completed_event": not any(event.get("event") == "completed" for event in RUN["candidate"]["events"]),
    "candidate_worker_has_no_uncaught_exception": not RUN["candidate"]["thread_errors"],
}
report = {
    "experiment_id": RUN["experiment_id"],
    "independent_audit": "PASS_BASEEXCEPTION_CUSTODY_FAIL_CLOSED" if all(checks.values()) else "FAIL_AUDIT",
    "checks": checks,
    "baseline_terminal": baseline_terminal,
    "candidate_terminal": candidate_terminal,
    "scope": "Synthetic ExecutorV13 boundary only; no physical release, task effect, or live-control claim.",
}
(HERE / "AUDIT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2, sort_keys=True))
raise SystemExit(0 if all(checks.values()) else 1)
