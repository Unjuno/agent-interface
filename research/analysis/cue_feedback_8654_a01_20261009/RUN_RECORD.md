# C01 run record and raw-custody stop

Issue: #8654  
Branch: research/8654-a01-20261009  
Type: unpromoted construction check; not the formal T0 allocation  
Execution date: 2026-10-08 UTC / 2026-10-09 JST  
Host: Windows 10.0.26200.9550, Python 3.12.10, standard library only

## Frozen inputs

- Protocol commit: 4f8791421ef402cb0ba930fa1bfc6a14628c742c; file blob SHA: f1f8ba5b7ed3fa3b2b59db6f15987420bb5a96d8.
- Candidate source: research/analysis/cue_feedback_8654_a01_20261009/candidate.py; blob SHA: 887ec03bb2cf136db8d044fc636d0975e28d672d.
- Independent auditor source: research/analysis/cue_feedback_8654_a01_20261009/audit.py; blob SHA: 512662c2cc27ea4aea2aeaf911018ea18e1248ff.
- Candidate and auditor were fetched from the frozen branch immediately before execution.

## First-run record

One candidate invocation emitted the 867-row JSONL stream. One separate Python process consumed that stream as stdin and ran the frozen auditor. No candidate or auditor retry occurred. The auditor output was:

```json
{
  "errors": [],
  "expected_rows": 867,
  "mutations_rejected": 4,
  "mutations_total": 4,
  "probability_mass": {
    "GLOBAL_SHIFT": 1.0,
    "REVERSAL": 1.0,
    "STABLE": 1.0
  },
  "rows": 867,
  "scope": "deterministic finite method construction only",
  "status": "PASS_CONSTRUCTION_SCOPED"
}
```

Raw stream SHA-256 (computed over UTF-8 JSONL including final newline): 9ecddefb9e6d1ed456e889890d640a2fbb6519383988f8a30abc92b5bf79df77.

## Custody failure and disposition

The runner retained the stream only in process memory and did not persist or publish the JSONL before returning. The stream is therefore **not recoverable from this evidence package**, despite its digest and the successful raw-only audit. Do not treat the auditor's output as independently re-auditable raw evidence.

Disposition: **STOP_RAW_CUSTODY_NOT_RETAINED** for evidence promotion. Preserve the auditor's method result exactly as observed, but do not claim a validated experiment, do not merge this package as a scientific PASS, and do not rerun or recreate the same allocation. A genuinely new successor allocation would require an explicit protocol that durably writes candidate output before the audit and a new freeze/allocation; it must not overwrite or retroactively repair this first result.

The run was on the native Windows Python host because WSLc 3.0.1.0's preceding read-only smoke test ended in WSL ERROR_TIMEOUT and the registered Ubuntu distribution's direct process startup failed with WSL error 5. No WSLc result, Docker comparison, resource-limit claim, runtime behavior, model result, GUI effect, human outcome, or product claim follows.
