# Issue #5962 — retained-session eligibility T1 (successor 02)

**Disposition: `HOLD_T2_NO_COMPARABLE_SESSION_COHORT`.** This is a provenance/eligibility audit, not an estimate of route reliability or a test of the mission-survival hypothesis.

The first allocation (`...-01`) is retained as `FAIL_INTEGRITY_REPORT_SNAPSHOT_MISMATCH`: its output embedded the old main SHA despite preregistering a newer snapshot. Its freeze, candidate, and output are preserved unchanged outside this successor package; it is not evidence and was not overwritten. This clean successor corrects the embedded snapshot and makes one separately frozen invocation.

## Frozen inputs and method

At main `ad123c3875d81ebdc8bdfbdb59340005d705a60d`, the comparison-04 manifest blob is `68d328b9a9d99a6b19c84aa7ac9f8a152d810a5b`, and its raw archive SHA-256 is `811e63849956658bdbb0fecc1a7237308dd93c71d96644050b1581bc243c4dd2`. The CPU-only standard-library auditor verified all 1,051 archive members, with zero member mismatches, then examined `current`, `interrupted02`, and `caller-stop03`. Archive contents were parsed as data; no archived executable was run.

The separately committed #2737 v4 `RESULT.json` (blob `69c7ae2f69f701e4b951aaebc6b6071942c969a8`) reports one six-task container allocation and independent exact-effect/release checks. Its full report remains local per its README, so it is treated as a compact public summary only and is not pooled with comparison-04.

## Findings

- `current` contains one complete descriptive direct/guarded six-task pair. Both routes have the same declared task order and exact-once independent effect ledger; task phases include warm/carryover and invalidation/repair. Host-event sequences are contiguous, but no explicit stable session/conversation ID is present in those events. Identity is a route-local display/window/history composite.
- The pair is serial, with growing conversation context and uncounterbalanced route order. No explicit reset/clean-boundary receipt joins both routes to a stable session identifier. It documents sequence behavior but does not qualify as a comparable independent-session route-ranking cohort.
- `interrupted02` preserves direct's completed six-task trace and guarded's three-task prefix; guarded tasks 4–6 are missing after an explicitly authorized WSL restart. This is an interruption, not success and not silently censored.
- `caller-stop03` preserves a caller schema-refusal STOP before field input (zero task records); it is not converted into six failures. Guarded was never allocated.
- These campaigns have distinct seeds/source revisions and are not exchangeable replicated route pairs. The one complete current pair is descriptive only; T2 eligibility is false.

## T1 decision

Retain `HOLD_T2_NO_COMPARABLE_SESSION_COHORT`. Do not infer a ranking reversal, temporal dependence parameter, or user-facing reliability claim. A future T2 needs a separately frozen matched set of independent sessions, explicit session and reset identity, counterbalanced route order, complete first-outcome/STOP accounting, and independent effect scoring. #2737's compact summary remains a separate candidate record but cannot supply its missing full trace here.

## Reproduction package

`FREEZE.json` binds source identities, candidate bytes, one invocation, and scope. `PROCESS.json` records invocation and exit status. `eligibility-audit.json` is the sole formal output for this successor. `SHA256SUMS` binds the package. `PREREGISTRATION.md` retains H/T/D/C/U. Raw inputs remain at existing repository paths and are identified by exact hashes; they are not duplicated in this publication.