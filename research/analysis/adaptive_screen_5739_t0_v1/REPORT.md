# Issue #5739 T0 result â confirmation claim boundaries

## H / T / D / C / U

- **H.** A claim-aware protocol should withhold an unadjusted choice among multiple survivors, restrict claims when a screened-out arm is not confirmed, and give a hard safety violation precedence over a favorable success/speed score.
- **T.** The frozen finite authored fixture ran once on Windows x86_64 / CPython 3.12.10. Candidate source and world were frozen/read back from GitHub before execution. Candidate command: `python -B runner.py`, exit 0, 32 sealed assignments. The first independent audit-v1 command `python -B audit.py` exited 1 in result serialization (`NameError: seen`); that STOP is preserved. Following the repository failure-classification rule, an explicitly versioned **read-only** audit-v2 was frozen against the exact existing raw SHA and run once; no candidate code was rerun.
- **D.** `PASS_CLAIM_BOUNDARY_SCOPED` for these fixtures under audit-v2: multiple survivors sharing the baseline cohort were labeled `HOLD_MULTIPLE_COMPARISON_UNADJUSTED`; a screened-out arm that wins on the sealed table yielded `SURVIVOR_VS_BASELINE_ONLY_NO_GLOBAL_OPTIMALITY`; and the faster, higher-success arm with a forbidden attempt yielded `HARD_SAFETY_STOP`. The retained raw emits zero global-optimality claims. Independent audit-v2 reconstructed all 32 assignments and rejected 7/7 mutations. Audit-v1 remains a failed auditor invocation, not retroactively relabeled as success.
- **C.** A single predeclared survivor-vs-baseline contrast with a fixed non-statistical gate may not require multiplicity adjustment. This deterministic fixture contains no probability model or calibrated uncertainty; it demonstrates claim-label boundaries only.
- **U.** Authored synthetic values only. No empirical GUI/model/task effect, safety, performance, global best-candidate, actual shared-resource savings, Docker/container result, or product conclusion.

## Retained outcomes and hashes

- Candidate raw SHA-256: `64f387c791f6bd87efdb05f07c9418a7631012f5203cb14bfacef3f8432ac7ea`.
- Candidate source/world SHA-256 are in `SHA256SUMS.txt`; raw-only audit-v2 inputs and source are in `AUDIT_V2_SHA256SUMS.txt`.
- Audit-v1 STOP and captured traceback are in `AUDIT_V1_STOP.md` and `audit_v1.combined_output.txt`.
- Read-only audit-v2 result SHA-256: `b0f597170a0f1ced12f787a915c6d0f435b4eab1b98080c540a1326b194461fc`.
- Audit-v2 source SHA-256: `c0f1ac21a1c081deea1b8e6bf0714e15cc40a6a9a887e6bdcde024abcbaffc76`.
- Exact commands, invocation counts, exits, and the stdout-capture limitation are recorded in `candidate_execution.json` and `audit_v2_execution.json`. The machine-readable audit result is authoritative; console output was captured by the command tool rather than separately redirected.

## Execution boundaries

No Docker was used: #5085 has no allocation for this issue, the local engine service was stopped, and ownership of old containers was unresolved. No model, GPU, GUI, game, X11, input, network, retries, or candidate rerun occurred. This is a finite CPU-only method test; it does not advance the live Issue #59/MAP01 acceptance gates.
