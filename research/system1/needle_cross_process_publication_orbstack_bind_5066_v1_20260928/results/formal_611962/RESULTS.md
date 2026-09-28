# Formal run 01 — STOP (auditor/provenance gate)

Allocation: `needle-publication-orbstack-bind-5066-20260928-01`\
Issue: #5073\
Frozen main: `611962d32477f8a86096431227a819418ceef994`\
Frozen source commit: `11bbc1aaab9993a58f4cb1eb861b7c6e979c2e90`\
Image: `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e` (`linux/arm64`)\
Context: OrbStack; host: macOS arm64

## Invocation and execution

One frozen formal invocation and the planned separate raw-only audit were run. No retry was made.

```text
python3 -B research/system1/needle_cross_process_publication_orbstack_bind_5066_v1_20260928/formal.py \
  --output /tmp/needle-publication-5073-611962-one-shot \
  --slot-release-5074-comment-id 5861415294 \
  --queue-release-5085-comment-id 5861416228
```

Formal container `c34dca2ab558749bef8b448e7652ada02866f30f8eb54d038c6ba1c7b3fe2906` exited 0 and emitted `RAW_CAPTURED`. Audit container `2c076d5e614dcbeeb8315253218c9c2c326172497143f9cf604c63b1f73db6b4` exited 1. Both used the pinned image, read-only `/src`, dedicated `/out`, network none, and the frozen CPU/memory/PID limits. Exact invocation, inspected container state/mounts, stdout/stderr, raw data, auditor output, work files, and manifest are retained alongside this report.

## Raw observations (descriptive; not accepted as a formal PASS)

- 28 atomic concurrent rows, 28 fresh-path post-publication rows, and 28 unsafe-arm rows were captured.
- The runner-reported atomic held-descriptor and post-path rows were all digest-valid; post reads targeted the expected new generation.
- All 28 unsafe partial reads were invalid and all 28 completion reads were valid.
- The audit output reports all ten configured corruption controls rejected.
- Raw JSON SHA-256: `33e39cf590e06f99e6c99066af41d9b4e1e2b3899a6df4fc09c818c6e06a4a4e`.

These are observations from the retained runner output. Since the frozen independent audit failed its provenance gate, they do not establish the preregistered scientific decision.

## Audit failure and disposition

Audit status: `STOP_PROVENANCE_ENVIRONMENT_OR_AUDIT`; errors:

```text
raw_platform_prefix
receipt_binding_docker_argv
source_missing_PLAN.md
source_missing_audit.py
source_missing_formal.py
source_missing_protocol.py
source_missing_runner.py
source_missing_test_construction.py
```

The audit code expects the raw platform string to start with `linux/arm64`, although the retained raw field is exactly `linux/arm64`. It also compares a top-level raw `docker_argv` field that the runner does not emit (the exact argv is in `invocation_receipt.json`), and resolves manifest source names at `/src/<name>` although the experiment files are under `/src/research/system1/needle_cross_process_publication_orbstack_bind_5066_v1_20260928/<name>`. These are auditor/receipt-contract mismatches, not evidence of an atomic-publication counterexample. They invalidate this run's formal acceptance gate.

Decision: formal run completed, but overall experiment disposition is **STOP**, not PASS or FAIL. The one formal allocation and its one planned audit are consumed; no same-allocation rerun, patched-auditor replay, replacement, or result-driven retuning is authorized. Any corrected scientific follow-up must be an explicitly new successor allocation preserving this result unchanged.
