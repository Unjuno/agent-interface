# #5766 T0 allocation 02 — explicit successor to retained failure

This is a new frozen allocation, not a rerun or edit of allocation 01. Allocation 01 remains `FAIL_T0_CONTRACT` on main with its first raw and auditor outputs unchanged. Allocation 02 addresses only its two identified implementation defects: use current-semantic check disagreement to hold the interval, and bind the auditor to the actual frozen deck-hash field. The same finite synthetic deck is intentionally reused to keep the correction comparison fixed; this does not constitute independent empirical replication.

## H / T / D / C / U

**H.** On the frozen finite oracle-check deck, bracketing catches induced in-deck semantic drift despite unchanged scorer bytes; does not falsely reject an equivalent scorer/app version change; and reports out-of-coverage candidate events as `UNKNOWN_COVERAGE`.

**T.** Candidate runs once in network-disabled pinned Python Docker. Cases are valid positive, wrong target, collateral effect, unsaved state and UNKNOWN. Four scenarios: nominal; app artifact-meaning drift with unchanged scorer source; a schema/scorer version change preserving meaning; and a candidate event outside declared deck coverage. Candidate output retains all five pre- and post-check rows. The separate raw-only auditor reads the output once, independently computes expected rows and decisions, and tests four mutations: missing post-check; swapped frozen label; UNKNOWN→PASS; post-candidate reference backfill.

**D.** `PASS_METHOD_SCOPED` only if the nominal and equivalent-version rows agree with independent and frozen references; same-hash drift has at least one score/reference discrepancy and is held as `HOLD_ORACLE_DRIFT`; out-of-coverage stays `UNKNOWN_COVERAGE`; all rows are retained; and the auditor reports zero base errors while rejecting all four mutations. Otherwise preserve exact FAIL/HOLD. One candidate invocation and one auditor invocation; no retries.

**C.** Deterministic constructed profiles and stipulated independent reference table; no real app or scorer deployment. Same deck as allocation 01, explicitly used to isolate implementation corrections.

**U.** Even a method-scoped pass says nothing about real semantic drift, reference adjudication quality, unseen semantics, task outcomes, #12/#57/#59 or production suitability. T1 requires replayable real raw outcomes and independent adjudication, and a separate authorization.

**Execution boundary:** CPU-only Docker; exact image pinned by digest; container network disabled, root filesystem and source mount read-only, output mounted separately. No GPU, GUI, model, OS input or live task. Candidate and auditor both verify the frozen deck byte hash, canonical deck hash and reference-lock hash. Freeze, branch, path, all source hashes and decision gates are committed and read back before the candidate call.
