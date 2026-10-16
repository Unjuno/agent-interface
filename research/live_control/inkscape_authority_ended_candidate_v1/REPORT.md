# Inkscape authority-ended one-capture receipt candidate v1

Status: **PASS_OFFLINE_RECEIPT_MECHANISM / HOLD_LIVE_INTEGRATION**.

Immutable base: `7f42fd577dff98d6a27a8eceb79d86bee0358bf9`. Tracks #166. This generation is additive and offline only: no shared executor/runtime edit, no GUI, model, OS input, or network effect.

## Why this exists

The retained legacy Inkscape expiry audit showed that the old `expired` terminal is not interchangeable with the newer `authority_ended` receipt. The mismatch is not cosmetic: the legacy path retains two passive captures and no independent post-authority lifecycle deadline/snapshot-finish contract.

This candidate isolates only the missing mechanism before touching the real Inkscape runtime.

## Candidate contract

`build_authority_ended_receipt()` accepts an already verified release and explicit evidence inputs. It contains **no fixed lifecycle budget**. The caller must supply `lifecycle_budget_ns` and the observed `post_release_input_admissions` count.

The mechanism:

1. requires a verified release with empty owned keys/buttons and integer `verified_ns`;
2. requires a positive source observation sequence, positive explicit lifecycle budget, and zero post-release input admissions;
3. requires the backend sequence to still equal the supplied source sequence before the post-authority capture;
4. performs exactly one synchronous `backend.snapshot()` attempt;
5. records the backend's singular resulting sequence plus the clock value immediately after the snapshot call returns as `snapshot_finished_ns`;
6. derives sequence advancement and deadline membership;
7. emits `terminal_status=authority_ended` while retaining the provenance reason `authority_end_reason=expired`;
8. grants no input authority and claims no old-tail resumption.

The unchanged bridge used by the retained authority-ended research is copied byte-for-byte into this evidence directory. Its SHA-256 is `2c9684d8f731b36469df06532fc2ce566716c0380002d18da1f317814f7acb1e`.

## Frozen first-outcome matrix

Environment: CPython 3.13.5, Linux 6.18.44 x86_64.

Candidate SHA-256: `fc625dbd68c0615c5855258fdc44d89896b98c8bb086c113b982c9643e6d9330`.
Runner SHA-256: `663511293d6444b3cfa774fab103a95d990d8234527911d3b2da600d79fde3e5`.
Independent auditor SHA-256: `9d1852eebb2f3157d3ad23719bf442a899e7e505678ba5afa913525ab5fe6cc5`.

All **9/9** frozen rows passed and no case invoked more than one snapshot:

| Case | First outcome |
|---|---|
| clean | unchanged bridge accepts and returns `safe_yield / authority_unavailable` |
| snapshot returns after lifecycle deadline | bridge rejects `post-authority observation outside lifecycle deadline` |
| snapshot raises | receipt records zero captures/error; bridge rejects exact-one-capture gate |
| sequence does not advance | bridge rejects sequence-advance gate |
| post-release admission count = 1 | candidate rejects before snapshot |
| release unverified | candidate rejects before snapshot |
| release still has a held key | candidate rejects before snapshot |
| lifecycle budget <= 0 | candidate rejects before snapshot |
| clean receipt mutated to two captures | unchanged bridge rejects exact-one-capture gate |

Decision: **`PASS_OFFLINE_RECEIPT_MECHANISM`**.

## What this does not prove

This result does not select or validate a real Inkscape lifecycle budget. The 400 ms value in the deterministic matrix is a test fixture, not a universal or production constant. It also does not establish that the real Inkscape backend's synchronous snapshot return time, sequence publication, or failure behavior matches the fake backend.

No claim is made about cross-process durability, power loss, exactly-once external effects, or useful task completion.

## H / T / D / C / U

**H.** A one-capture receipt mechanism with an explicit lifecycle budget can satisfy the existing `authority_ended` bridge cleanly while failing closed under the frozen faults.

**T.** Deterministic fake backend + injectable monotonic ns clock. Nine preregistered cases. Exact unchanged bridge. One first outcome; no tuning.

**D.** **PASS_OFFLINE_RECEIPT_MECHANISM / HOLD_LIVE_INTEGRATION.** Clean acceptance and eight negative controls behaved as specified; maximum snapshot calls per case was one.

**C.** The real Inkscape snapshot path may violate the candidate's timing/sequence assumptions even though the isolated mechanism passes. That is the next discriminator.

**U.** Offline only. The major remaining uncertainties are real snapshot latency distribution, whether return-time is the correct completed-snapshot boundary in the real backend, and how to measure zero post-release input admissions from the live owner/event stream without assuming it.

## Next smallest experiment

Create a versioned Inkscape runtime candidate without modifying the shared executor. On the same model-free held-Shift expiry scenario used by the legacy retained run, replace the old two-sample post-release collector with this singular receipt mechanism under a preregistered explicit lifecycle budget. Require:

- actual terminal status `authority_ended` with reason `expired`;
- verified empty release;
- exactly one passive post-authority snapshot;
- singular advanced sequence;
- retained snapshot-finish/deadline timestamps and positive margin;
- zero observed post-release input admissions and no program-tail resumption;
- unchanged bridge acceptance;
- trailing text still suppressed.

Only after that live receipt passes should it be composed with the already-retained durable-token + durable-submit callback ordering.
