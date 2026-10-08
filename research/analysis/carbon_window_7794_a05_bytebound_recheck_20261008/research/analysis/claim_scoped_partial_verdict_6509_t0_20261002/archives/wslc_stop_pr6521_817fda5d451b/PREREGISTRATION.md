# Issue #6509 — H / T / D / C / U

Allocation: `CLAIM-SCOPED-PARTIAL-VERDICT-6509-T0-20261002-01`.

## H

A typed claim ladder can retain trustworthy completed-check diagnostics after interruption while keeping every incomplete-positive, stale, contradictory, untrusted, or coverage-gap case non-authoritative. A source-bound independently decisive negative may reject early. Every complete run must equal an independent full-state oracle. This synthetic T0 tests method validity only, not a real-time benefit.

## T

Freeze 12 deterministic verifier traces and replay each through `ALL_OR_NOTHING_TIMEOUT`, `UNSAFE_SCALAR_PROGRESS` (negative control), and `CLAIM_LADDER`. Mandatory checks are `identity`, `freshness`, and `effect`; `diagnostic` is optional. Include complete positive/negative controls, timeout after a partial prefix, false scalar progress, stale generation, dropped mandatory evidence, crash between receipt and commit, untrusted receipt, contradictory later effect evidence, external state change, optional diagnostic completion without mandatory coverage, and complete mandatory coverage without optional refinement.

The candidate emits append-only source/generation-bound receipts with commit status. The independent auditor derives dispositions from raw check events, not candidate imports. The key invariant is: partial output is never `ALLOW`; `COMPLETE_ALLOW` requires complete current-generation mandatory coverage and all final authority gates; early `COUNTEREXAMPLE` requires an independently decisive, committed, source-bound and fresh negative with no contradiction. Otherwise incomplete work is `PARTIAL_UNKNOWN` with exact completed/missing check sets. A partial receipt carries no release authority.

## D

`METHOD_PASS_SCOPED` only if the scalar negative control produces the stipulated unsafe ALLOW on at least one incomplete-positive trace and the auditor flags it; every claim-ladder incomplete-positive, stale, untrusted, contradictory, crash-gap, or missing-mandatory trace remains non-ALLOW; only valid decisive negatives reject early; all complete traces match the independent oracle; and all 12×3=36 raw rows reconstruct with zero audit errors. Any false partial ALLOW, invalid early reject, or lost mandatory check is `FAIL_METHOD`. This T0 does not establish `SCOPED_BENEFIT`; no wall-clock or GUI latency claim is tested.

## C

All-or-nothing timeout may be simpler and equally useful. Some checks may lack a trustworthy atomic negative, leaving only UNKNOWN. Receipt overhead may exceed any future saved work.

## U

Finite authored traces cannot establish live GUI timing, application-effect truth, adversarial verifier resistance, or production authority. Hashes/fixture tags are symbolic bindings, not cryptography. No partial positive authorizes an action.
