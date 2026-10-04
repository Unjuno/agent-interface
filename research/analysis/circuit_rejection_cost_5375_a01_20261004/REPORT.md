# #5375 A01 STOP rescue

## H / T / D / C / U

**H:** A01 contains useful custody evidence for a failed synthetic construction attempt, but its hypothesis result is unevaluated and its auditor never wrote a verdict.

**T:** Preserve the exact five-file package from PR #7391 on current main, verify the raw receipt byte-for-byte and syntax-check the frozen programs without invoking either one, then refresh the generated analysis index.

**D:** Retain the candidate's observed first-row capacity violation and the auditor's `STOP_AUDIT_OUTPUT_READ_ONLY` exactly as recorded. No candidate or auditor rerun; no replacement audit; no PASS interpretation.

**C:** The scenario is deterministic and hand-authored. It does not estimate real rejection/quarantine cost, Agent Interface workload behavior, resilience prevalence, latency, GUI/model effects, or product safety.

**U:** Scientific hypothesis remains unevaluated. Future work requires a new allocation ID, corrected queue/resource semantics, construction tests, and a writable auditor output destination. Earlier #5375 evidence and this one-shot record remain immutable.

## Provenance and local checks

- Source: PR #7391 head `3d4c982c83022ec697fe6cd47e68e08ab2e107b0`; exact candidate, auditor, README, raw JSONL and run record copied without edits.
- Base: current main observed at `41df296f3ce4d03c801c998d38f6e537e64a83ab`.
- Raw SHA-256 reproduced locally: `cbfe518ebc72d9f2fa74a7722b0d66924af1ef5eeb1660cbe5929346e3b05fb8`, matching the run record. Recorded raw size is 147,085 bytes.
- Candidate/auditor syntax compilation is permitted; execution is not. Original STOPs and the 480-row raw file are preserved.
- `git diff --check` reports only inherited trailing whitespace/blank-at-EOF in the frozen README and run record/program files. These bytes are retained to avoid altering the original package; no new report/index whitespace warning was observed.
- PR #7391 replay-gate and analysis-index checks passed; formal was skipped. Local full analysis-index validation is run after refreshing the generated index.

This is archival rescue of failure/STOP evidence, not an experiment success or a code change eligible for runtime integration.
