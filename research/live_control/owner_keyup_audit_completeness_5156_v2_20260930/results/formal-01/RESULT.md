# Allocation 04 T0 result — key-up audit completeness

Allocation: `map01-owner-keyup-audit-completeness-5156-t0-v2-20260930-01`  
Source freeze: `3929f856f16166cb2600b7b6e7f3f709850b0de6`  
Frozen main: `de12176584bf7192d206a12a44b4f2877faf3ab2`

## H / T / D / C / U

- **H:** A separately frozen expected-release inventory lets a raw-only auditor detect missing key-release measurements, including deletion of every measurement row.
- **T:** Read back the frozen GitHub source bytes, run the fixed synthetic 12-test suite with CPython 3.12.14, execute the frozen two-row runner once, then run the frozen auditor in a distinct Python process on the captured raw and eight frozen corruption mutations.
- **D:** `PASS_AUDIT_COMPLETENESS_T0_SYNTHETIC_ONLY`. Hash readback matched every frozen source SHA-256. Unit tests 12/12 passed. Runner: one invocation, two records. Separate raw-only audit: PASS, errors=[]; corruption controls 8/8 rejected (drop all, drop one, duplicate, unexpected identity, bool timestamp, inverted order, authority escalation, physical-key-up claim).
- **C:** Host-only Python construction; no Docker/OrbStack invocation, X11 server, GUI, physical keyboard, MAP01, model, GPU or CUDA. This establishes only behavior for the synthetic contract and retained bytes, not server/physical key-up timing, MAP01 occupancy, task effect, recovery, or human tempo.
- **U:** A distinct authorized disposable X11 fixture and later plan-bound MAP01 measurement remain unrun. Applying completeness checking to real traces requires an independently retained expected-release inventory tied to observed admissions/terminal records.

## Provenance

The frozen runner and expected inventory were read from the branch and executed in memory; raw stdout is retained as `formal-01/raw.json`. The auditor ran in a separate CPython process, importing neither the runner nor unit tests; its output is `formal-01/AUDIT.json`. No local evidence files were written. The #5085 no-Docker boundary remained in force.

This T0 repairs the synthetic auditor-completeness contract only. Allocation-03, PR #5298, #443/#503, all original v38/v39 bytes and dispositions are unchanged. No formal X11 allocation was consumed.
