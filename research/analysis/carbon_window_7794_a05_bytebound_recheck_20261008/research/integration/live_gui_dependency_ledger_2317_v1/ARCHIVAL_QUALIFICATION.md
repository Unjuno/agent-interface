# Freeze-only archival qualification — Issue #2317

This preserves the four exact branch-only files from `research/live-gui-dependency-ledger-2317-20260922` at head `fd6204c20deb5bb94bbe0d301e5c4d0583d69092`. The original FREEZE Git blob is `86743f6603ef1324d108656474edc32acf1b85d2`; the original branch history is retained at `archive/recovered/live-gui-dependency-ledger-2317-20260922`.

## H/T/D/C/U

- **H:** retain the 36-case design, environment and source hash commitments for the live GUI dependency-ledger question.
- **T:** the remote branch contains only BATCH_PLAN.json, ENVIRONMENT.json, FREEZE.json and PLAN.md; no runner/auditor source, formal raw batches, process receipts, or audit/control outputs. The Issue reports a scoped 36-case PASS, but exact-byte repository reconstruction is unavailable. No rerun was performed.
- **D:** `HOLD_SOURCE_AND_RAW_UNAVAILABLE`; the Issue-reported PASS remains historical, not independently reproduced or promoted.
- **C:** a plan and source hashes identify missing bytes but do not supply them.
- **U:** executable sources and the 36-case raw/audit corpus remain unavailable. Issue #2317 stays open.
