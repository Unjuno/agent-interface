# Issue #6301 T0 — retained STOP: candidate/auditor disagreement

**Outcome:** `STOP_AUDITOR_DISAGREEMENT` (formal method check did not pass). This is a finite synthetic construction result only; it is not evidence about any model, GUI, human cognitive mechanism, or runtime.

**Allocation:** `EFFECT-TERMINAL-FEEDBACK-6301-T0-20261002-01`  
**Issue:** https://github.com/Unjuno/agent-interface/issues/6301  
**Frozen main snapshot:** `eba652642a7a741d57bbdfe0c1a9929d3b15bd7f`  
**Runtime:** Arch Linux WSL2, WSL Containers 3.0.1; pinned image `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (linux/amd64). Source was mounted read-only from `/home/unjuno/agent-interface-6301-t0`; formal invocations used `--pull never --network none --cpus 1 --memory 512M --rm`.

## Frozen question and method

The frozen H/T/D/C/U and truth rules are in [`FREEZE.md`](FREEZE.md). The candidate enumerated nine synthetic traces across three truthful display variants (27 trace/display rows; independent-task trace contains two tasks). The independent auditor reconstructed the rows from `fixture.json`. Formal order was construction-only tests, one candidate invocation, and—only after candidate exit zero—one auditor invocation. No model, GUI, GPU, provider, human data, or real task was involved.

## Execution record

| Stage | Result | Evidence |
|---|---|---|
| WSLc Linux-native read-only mount/cleanup smoke | PASS; write attempt rejected with EROFS and disposable container cleanup verified | `wslc_smoke.sh` (host/probe invocation); retained output summarized here |
| Construction-only tests | PASS, 5/5 | `construction_raw.txt` |
| Candidate, one formal invocation | exit 0; stdout retained | `candidate_raw.json`; stderr in `candidate_stderr.txt` |
| Independent auditor, one formal invocation | exit 1; stdout empty; traceback retained | `audit_raw.json` (0 bytes); `audit_stderr.txt` |
| Mutation controls | not reached; 0/4 adjudicated formally | auditor stopped at full-output comparison before mutations |

The auditor's first assertion failed: `candidate output differs from independent reconstruction`. Read-only inspection of the preserved raw output localized a concrete discrepancy in trace `cancelled_input` / task `task-06`: the frozen fixture says the effect is `NOT_APPLIED_VERIFIED` at the current generation, while the candidate emits B's “Effect not verified; task remains unresolved.” The same trace correctly remains non-terminal because its release obligation is still pending, but the typed effect cue is misclassified. The formal auditor compared all output rows and stopped at that mismatch. No auditor or candidate retry was made, no code was changed after the frozen formal run, and the incomplete mutation checks are not reported as passes.

## Deviations and limitations

- A pre-formal wrapper attempt failed before creating a candidate container because nested PowerShell/Bash variable quoting produced an empty bind-mount host path (`:/src:ro`). It is a setup failure, not a scientific run. The command was corrected and the frozen formal sequence then ran once.
- WSL emitted: “kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.” The requested 512 MiB cap was passed, but swap/cgroup memory isolation and peak-memory enforcement are unverified.
- A separate WSL-native runtime smoke passed. Its result does not alter the formal candidate/auditor outcome.
- The candidate/auditor disagreement prevents `PASS_METHOD_SCOPED`; no claim about cue quality, model behavior, effect size, safety, or transfer is supported.

## Reproduction and retained evidence

`FREEZE.md`, `fixture.json`, `candidate.py`, `auditor.py`, `test_construction.py`, `construction_raw.txt`, `candidate_raw.json`, `candidate_stderr.txt`, `audit_raw.json`, and `audit_stderr.txt` preserve the frozen inputs and formal outputs. `SHA256SUMS.txt` gives hashes for the retained source and raw artifacts. Do not repair and silently rerun this allocation; any corrected implementation requires a separately identified successor allocation and must preserve this STOP unchanged.

The WSL working directory was `/home/unjuno/agent-interface-6301-t0`. The evidence is submitted as an additive research record for review; no runtime behavior or `main` change is proposed.

