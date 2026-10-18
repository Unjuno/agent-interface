# Issue #7409 T0 A02 protocol

## H / T / D / C / U

**H.** A versioned-draft fixture can preserve disjoint human and agent edits across both matching and changed live revisions, while holding overlapping writes/read dependencies and refusing shared-backend, external-effect, or unknown-revision cases. The candidate will emit the exact draft-base and observed-live revision tokens; the independent auditor will derive the revision gate from those tokens and event order, not from a self-reported boolean.

**T.** This is a new allocation following A01's `HOLD_AUDIT_WEAKNESS`; it does not rerun or modify A01. Use eight authored cases: C1 disjoint writes after `r0→r1`; C2 same-field conflict after `r0→r1`; C3 hidden read/write dependency conflict after `r0→r1`; C4 disjoint writes after `r0→r2`; C5 a separate UI context with shared-backend autosave; C6 an external side effect; C7 unchanged `r0`; and C8 unavailable live revision. Candidate runs once and emits raw JSON. Only after exit 0, the independent raw-only auditor runs once, reconstructs all rows, and checks token identity/validity, equality state, revision-comparison event position, conflict decisions and promotion ordering. Eight frozen mutations alter or omit the revision receipt, falsify either token/equality, move comparison after promotion, promote same-field/dependency conflicts, or promote with an unknown token.

**D.** `METHOD_PASS_SCOPED` requires exact reconstruction of all eight rows; exact candidate-recorded base/live tokens equal to the frozen inputs; `MATCH`, `CHANGED`, or `UNKNOWN` derived correctly; revision comparison before conflict evaluation and any explicit promotion; conflict cases held; only conflict-free valid-revision cases promoted; unknown revisions held; shared-backend and external-effect cases refused before draft creation; no staged external effects; and rejection of all eight mutations. Missing or self-asserted revision evidence is `HOLD_AUDIT_WEAKNESS`; a contradictory comparison or unsafe promotion is `FAIL_AUDIT`. Neither result claims real-application behavior.

**C.** Per-field conflict detection without version tokens may be sufficient for this simple fixture. A live application may require document-level snapshots, formula/dependency metadata, server-side revision semantics, or application-specific merge rules not represented here.

**U.** This is an authored deterministic fixture only. No real application, browser, human, model, GUI, focus/live-view change, external service, safety result, or user benefit is tested. Revision identifiers and field semantics are stipulated; no production merge or T1 result follows.

## Successor delta and execution

- Issue: https://github.com/Unjuno/agent-interface/issues/7409
- Predecessor qualification: A01 `HOLD_AUDIT_WEAKNESS`, retained in PR #8148 and its `results/post_run_review/` record. A01 raw/source remain unchanged.
- Allocation: `APPLICATION-QUALIFIED-DRAFT-7409-T0-A02-20261005-01`
- Frozen main base: recorded in `FREEZE.json`; this Issue imposes no exact-main-before-candidate stop gate.
- Candidate input allowlist: `cases.json` only. Auditor inputs: `cases.json` and candidate raw output.
- Candidate and auditor formal invocation budgets: one each, auditor only after candidate exit 0, retries 0. Preserve first outputs and stop on nonzero exit.
- Runtime: OrbStack Docker with digest-pinned Python image, `--network none`, one CPU requested, read-only source/root, distinct writable output and bounded tmpfs. CPU/cgroup enforcement is not inferred.
- Both formal roles use standard-library Python only. Container mount preflight is separate from the formal allocation.
