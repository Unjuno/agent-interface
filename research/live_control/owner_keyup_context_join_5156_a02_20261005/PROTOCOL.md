# #59/#5156 per-admission to owner-key-up context join A02

## H / T / D / C / U

**H.** The A02 per-key owner KeyRelease/XSync receipt can pass through current-main `doom_retained_input_backend_v4` and stay bound to that backend's `id`, `step`, admission position, and release key for a single key, reverse-order multi-key release, and repeated same-key cycles. The join preserves the backend's existing post-batch outcome and adds no X11 query or XSync between requests.

**T.** This is a new composition successor to A01. One fake-Xlib candidate uses the exact current-main backend v4 and frozen owner/wrapper candidate sources for three cases: one explicit key up, A+B admitted then B+A released, and C down/up repeated twice. A raw-only auditor reconstructs each case's interleaved operation sequence, admission/release context, nested owner receipt, terminal keymap, and eight corruption controls. A01's candidate and auditor are not rerun or reclassified.

**D.** `PASS_OWNER_KEYUP_CONTEXT_JOIN_SCOPED` requires candidate/auditor exits 0; exact source/image hashes; each expected admission and release exactly once with correct case/key/step/admission position; unique identity-bound nested owner receipt IDs; `caller_start <= owner_keyup_start <= owner_sync_return <= caller_return`; exact per-case XTest/XSync sequence; preserved true existing owner batch outcome and false physical authority; empty fake keymap after independently verified owner cleanup; and rejection of all eight corruptions. Otherwise FAIL/STOP.

## Frozen sources and execution envelope

- Main intake is `ad7a6d5a6dcc0d990af5a2beef32d59b31fbaa04`.
- Current-main blobs: InputOwner v10 `341b3c01649943ddaad5f28431a792c4889cc36e`; transition wrapper v3 `99dfc7c9907b018e7473bc2ba8a7393a5b221f51`; retained backend v4 `81484e6146bb8b93a007f338df3e504620924a45`.
- A02 owner/wrapper candidate files are copied byte-for-byte from their frozen A02 package. Candidate and auditor, baseline, fake-Xlib, and protocol hashes are fixed in `FREEZE.json` before execution.
- Use cached WSLc `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016` (image ID `sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364`), linux/amd64, Python 3.12.15. One CPU, no network, read-only source, separate output, no memory cap, no pull, no retries; candidate and auditor each run once in separate disposable containers.
- A01's frozen auditor grouped admissions before releases and falsely rejected the interleaved repeated-cycle call sequence. A02 fixes the per-case expected sequence and adds a single-key case. A01's exit-1 audit remains historical.

**C.** Fake Xlib and the stubbed outer executor do not model a real X server, OS scheduling, application consumption, or game behavior. The bounded cases verify serialization and identity only.

**U.** No live X11, physical input, MAP01, model, useful feedback, recovery, safety rate, task effect, latency, or product-readiness claim. The live #59 threat-exposure lane remains separately gated and unassigned.
