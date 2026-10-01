# #4295 formal successor allocation — 2026-10-01

Allocation: `specialist-regeneration-4295-20261001-01`

Frozen main: `219439dbf803398a7283dc6c0244c598758be043`
Source capsule: `research/analysis/specialist_regeneration_4284_preformal_preserved_4295_v1/source/`

This is a fresh allocation after the original 2026-09-23 allocation remained
formal-unrun and its exact capsule was later recovered to main by PR #5713.
The old source, construction rows, branches, and all #4284/#4295 historical
evidence remain unchanged. The frozen candidate/auditor/control source bytes
are used as read-only inputs; only this additive result path is new.

## H — hypothesis

For a four-entry deterministic specialist with a complete local support
manifest, `REGENERATE_AND_ATTEST` preserves the versioned lifecycle's exact
predicate/UNKNOWN/fail-closed behavior while using fewer GENERAL calls across
support/producer changes and recovery.

## T — one-shot finite experiment

- Standard-library-only candidate; no GUI, model/provider, network, external
  files, or OS input.
- Eight frozen schedules × repetitions 10 and 11 × eight requests = 128 rows;
  each row contains `ALWAYS_GENERAL`, `VERSIONED_SHADOW_SWITCH`, and
  `REGENERATE_AND_ATTEST`.
- Source members must pass the preserved `SHA256SUMS.txt` before import.
- Run the frozen formal runner once, then its raw-only audit and 12 frozen
  corruption controls once each, only after runner exit 0.
- A separately authored raw-only completeness audit checks the exact expected
  schedule/repetition/index set. It imports neither the candidate nor the
  frozen audit and is frozen before candidate execution.
- Retain first output, command receipts, source/environment identities, audit
  outputs, hashes, and all failures. No retry, replacement, exclusion, or
  threshold tuning.

## D — decision gates

Use the frozen issue gates without modification: all 128 rows, exact oracle and
graph agreement, no stale specialist use or UNKNOWN coercion, fail-closed
novel/incomplete/corrupt controls, at least eight fewer GENERAL calls for
regeneration over the 48 version-change/recovery rows, complete attestation,
zero authority, clean frozen audit, and at least 10/12 effective corruption
controls. The independent completeness audit must also confirm the exact
8 × 2 × 8 denominator. Semantic mismatch is FAIL; insufficient call reduction
is HOLD; any source, raw, provenance, or audit gap is STOP/HOLD. The frozen
allocation is single-use.

## C / U

The complete four-entry support fixture and regeneration are deterministic.
The run uses local Darwin arm64 / CPython 3.14.5 rather than the preserved
construction container's Linux x86_64 / CPython 3.13.5; this finite
standard-library contract is expected to be platform-independent, but the
environment difference is disclosed. Invocation-count savings are not wall
time, energy, model quality, task effect, token, GUI, cross-application, or
production evidence. No general claim about learned specialists follows.
