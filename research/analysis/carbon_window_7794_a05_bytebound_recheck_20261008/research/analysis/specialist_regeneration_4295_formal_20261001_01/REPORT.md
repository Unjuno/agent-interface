# #4295 formal allocation report

## Disposition

**STOP_PROTOCOL_DEVIATION.** The single candidate and both primary raw audits
completed, but the frozen corruption-control command supplied the audit result
JSON where `controls.py` requires the auditor program path. Its twelve child
processes therefore executed the JSON as a Python expression and all returned
exit 0; no mutation was actually checked by the intended auditor. Preserve this
STOP and do not retry or overwrite the allocation.

## H / T / D / C / U

- **H:** For the complete deterministic four-entry support fixture,
  `REGENERATE_AND_ATTEST` preserves the versioned lifecycle's exact predicate,
  UNKNOWN, and fail-closed behavior while reducing GENERAL calls on version
  changes and recovery.
- **T:** One standard-library candidate invocation over eight schedules × two
  repetitions × eight requests. Candidate source and inputs are the exact
  recovered frozen capsule in the neighboring
  `specialist_regeneration_4284_preformal_preserved_4295_v1/source/` package.
  No GUI, provider, model, user files, or OS input were involved.
- **D:** The candidate's 128-row semantic gates and two raw audit gates pass;
  the required corruption-control gate is **NOT EVALUATED** due the invocation
  error. Therefore this allocation does not satisfy the Issue's full PASS gate.
- **C:** The support table is complete by fixture construction and regeneration
  is deterministic. This run used Darwin arm64 / CPython 3.14.5, not the
  preserved construction container's Linux x86_64 / CPython 3.13.5.
- **U:** Invocation counts are not elapsed time, energy, model quality, task
  effect, token savings, GUI behavior, or production evidence.

## First outcome

- Candidate command exited 0 and printed `{"mode": "formal", "rows": 128}`.
- `FORMAL_RAW.json` SHA-256:
  `8fe7767b456cc5ca70285b426c492675952c3247f55400d71233aa9780412d3e`.
- Frozen audit exited 0: `PASS_REGENERATE_TRIVIAL_SPECIALIST_SCOPED`,
  errors `[]`, 128 rows, 16 attestation events, 44 versioned versus 4
  regeneration GENERAL calls on the designated schedules, reduction 40.
- Independent exact-denominator audit exited 0:
  `PASS_EXACT_FORMAL_DENOMINATOR`, 128 unique rows, exact 8×2×8 coverage.
- Frozen control command exited 1 with 0/12 effective rejections. The
  preserved `CONTROLS.json` SHA-256 is
  `bbda8c6fe017bdaab942be91157f0ea5a09e8fb3a7db1994339320c78eb239a2`.
- Candidate/audit/control invocations: 1/1/1. No reruns, replacements, row
  exclusions, or tuning.

The control harness interface is `controls.py RAW AUDITOR_SCRIPT OUTPUT`.
The frozen command passed `.../AUDIT.json` as `AUDITOR_SCRIPT`; that JSON is a
valid Python expression, so the twelve subprocesses exited 0 without invoking
the intended `audit.py`. This is a protocol execution failure, not evidence
that the frozen auditor accepts or rejects those mutations.

## Commands

Candidate (exit 0):

```text
python3 -B research/analysis/specialist_regeneration_4284_preformal_preserved_4295_v1/source/runner.py formal research/analysis/specialist_regeneration_4295_formal_20261001_01/results/formal/FORMAL_RAW.json
```

Frozen audit (exit 0):

```text
python3 -B research/analysis/specialist_regeneration_4284_preformal_preserved_4295_v1/source/audit.py research/analysis/specialist_regeneration_4295_formal_20261001_01/results/formal/FORMAL_RAW.json research/analysis/specialist_regeneration_4295_formal_20261001_01/results/formal/AUDIT.json
```

Incorrect frozen controls invocation (exit 1; retained as run):

```text
python3 -B research/analysis/specialist_regeneration_4284_preformal_preserved_4295_v1/source/controls.py research/analysis/specialist_regeneration_4295_formal_20261001_01/results/formal/FORMAL_RAW.json research/analysis/specialist_regeneration_4295_formal_20261001_01/results/formal/AUDIT.json research/analysis/specialist_regeneration_4295_formal_20261001_01/results/formal/CONTROLS.json
```

Independent completeness audit (exit 0):

```text
python3 -B research/analysis/specialist_regeneration_4295_formal_20261001_01/audit_completeness.py research/analysis/specialist_regeneration_4295_formal_20261001_01/results/formal/FORMAL_RAW.json research/analysis/specialist_regeneration_4295_formal_20261001_01/results/formal/COMPLETENESS_AUDIT.json
```

## Preservation / next gate

All raw/audit/control files remain immutable. Any corrected mutation audit must
be registered as a new audit-control-only successor allocation, consume no
candidate invocation, write to a distinct output path, and state explicitly
that it cannot relabel this allocation's STOP or independently establish the
Issue hypothesis.
