# Issue #5348 T1 — causal-cut audit disposition

## H / T / D / C / U

- **H:** In a bounded synthetic asynchronous two-stream model, vector-clock
  cuts plus explicit in-flight channel accounting can reject receive-without-
  send and other incomplete evidence while retaining complete reordered and
  independent concurrent cuts. This is a model hypothesis, not product or GUI
  evidence.
- **T:** The frozen package specifies 25 process-prefix cuts over three DAGs
  and six channel/metadata/duplicate controls, with a separately authored
  graph-parent auditor. The candidate was invoked once; the first auditor was
  invoked once. No retry or candidate rerun is recorded.
- **D:** **UNCERTAIN — preregistered audit failed.** `AUDIT-01` exited 1 with
  `raw_reconstruction_mismatch`. Its retained diagnosis reports 25 cut rows
  and six controls recomputed, `candidate_imported=false`, with only missing
  `/runtime` and `/disposition` fields identified. A post-run corrected
  auditor source exists, but there is no corrected-audit receipt; no independent
  audit PASS can be inferred from the correction code or construction tests.
- **C:** The test corpus is deterministic and synthetic; records are locally
  fresh by construction. Graph consistency does not establish that omitted
  external writers or callbacks were observed. The Issue's later paired-world
  proposal is a separate, unrun successor idea.
- **U:** No GUI/backend event, real observer, synchronized clock, performance,
  model, runtime, action, safety, or product claim. Do not rerun the frozen
  candidate or retroactively describe corrected code as the pre-run auditor.

Local archive validation: `test_core.py` passed 11/11 synthetic construction
tests. All five `test_audit_correction.py` cases
(`test_complete_expected_schema_matches`, `test_dropped_cut_row_is_rejected`,
`test_missing_runtime_metadata_is_rejected`,
`test_nonzero_side_effect_is_rejected`, and `test_wrong_candidate_blob_is_rejected`)
errored before auditing any file: `audit_t0_corrected.expected_raw()` raises
`NameError: name 'false' is not defined` while constructing an in-memory
synthetic record. This is a separate local construction failure, not an
AUDIT-02 receipt. No code or historical artifact was repaired or rerun. See
`ARCHIVAL_QUALIFICATION.md`; original files and result artifacts are unchanged.
