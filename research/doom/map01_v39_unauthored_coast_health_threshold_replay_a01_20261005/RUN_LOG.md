# Execution record

The input trace is posthoc A04 evidence. No live allocation, game, model, GUI,
X11, or OS input was executed here.

- Selected repository base: `95316efef54b092fc2f0264539223830cdb9ba21`.
- Python: `Python 3.14.5` (system standard library only).
- Candidate source SHA-256: `9b72e814b085a00087739c5bf51e13f15fd8d2d14027993e0cb33a041e20fef5`.
- A01 candidate run: exit 0, `PASS_A04_TRACE_REPLAY`, 45 timed observations and
  five thresholds. Result: `results/a01/candidate.json`.
- A01 independent audit: exit 0, `PASS_A04_TRACE_REPLAY_AUDIT`, 12 checks.
  Result: `results/a01/audit.json`.
- A02 is the same deterministic trace replay after strengthening provenance
  checks in the auditor (source manifest, freeze, result and prior audit
  hashes). Candidate bytes match A01 exactly. A02's auditor wrote 16 passing
  checks but still resolved the default A01 candidate path; preserve this
  output with that limitation.
- A03 fixes the auditor to read the candidate from its own `RESULT_DIR` and
  repeats the deterministic trace replay once. Candidate and auditor exit 0;
  the path-bound independent audit passes 16 checks over 45 observations.
  `results/a03/` is the authoritative candidate/audit pair.
- A separate auditor corruption control changed one byte in a temporary copy
  of the A04 report. The A03 auditor exited 1 with `AssertionError` before
  writing an audit result, as expected. Summary: `results/a03/audit_tamper_control.json`.
- After `origin/main` advanced from `95316efef` to `307b9e2f`, the branch was
  rebased and the controller file SHA remained unchanged. The frozen replay
  was rerun to `results/a04/`; candidate and its path-bound independent audit
  exit 0, and the audit again passes 16 checks over 45 observations. This is
  deterministic revalidation of one retained trace, not an independent trial.
- During initial wiring, two candidate invocations exited 1 before writing any
  result: the retained upstream package checksum list uses literal `\\n`
  separators, and the A04 action snapshot is adjacent to, not nested in, its
  contract. The parser was corrected to normalize the manifest and read the
  frozen report schema. These setup failures changed no source evidence and are
  retained here; they are not threshold outcomes.
- Candidate and auditor `py_compile` passed. The final package checksum check
  and `git diff --check` are recorded with the committed tree.
- An independent PR comment observed that the A04 negative-control checks
  compared report values with the candidate but did not bind those values to
  raw events. A05 leaves the candidate and frozen trace unchanged and extends
  the auditor to require unique typed-observation sequence IDs, matching
  source/monitor sequence, capture time, observed health status/value, and the
  `health:source_expired` reason. The audit emits the raw join in its result.
- A05 candidate and audit both exited 0. The audit passes 25 checks over the
  same 45 pending observations and records source seq204 health 30 and monitor
  seq216 health 30, with their raw capture timestamps.
- Negative control: in a temporary copy, seq216 raw health was changed to 29
  and the copied manifests were updated so provenance checks still passed.
  Audit exited 1 with `AssertionError` and created no audit output in an empty
  result directory. The original A04 inputs and retained A01-A05 outputs were
  untouched.
- Negative-control summary: `results/a05/audit_tamper_control.json`.
