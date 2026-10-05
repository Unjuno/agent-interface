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
- During initial wiring, two candidate invocations exited 1 before writing any
  result: the retained upstream package checksum list uses literal `\\n`
  separators, and the A04 action snapshot is adjacent to, not nested in, its
  contract. The parser was corrected to normalize the manifest and read the
  frozen report schema. These setup failures changed no source evidence and are
  retained here; they are not threshold outcomes.
- Candidate and auditor `py_compile` passed. The final package checksum check
  and `git diff --check` are recorded with the committed tree.
