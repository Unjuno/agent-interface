# V39 adapter-linked admission receipt integration A23

## Test-first record

A22 is the RED control: exact current-main V39 backend raw/publish path plus current-main V4/V12 owner on Xvfb observed the event pair and keymap down/up, but the unchanged PR #8857 analyzer rejected its emitted records (`unmatched_admission_count=1`, `invalid_release_count=1`). A22 used no patch.

A23 tests one minimal adapter change: retain the exact admission row emitted by the backend; at release batch publication, join it only when the unique row matches key, owner id, intent token and deadline and its admission/ack/release timestamps are ordered within the lease. Attach the exact row and an explicit validity result to the per-key transition. Invalid or ambiguous joins fail closed. No auditor-side reconstruction or inference.

**PASS_METHOD_SCOPED** requires real Xvfb KeyPress/KeyRelease and server keymap down/up; backend-emitted exact admission and release rows; owner-thread verification; analyzer ready with one hold and zero malformed/unmatched/invalid counts; owner cleanup verified and stopped; exact source audit and clean WSLc cleanup. The candidate runs once; no retry.

## Scope and source

Backend methods are copied from exact current main `964c9197d5083ab55ea7fdc9105427623e89e677` / PR #8874 head `6d008b53e23fda4703c8f56c4ea1bd762e5d147b`; A23 changes only the experimental copy of the backend. Owner V4/V12 files are A09's current-main freeze at `f185a9059d485a4f8d5a65e9e7f6782897f67eae`. Analyzer is current PR #8857 head `cd766747abb4ca6d321b626c0a7b9734b9e06816`, byte-identical to A22. Exact hashes and source diff are saved in the manifest and evidence.

The Xvfb XTEST key proves only virtual server key state. The game-specific parent lifecycle and Doom/MAP01 task effect are not exercised. No physical desktop, model, threat, formal/live allocation or user task effect is claimed. WSLc uses the cached immutable image, offline, one CPU, read-only source and separate output; host memory/swap enforcement limitations remain as reported.
