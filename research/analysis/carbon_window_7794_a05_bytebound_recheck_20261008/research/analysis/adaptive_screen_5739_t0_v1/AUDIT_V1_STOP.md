# Issue #5739 T0 audit-v1 STOP receipt

## H / T / D / C / U

- **H/T:** The frozen claim-boundary fixture was tested with one candidate invocation followed by one independent audit invocation. The candidate process exited 0 and emitted 32 assignments. This file preserves the first audit disposition.
- **D:** `STOP_AUDITOR_REPORT_SERIALIZATION`: audit-v1 reached its summary construction and exited 1 with `NameError: name 'seen' is not defined` at audit.py line 104. No audit-result file was produced. Do not interpret this STOP as candidate PASS, scientific FAIL, or audit disagreement.
- **C:** The source is statically defective in the final receipt expression: `seen` exists only inside `validate()`. The error appears after raw validation and all in-memory corruption checks, but because there is no persisted audit result and nonzero exit, those checks are diagnostic only and are not an accepted independent audit.
- **U:** Candidate raw is preserved separately. No candidate retry, changed threshold, or replacement raw is permitted. A separately frozen, read-only audit-v2 may evaluate this exact raw artifact without executing or importing the candidate; any such result must leave this STOP immutable.

## First-attempt evidence

- Frozen branch: `research/5722-claim-boundary-successor-20261001`.
- Frozen base main: `24f6b7d5f9395105807f981d48db212e6692a6f4`.
- Candidate command: `python -B runner.py`; one invocation; exit 0.
- Independent auditor command: `python -B audit.py`; one invocation after candidate exit 0; exit 1.
- Candidate summary observed: 32 attempts; multiple-survivor label `HOLD_MULTIPLE_COMPARISON_UNADJUSTED`; screened-out-best label `SURVIVOR_VS_BASELINE_ONLY_NO_GLOBAL_OPTIMALITY`; unsafe-fast label `HARD_SAFETY_STOP`; zero global-optimality claims.
- Combined audit output is retained in `audit_v1.combined_output.txt`. No `audit_result.json` was emitted.
- No Docker, model, GPU, GUI, game, X11, network, input, retry, or control mutation occurred.
