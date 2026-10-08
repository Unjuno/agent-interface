# Audit mutation effectiveness probe — Issue #4889

## H / T / D / C / U

- **H:** choosing a distinct `linearizations=0` mutation for the `OPEN,CLOSE` two-event row makes the control effective, and an exact expected-row comparison rejects all eight copied-record corruptions.
- **T:** one 3 KB, Python-standard-library probe ran in the already-cached `python:3.12-slim` image, pinned by digest, with network disabled, read-only root/source, 0.25 CPU, 384 MiB RAM, and 64 PIDs. It models only `OPEN`/`CLOSE`; no formal Issue #4889 rows or runner/auditor were loaded or rerun.
- **D:** `CONSTRUCTION_ONLY_PASS`: 8/8 mutations changed the expected record and were rejected; dropping the `OPEN→CLOSE` dependency yielded one divergent order. Runner exit 0. This confirms the control-value selection defect only.
- **C:** independent minimal reducer and exact whole-record comparator; same two-event scoped semantics as the motivating no-op.
- **U:** not an independent audit of #4889's 11,111 rows, does not repair PR #4892's auditor, and cannot change `HOLD_AUDIT_CONTROL_HARNESS`. No production, runtime, replay-format, or performance claim.

## Provenance

- Lineage: Issue #4889; retained formal result and HOLD in PR #4892 remain unchanged.
- Local image: `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9` (`linux/amd64`).
- Invocation: `docker run --rm --pull=never --network none --cpus=0.25 --memory=384m --pids-limit=64 --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m ... python -S -B probe.py`.
- Source: `probe.py`; SHA-256 `a406db27d12ecba2dec76cf7adddb557b7ea6dbea041e864352b0928b59a6c96`.
- Formal rows: 0. GPU: not used. Existing X11 and Ollama containers were left running and untouched.

This is a diagnostic construction note, not the successor formal allocation proposed in #4889's decision section. Do not use its PASS to relabel or close the prior HOLD.
