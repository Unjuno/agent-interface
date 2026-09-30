# Issue #5170 — matched model/effort evaluator guard

## H / T / D / C / U disposition

**H — hypothesis.** The Issue #57 evaluator may retain a comparison whose arms or preflight/task calls use different requested model/effort identities.

**T — bounded local check.** Latest tested main: `a616f3a7bbdc7fa60f53c6b20a2aaf4051b48553` (intake mutation probe was on `8346f25ba07695c0bd554bfee7d335295c9a323d`); branch: `research/issue-5170-model-effort-guard-v1`. Changed only the evaluator identity invariant and added this issue-scoped host-only suite/oracle. The cases mutate model and effort independently in each of three arms' task calls and preflights, plus the preflight/task boundary; matched and zero-task-call reuse controls are retained. No Docker/container, GPU/CUDA, model/provider, GUI, Mindustry, network task, or OS input.

**D — result: `PASS_COMPARABILITY_GUARD_SCOPED`.** Eight unittest methods pass (including 12 arm-specific subcases); the independent standard-library oracle agrees on matched baseline and mismatched mutation; the existing protocol probe remains `RETAIN` with 10 prior controls passing. The prior exploratory four mismatch mutations all returned `RETAIN` before this fix; the new suite shows those acceptance paths now fail closed. This is a protocol/evaluator result, not a Mindustry allocation result.

**C — controls.** Frozen task order, route schedule, usage, correctness/economics fields, and call cardinality stay unchanged. Only requested model/effort identities vary in mutation cases. Task calls are required to match the common identity established by all arm preflights. The independent auditor uses only Python standard library and does not import the evaluator.

**U — limits.** Establishes only the model/effort comparability gate. No model quality, task correctness, token savings, GUI behavior, runtime speed, or product claim. Issue #5130 remains separately subject to its current-main/resource gates. No Docker/GPU authorization is implied.

## Reproduction

```powershell
python -m unittest discover -s research/integration/issue_5170_model_effort_guard_v1 -p 'test_*.py' -v
python research/live_control/probe_integrated_efficiency_protocol_v1.py
python -m py_compile research/live_control/integrated_efficiency_protocol_v1.py research/integration/issue_5170_model_effort_guard_v1/test_model_effort_guard.py research/integration/issue_5170_model_effort_guard_v1/audit_model_effort_guard.py
git diff --check
```

Recorded outcome: 8 tests passed; existing probe printed `passed=true`, `positive=RETAIN`, `controls=10`; byte-compilation and diff-check passed. A post-merge invocation initially found the issue path outside the sparse checkout and therefore ran 0 tests; it is explicitly not counted. After expanding the sparse path, the 8 tests above were discovered and passed on main `442ef765598971806dc5d671a223af7b3a711a5f`. Current Windows working-copy SHA-256 values after that verified rerun:

- `research/live_control/integrated_efficiency_protocol_v1.py`: `7bf02cd7bc3b2919ba81325f6026d8ce1110b0e18803e370707feac1a1c77c5a`
- `test_model_effort_guard.py`: `378cc278d61811ff8da6b92d0917273bc75e7750ec1886fbac963c774e37cbe5` (working-copy SHA-256)
- `audit_model_effort_guard.py`: `1323f110fbbcd1c9ca94efdcedf30a94f3bcba948913ee65acd4333a35195e65` (working-copy SHA-256)
