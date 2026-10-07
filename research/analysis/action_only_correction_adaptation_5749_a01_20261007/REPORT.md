# Issue #5749 action-only adaptation successor — A01

**Scoped disposition: `PASS_METHOD_SCOPED`; interpretation remains synthetic and conditional.** The candidate ran once (exit 0); an independent reconstruction ran once (exit 0), matched all 78/78 policy-turn rows with zero errors, and rejected all seven frozen corruptions. Retries: 0.

## Results

In the stable-B episode, the action-only adapter learned B after the second consecutive B observation. Across six turns, wrong proposals were 1 for action-only adaptation, 6 for the fixed A default, and 0 for clarification-only; query counts were 0, 0, and 6 respectively. Across all five scripted episodes / 26 turns, wrong proposals were 6 (adaptive), 17 (static), and 0 (clarify); queries were 0, 0, and 26.

The boundary episodes behaved as frozen: a one-off B followed by conflicting A and a missing event did not install a durable choice; a new B observation suspended learned A and yielded until confirmation; scope change cleared learned B before the next proposal; and consent revocation cleared adaptation before using only the explicit A default. All outputs had `authority_granted=false`; clarification answers were turn-scoped.

These are deterministic fixture counts, not comparative estimates of human assistance. The common scripted action sequences do not model how user behavior would change under each policy, so differences in errors/queries are not causal user outcomes. The two-observation threshold is arbitrary and is not a production recommendation.

## Instrumentation limitation

The candidate's policy transition logic uses the evaluator `target` only to append `wrong_proposal` scoring metadata after each decision; it does not use that label to select routes, proposals, or state transitions. However, the policy runner and scorer are in the same process and the candidate fixture contains those labels. Therefore this is not a process-isolated blinded-evaluator test. A future confirmatory allocation should separate the scoring process and feed the policy a target-stripped input; A01 is preserved as run and was not rerun or rewritten.

## Execution and checks

The pre-formal freeze is commit `0185454d0f5f35506fefffce3e908838e17e675b` on base `75bfe2badd49376ac33cd8a87030e7a6a3396ecf`. Raw output, independent audit, command metadata and hashes are retained beside this report.

OrbStack was not used: current Issue #8200 evidence reports the containerd content store still failing image inspection (`operation not supported`) and no other container runtime is installed. This standard-library fixture ran on host macOS 27.0 arm64 / Python 3.12.13. No container/network isolation is claimed.

- Construction tests: 7/7 passed before freeze and after formal execution.
- Formal independent audit: 78/78 rows, zero errors; mutation controls 7/7 rejected.
- Construction suite (the exact package CI command), retained-result index check, and `git diff --check`: passed during final packaging.
- GitHub Actions Analysis Index remains an external PR check; no workflow result is inferred from these local commands.
- Scope: no human participants, model, GUI, network, application effect, private utility inference, consent UX, safety, or transfer.
