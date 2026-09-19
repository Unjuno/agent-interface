"""Preserve the first client-wait allocation as an evidence-retention failure."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]
ROOT = REPO / "results-local/live_control/release-client-wait-live-01"
PREREG = HERE / "release_client_wait_live_v1_prereg.json"
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    plan, report = read(PREREG), read(ROOT / "report.json")
    stderr = (ROOT / "audit-stderr.txt").read_text(encoding="utf-8")
    evidence = {
        "frozen_sources": all(sha(REPO / name) == digest
                              for name, digest in plan["source_sha256"].items()),
        "runner_checks_passed": report["passed"] is True and all(report["checks"].values()),
        "audit_failed": (ROOT / "audit-exit-code.txt").read_text().strip() == "1",
        "missing_server_receipt_exposed": "KeyError: 'received_ns'" in stderr,
        "request_receipts_not_retained": all("received_ns" not in client
            for client in report["clients"].values()),
        "same_stream_boundaries_retained":
            report["clients"]["early"]["reply"]["records"][-1]["event"] == "input_released" and
            report["clients"]["terminal"]["reply"]["records"][-1]["event"] == "terminal",
        "wait_difference_retained": report["metrics_ms"]["early_client_wait_advantage_ms"] == 110.444045,
        "zero_model_retry_cancel": report["model_calls"] == report["retry_count"] == 0,
    }
    if not all(evidence.values()): raise RuntimeError(evidence)
    failure = {"allocation_id": plan["allocation_id"], "allocation_passed": False,
        "runner_reported_pass": True, "independent_audit_exit": 1,
        "failure_class": "server_request_registration_receipt_not_serialized",
        "failure": "the live runner checked both socket reads were registered before focus transfer, but did not retain the server request receipts; the frozen independent audit requires received_ns and crashes, so the preregistered ordering cannot be independently reproduced",
        "evidence": evidence, "metrics_ms": report["metrics_ms"],
        "descriptive_result": "same-stream early client returned 110.444045 ms before terminal-only client, but this is not promoted because the both-waiting precondition lacks retained independent evidence",
        "repair_candidate": "version the runner and audit; persist the exact server request receipt list before focus transfer, bind request IDs, and audit those retained timestamps; do not rerun this allocation",
        "limits": "posthoc analysis of one no-model pointer/client run; missing registration receipts cannot be reconstructed from client start timestamps or the runner boolean"}
    (ROOT / "failure.json").write_text(json.dumps(failure, indent=2) + "\n")
    print(json.dumps({"allocation_passed": False, "failure_class": failure["failure_class"],
                      "metrics_ms": failure["metrics_ms"]}, indent=2))

if __name__ == "__main__": main()
