# Allocation 02 correction under Issue #2781

Preserve allocation `dynamic-focus-save-overlap-2781-20260926-01` exactly as `STOP_EXTERNAL_EXECUTION_ENVELOPE / HOLD_FORMAL_INCOMPLETE`: batch0 completed four Inkscape rows; batch1 was externally interrupted after two completed LibreOffice SHORT rows and during case6; batches2/3 unstarted. No row is pooled into this allocation.

Changed execution plumbing only:
1. `study.run_case()` resolves its owned output root to an absolute path before forming HOME/profile/document/log paths. This removes the construction/formal path discrepancy that produced relative HOME/Openbox errors in allocation01.
2. formal serialization changes from four 4-case outer calls to sixteen 1-case outer calls. Scientific source except the one path-normalization line, schedule, fixture sizes, policies, scorer, raw auditor and decision gates are unchanged.

Excluded construction `absfix-06` invoked the corrected source with a RELATIVE `--out` path for LibreOffice SHORT cases4/5. Both produced the exact `z9z9` saved effect; STATIC waited for A then B, RESOLVED recorded B before A; Openbox stderr had no relative-HOME error. These rows are construction only.

Formal allocation ID: `dynamic-focus-save-overlap-2781-20260926-02`.
Formal denominator: same 16 SCHEDULE.json cases, each in a fresh output directory and separate Python invocation, indices 0 through15 in order. Stop on the first nonzero/timeout/missing record. No case retry/replacement/exclusion, no allocation01 pooling, no post-result tuning.

Decision rule remains the D section of PLAN.md and frozen audit.py: only a complete 16-row allocation can receive `PASS_DYNAMIC_FOCUS_SAVE_TAIL_RUNG1_SCOPED`; otherwise retain FAIL/HOLD/STOP according to observed evidence.
