# Finite compiled cancellation characterization (#57)

Disposition: **PASS_FINITE_CANCELLATION_SCOPED** under the explicit v2 finite oracle. This is additive analytical/engineering evidence, not a live task, physical release, model, timing or efficiency result. No executable runtime change is proposed.

The executed matrix uses exact Git-byte snapshots of main `11f1bae6f8dbfd280b6ccbd0def0bc23fa5da68d` and PR #6863 head `82bf35dba0c709370e18d3ccacef434818879ba5`. Eighteen permanent-cancellation schedules cross four execution terminals, giving 72 rows per source and 144 total. Both sources behave identically on these valid-integer-admission conditions. The unchanged main already checks cancellation after admission; a source repair is unnecessary for the tested property. This does not repeat #6863's admission-type matrix or confer approval of that entire PR.

| Per-source outcome | Rows |
| --- | ---: |
| SAFE_YIELD / cancelled | 29 |
| SAFE_YIELD / delivery_uncertain | 13 |
| RUNTIME_FAILED / execution_failed (release failure) | 13 |
| SAFE_YIELD / execution_refused (attested no input) | 13 |
| TASK_SUCCEEDED / method_complete | 4 |
| Total | 72 |

Across both sources, 76 rows actually reach their cancellation trigger; the other 68 include never-cancel controls and unreachable triggers after an earlier terminal. No execute entry occurs after a delivered cancellation. Thirty-six completed released transitions are retained across the matrix. Cancellation delivered during an execute callback does not erase that already-entered action. Cancellation during the final observe/verify/complete-branch journal can coexist with graph completion: this study claims zero later dispatch, not universal cancellation precedence or an independent application-effect certificate.

Candidate and first raw auditor each invoked once, exit 0. The main compiled regression suite passes 29/29. Exact process commands, UTC times, stdout/stderr and exits are in `*.receipt.json`. Injected runtime clock is constant zero; real subprocess timestamps are provenance only, not runtime latency evidence.

## First audit and completeness correction

Preserve `audit.py`, `audit.json`, `controls.json` and their first outputs unchanged. The v1 raw-only checker passes 144/144 rows and rejects ten raw corruptions. Deleting all three cancellation checks in an isolated source copy exposes post-cancellation execute entries in 28/72 rows and is rejected.

After these checks, review found that v1's invariant-only gate could accept an always-stop implementation. Overall acceptance was held while a separately frozen v2 supplement added explicit finite reachability, normal completion and terminal/prefix counts. `AUDIT_V2_FREEZE.json` was fixed before invoking it. The original candidate/raw were **not** rerun. V2 independently reconstructs the same 144 rows with zero errors, rejects all ten raw controls and both diagnostic implementation mutations. The new always-stop mutant passes v1 with zero errors but fails v2 in 52/72 rows; its source and raw are retained in `mutants/`. V1's first result is a limited invariant result, not evidence of complete control coverage.

The auditors import neither the tested runtime nor candidate. V2 reuses v1's raw invariant checks and adds a separately authored case oracle; it is not wholly independent of v1. Both auditors are authored by this worker, so neither substitutes for nonauthor review. Source mutations and copied-data controls are ordinary diagnostics, not new formal allocations or retries of historical experiments.

See [PLAN.md](PLAN.md) for H/T/D/C/U, exact boundary assumptions and variable units; [FREEZE.json](FREEZE.json) for source Git/SHA-256 identities; [audit_v2.json](audit_v2.json) and [controls_v2.json](controls_v2.json) for final gate results. `SHA256SUMS` covers the package except itself.

## Execution and integration limits

macOS arm64, CPython 3.14.5, stdlib, no physical input, backend, GUI, model, GPU, VM or container. Analytical-first enumeration is appropriate to this exactly specified callback-order property under `docs/RESEARCH_METHOD.md` and FINAL-v5 section 5. It does not establish blocked-call preemption, transient-pulse delivery, thread races, hardware/OS release, foreign-platform behavior, end-to-end reliability, tokens, latency or human tempo. No formal/shared allocation is acquired.

Exact historical source snapshots are fixed. Current main advanced during the work; intervening changes through `f1416985d4` do not touch the relevant runtime/configuration paths. Recheck dependency applicability and current-main combination at integration. The evidence-only PR still needs FINAL-v5 fixed nonauthor committee and approvals, combined-tree nonauthor verification, applicable real GitHub requirements and conditional application. No main write, quorum reduction or required-condition bypass is implied.

Setup failures were corrected in the dedicated checkout before candidate invocation: a shared-object clone initially lacked promisor configuration and sparse checkout exposed missing blobs; declaring origin as the existing partial-clone remote and narrowing checkout fetched the two required doc blobs. Initial add refused paths outside sparse definition; `git add --sparse` then succeeded. Neither failure ran the candidate or changed another worker's checkout. The full tool transcripts remain in this session; these are setup disclosures, not invented process receipts or scientific outcomes.
