# r133 cross-domain evidence coverage transfer

## H/T/D/C/U

- **H:** An axis-separated coverage vector can represent physical bounded input brackets, interval-censored continuous-control occupancy, weak state feedback, untimed discrete-task outcomes, and observation counts without imputing missing or censored endpoints as zero or success.
- **T:** One deterministic reconstruction from the five exact retained source blobs listed in `frozen_sources.py`, run once in a network-disabled Docker container; then a separate raw-only auditor independently reconstructs the expected vector and attempts three corruption controls.
- **D:** The frozen values and classifications match; Calc duration, DOOM plan-bound task effect, and v39 occupancy-gate promotion are rejected. No scalar cross-domain score is emitted.
- **C:** Existing retained summaries only; no model/GUI/game calls, no input actuation, no raw-trace rescanning, no repeated source allocation. This compares evidence semantics, not matched domain performance.
- **U:** Does not measure new held-input duration, task effect, first-useful-feedback timing, bounded recovery, human tempo, or cross-domain performance transfer. It does not complete r133.

## T0-01 — retained infrastructure STOP

The first Docker allocation used `git cat-file` inside `python:3.12.10-slim`, where Git was absent. It stopped before reading any source blob or constructing a candidate. Exact evidence: `results/t0-01/STOP.json`. No retry or result substitution was made.

## T0-02 — retained infrastructure STOP

The host exporter resolved the exact frozen Git blobs, but its first container invocation omitted Docker's `-i` option. Standard input was empty; JSON parsing failed before source verification or candidate generation. Exact evidence is retained in `results/t0-02/STOP.json` and `results/t0-02-container-run.log`. No retry or audit was performed.

## T0-03 — frozen source payload reconstruction

Base: `6968d45197c6a29e717a9281dcd050be1eed90c7`. The host handoff verifies the commit-to-path Git object IDs and exports their exact blob bytes as UTF-8 in one JSON stdin payload. Both isolated candidate and auditor containers recompute all four Git blob SHA-1 identities before parsing. Candidate and auditor are separate Docker processes; the auditor imports neither candidate builder nor candidate tests and independently reconstructs all classifications. Local unit tests are construction checks only. Formal outputs are additive under `results/t0-03/`; the handoff refuses an existing output directory and has a unit-tested `-i` invariant.

Run one time from the repository root (the experiment image has Python only; Git object reads are supplied as a read-only mounted repository):

```powershell
python -B docker_handoff.py
```

The image is pinned by the resolved base digest and local built-image ID in `FREEZE_T0-03.json`. Network is disabled and the container root filesystem is read-only; only the result bundle is mounted writable, with a bounded private `/tmp`. The host runner invokes one candidate container, then one separate auditor container. No retries or post-result tuning are permitted; any defect after launch remains a STOP/FAIL and requires T0-04.

## Interpretation

PASS can establish only faithful, mutation-resistant evidence classification. A release edge is not an occupancy-duration measurement; health/ammo change is not an independently scored useful task effect; a correct saved document is untimed without the missing receipt clock; passing v38's precision gate does not rescue v39. These are separate axis outcomes, not one agent capability score.
