# Issue #7822 A02 — executable bounded-progress synthesis

**Disposition: `PASS_METHOD_SCOPED` for the six frozen finite event graphs.** Unlike A01's authored witness trace, A02 computed finite-horizon policies from the public transition graph and contract, then a separate auditor independently enumerated supervisor choices against a hidden oracle. No candidate action was applied to an application.

| Frozen case | Candidate/auditor result |
|---|---|
| Safe WAIT cycle with a verified progress route | Minimal bound 1. Ordinary safe nonblocking remained true while admitting the reachable non-marker cycle; the bounded policy removed WAIT. |
| Two forced asynchronous events then verified progress | Minimal bound 3; all possible paths stay safe and reach the marker. |
| Uncontrollable self-cycle plus a marker route | `SAFE_YIELD`; the environment can repeat the uncontrollable event forever, so no finite bound is reported. |
| Attempt with no marker evidence | `SAFE_YIELD`; no completion claim or application action. |
| Safe and unsafe controllable alternatives | Bound 1 using the safe edge; unsafe edge excluded. |
| Public task contract conflicts with the hidden oracle | The candidate proposed a bound from the declared contract; independent audit returned `HOLD_TASK_CONTRACT_ORACLE_DISAGREEMENT`, with no completion claim or application action. |

The independent raw auditor returned no errors and rejected all six frozen mutations: re-enable the WAIT cycle, suppress a mandatory uncontrollable tick, enable an unsafe edge, assert completion from a proposed policy, understate the horizon, and promote a policy under the conflicting task contract. Candidate and auditor were each invoked once; retries were zero.

## H / T / D / C / U

- **H:** Supported only on these finite graphs: ordinary finite-trace nonblocking can permit a safe infinite non-goal loop, while a rank-decreasing bounded policy can remove that loop when controllable progress exists. No finite bound is sound when an adversarial uncontrollable cycle remains.
- **T:** One candidate process read `public_cases.json` only. After it exited 0, one separate auditor process read the public graph, hidden `oracle_cases.json`, and immutable candidate raw output. The auditor independently enumerated controllable edge subsets, checked mandatory uncontrollable transitions, exact minimal horizons, policy closure, safety, evidence, and mutations.
- **D:** `PASS_METHOD_SCOPED`; all eligible cases matched the independent result, required no-progress/contract-conflict cases were held or yielded, and all six mutations were rejected.
- **C:** A small explicit no-progress/YIELD handler could be simpler than a general supervisor. The authored contract and graph may still encode the desired policy, and this experiment does not compare implementation cost or practical utility.
- **U:** Six hand-authored, fully observed graphs; no partial observation, real task oracle, GUI, model, input, wall-clock deadline, human/model delay, runtime integration, or application effect. `YIELD` is represented only by the frozen zero-app-effect control-plane contract. Transition bounds are event counts, not time guarantees. This is not a live safety or task-completion result.

## Provenance

Base main: `4670a6fb5bc152087054ad84ff15cc8148f7683c`. Freeze and preformal source/input hashes are in `FREEZE.json` and `SHA256SUMS.txt`. Construction checks passed 7/7 before formal freeze. Formal host: macOS arm64, CPython 3.14.5, standard library only, no network or container. Commands, exit codes, invocation counts, and raw digests are in `RUN_RECORD.json`. A01 at PR #7835 remains unchanged; A02 is a separate allocation and does not retroactively repair or replace it.
