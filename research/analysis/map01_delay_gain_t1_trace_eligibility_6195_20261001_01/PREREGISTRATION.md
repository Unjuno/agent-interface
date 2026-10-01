# Issue #6195 T1 preregistration — retained-trace eligibility

Allocation `MAP01-DELAY-GAIN-TRACE-ELIGIBILITY-6195-T1-20261001-02`  
Owner: Unjuno / local Windows Codex task `01a0b990-3d17-72f1-a908-9a2072104ce5`  
Window: 2026-10-01 19:35–19:50 UTC  
Frozen main: `14b81dd1f6853623a694266b98538f812847257a`  
Branch: `research/6195-delay-gain-t1-trace-eligibility-20261001-02`

## H / T / D / C / U

**H:** At least one of the exact v38/v39 traces contains a source→decision→held-action→independent-effect chain with explicit consumed-generation identity, verified release, one comparable clock domain, and repeated correction opportunities. Otherwise the historical traces are not eligible for #6195's causal delay×policy T2.

**T:** Candidate reads exactly the two source-bound JSONL inputs and reports six gates per trace, full event histograms, relevant field names, Git object identity, byte count, and SHA-256. A separately implemented raw-only auditor reconstructs those summaries directly from the two inputs and rejects five mutated candidate documents.

**D:** `T1_ELIGIBLE_TRACE_FOUND` iff one trace passes all six gates and the independent audit reconstructs every field with all five corruption probes rejected. If the retained records lack a required edge, `HOLD_NO_CLOSED_LOOP_TRACE`. Hash/parse/reconstruction failure is retained, never retried.

**C:** Exactly two public trace files are in scope. The explicit field/event rubric may conservatively miss semantically equivalent evidence encoded under other names; no missing edge is imputed.

**U:** No exact physical occupancy, controller stability, useful feedback, task-effect causality, MAP01 success, safety, human-tempo, or runtime claim. This is read-only evidence-availability analysis only.

Inputs are pinned in `FREEZE.json` by main SHA, Git blob, byte count and raw SHA-256. Both local copies were verified to match the frozen Git blob before execution. Candidate source SHA-256 is `aa1c0b74f825c3f11405903c3a61a4a4e7573924b54a3b828a117c5cd5b9b699`; auditor is `ec92b8ec117997cb2d6a8ba2720d6119a24569a0417116b443ac74c225b4d32a`.

The prior allocation-01 was a preflight HOLD before any candidate/auditor invocation because its registered GitHub branch did not contain the frozen package. This is a distinct, newly frozen allocation, not a backfill/retry. Host-only execution is appropriate for this pure retained-file inventory. Candidate once; independent audit once only after candidate exit 0; retries=0. Output path is a fresh allocation-specific directory.

