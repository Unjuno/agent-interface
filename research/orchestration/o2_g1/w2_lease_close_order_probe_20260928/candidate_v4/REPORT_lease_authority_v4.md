# W2 lease authority v4 — open/close interval boundary

## H / T / D / C / U

**H.** Candidate v3 can authorize an input edge that occurs before its matching `LEASE_OPEN`, because v3 records open lineage but discards the open timestamp. Contract-aligned authority requires the input-edge interval to be wholly after the matching lease-open interval and before any applicable close.

**T.** Keep v3 and all frozen W2 source/results unchanged. Using the exact frozen eight-case trace fixture, exercise edge-before-open, overlap with open, strictly-after-open, unknown open time, terminal without close, and explicit close before edge. Compare the v4 candidate, separately written raw-row oracle, and explicit expected interval rule across the Cartesian domain of 21 edge intervals, 24 open-time states, 24 close-time states, four close-lineage relations, and 24 terminal-time states.

**D.** PASS only if all focused cases produce the stated policy, candidate and oracle agree with the separately defined rule on every combination, and the focused plus existing binding/close regressions pass. Any harness-construction issue is retained and corrected before a full result; no preliminary failure is overwritten.

**C.** Single synthetic clock, integer endpoints 0..5, one target lease/actuation, one close row per combination, and terminal varied independently. Missing/unknown/invalid open time holds. An edge wholly earlier than open rejects; an interval intersecting open is held. Foreign-lease closure is irrelevant; same-lease close lineage must match. Terminal never stands in for a close.

**U.** Python 3.12.10 Windows host CPU. Docker Desktop context is `desktop-linux`; no container was invoked. At the queue check, the named one-cycle shared CPU allocation belonged to another research lane (#5133 -04), and the lease cannot be inherited. This is not a formal/live run, runtime behavior, or product-safety finding.

## Result

`PASS_FINITE_LEASE_AUTHORITY_OPEN_CLOSE_INTERVAL_POLICY_ONLY`. The exhaustive audit checked 1,161,216 combinations with zero candidate/oracle mismatches and zero expected-rule mismatches. After static review, the harness was tightened to select the target decision by event ID rather than list position; the full 32-test suite and all 1,161,216 combinations were rerun with the same zero-mismatch result. Six focused v4 tests and 26 existing regression tests passed (32/32 total).

The material result is a v3 candidate gap, not a change to the frozen verifier: v3 omitted the `LEASE_OPEN` time bound. V4 holds when open timing is unknown or overlaps the edge, rejects an edge definitely before open, and only then applies the explicit-close rule. `PROGRAM_TERMINAL` remains a distinct lifecycle event, not an inferred lease close. The v3 PR/result remain immutable; v4 is a successor candidate.

Preliminary environment/harness failures, corrections, and one superseded duplicate process stopped after exact command-line inspection are itemized in `PRELIMINARY_FAILURES_lease_authority_v4.json`. The first command failure was the missing fixture environment variable; corrected run passed. Early exhaustive drafts had lineage/sentinel mistakes in the test harness; after correction the single counted complete run passed.

## Reproduction

From this local evidence directory:

```powershell
$env:W2_TRACE_FIXTURE = (Resolve-Path ..\o2-w2-independent-audit-20260928\trace-cases.json).Path
python -m unittest -v test_lease_authority_v4.py test_lease_authority_v3.py test_binding.py test_binding_v2.py test_binding_gate_cli.py test_close_order_cli.py
python exhaustive_lease_authority_v4.py
```

The additive candidate, oracle, focused tests, enumerator, source freeze, result, and failure ledger are retained beside this report. After the run, the five W2 source blobs were re-fetched at each observed newer main through `716d25286ec37999d8098cd63bf1731fae0d88d6`; all remain identical to the frozen source identities. Before any container rerun, refetch them again and obtain an explicit queue lease. The latest coordinator order prioritizes #5134 and is reconciling #5134/#5139 sequencing, so #5127 is deferred and has no lease. No production or integrated-runtime claim follows from this finite synthetic pass.
