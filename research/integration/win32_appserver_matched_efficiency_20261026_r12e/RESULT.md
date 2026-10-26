# R12e result — Win32 direct versus compiled task

**Classification:** `PASS_SCOPED_COUNTERBALANCED_WIN32_MATCHED_STUDY`  
**Source:** `cc42df79f4c6dbef2e9457d3dae31663e7368f31`  
**Host:** user-authorized Windows PC; four owned disposable Win32 fixtures  
**Runtime:** Python 3.13.14; Codex App Server `gpt-6.1-sol`, low effort  
**Independent audit:** `AUDIT.json`, all four cells and all raw hash manifests pass.

## Result

The study ran two counterbalanced pairs of the same task. Every cell selected a bounded point from a fresh public observation, clicked and typed `office`, saved, verified the exact task effect against a fresh post-dispatch observation and an independent oracle bound to the terminal call, operation and target generation, and confirmed release and cleanup. Native input readback was all-up; fixtures and App Server sessions exited; the original foreground window was restored.

| Pair/order | Arm | Total elapsed | App Server time | Turns | Reported input/output tokens | Public observations / dispatches | Result |
|---|---|---:|---:|---:|---:|---:|---|
| 1, direct first | Direct | 9.117 s | 7.589 s | 2 | 20,737 / 34 | 5 / 2 | PASS |
| 1, direct first | Compiled | 5.452 s | 3.935 s | 1 | 10,255 / 19 | 4 / 2 | PASS |
| 2, compiled first | Compiled | 5.608 s | 4.084 s | 1 | 10,255 / 19 | 4 / 2 | PASS |
| 2, compiled first | Direct | 8.792 s | 7.268 s | 2 | 20,737 / 34 | 5 / 2 | PASS |

Direct-minus-compiled total elapsed was **+3.665 s** in pair 1 and **+3.184 s** in pair 2. The corresponding App Server latency differences were **+3.654 s** and **+3.184 s**. Both pairs had the same reported usage difference: **+10,482 input tokens and +15 output tokens** for direct, with one additional model turn and one additional public observation. Both arms used two dispatches and achieved the same exact task effect.

These two pairs provide a positive descriptive result for this narrow local task: the compiled caller used the initial model-grounded target choice, then local visible-state predicates to carry out the bounded save step. With n=2 and no independent upstream billing or image-token accounting, this does not establish a causal efficiency estimate, broad reliability, or a general computer-control advantage.

## Preserved setup failures

R12 through R12d are retained in sibling packet directories with their conditions, outputs and raw manifests. They expose and preserve harness findings: a missing paired producer factory; missing caller observation sequence; response wait above the server's 10-second bound; and a transition verifier that incorrectly required the final saved state before the save transition. R12d's direct-first cell passed, while its compiled cell performed one confirmed-release click-and-type action and safely stopped before save. R12e used new fixtures and oracle IDs; it does not rewrite those outcomes.

No WSLc allocation or Docker resource was used. This result covers the owned Win32 fixture and App Server integration only; WSLc and MAP01/live GUI remain unverified. Raw and per-cell hashes are in `run/SHA256SUMS` and each cell's `SHA256SUMS`.
