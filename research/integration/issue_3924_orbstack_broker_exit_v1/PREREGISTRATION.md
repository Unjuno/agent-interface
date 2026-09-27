# Issue #3924 OrbStack broker exit contract v1

## Scope

This is an additive, isolated experiment against the exact broker source at the recorded main commit. No shared runtime code is changed. It uses only a deterministic fake executable and an OrbStack container with `--network none`; no model, provider, GUI, credential, or task-effect call is permitted.

## Fixed cases

1. Baseline source + fake child exit 0: record the broker process status and raw receipt/response.
2. Isolated candidate differing only by preserving integer zero: fake child exit 0 must make the broker exit 0.
3. Candidate + fake child exit 7: broker exits 7 and receipt records 7.
4. Candidate + bounded fake child sleep: typed `HOST_BROKER_SUBPROCESS_TIMEOUT`, nonzero broker exit.
5. Candidate + nonexistent executable: typed `HOST_BROKER_EXECUTABLE_UNAVAILABLE`, nonzero broker exit.
6. Candidate + malformed request: fail closed; fake invocation count unchanged.
7. Candidate + two queued requests with `--once`: exactly one request gets response/receipt and the process exits according to that handled child.

All cases use fresh IPC directories. Preserve stdout, stderr, request bytes, response bytes, broker receipts, fake argv/call log, process statuses, container identity, and SHA-256 manifest. Run the independent audit only after the runner has finished. No retries or parameter changes after formal execution begins.

## Decision

PASS only if every fixed expectation holds, raw artifacts reconcile, and independent audit reports zero errors. A deterministic complete mismatch is FAIL. Missing source/runtime/provenance/raw evidence is STOP, not semantic evidence.

## Candidate construction

The candidate is the pinned main broker source with exactly one change: `return broker.get("returncode") or 1` becomes `return broker["returncode"] if broker.get("returncode") is not None else 1`. It exists only in the isolated evidence directory; shared source remains unchanged.
