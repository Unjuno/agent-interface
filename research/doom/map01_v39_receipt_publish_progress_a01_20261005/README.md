# V39 per-row release receipt publication A01

## H / T / D / C / U

**H:** Per-row progress plus stable release IDs and an idempotent sink recovers receipt rows across an emit-before-append failure and an append-then-raise lost acknowledgement without omission or duplicate storage.

**T:** Run candidate.py once against three fixed rows and three deterministic schedules. The owner cleanup source context is #7805 commit e00c7f5e5c949095d40ade458355e55ea5990b9d, blob e7889a7a34fe76df5f230d4108a77055b105a680; current main at freeze is 402c7d1b5147b2a905098f082233db60a47d68db. Run candidate and independent auditor in separate no-network WSLc containers from the pinned local python:3.12-slim image. Candidate writes only RAW.json to the separate output mount.

**D:** PASS only if all keyed receipts and payloads are preserved exactly once for normal, pre-append failure/retry, and append-then-raise/retry with the idempotent sink, the already-acknowledged first row is not re-appended, and controls fail closed. A non-idempotent sink that duplicates after lost acknowledgement is UNKNOWN, not a pass.

**C:** A production sink may lack idempotent write support; then exactly-once publication is not achievable from this in-memory cursor alone. This protocol test does not verify the actual executor event sink.

**U:** Synthetic publisher/sink protocol only. It does not address mutable owner record completion, owner hold retirement, terminal barriers, X11, GUI/game, model, useful feedback, recovery, or live allocation. It neither repairs #7805 nor closes #59.

Candidate writes RAW.json only to the separate output mount. Auditor reads it without mutation. No retries.
