# Issue #5309 A03 — four-arm held-out dynamics comparison

## Allocation and scope

- Allocation: `5309-FOURARM-A03-HOSTCPU-20261007`.
- Parent question: Issue #5309, “Dual-purpose task actions for safe online interface identification.” A01, A02, historical T0–T6, and the intervening unverified extensions remain immutable and are not replayed.
- Frozen source: repository `main` at `133dafbd8f616b7d2f2ca8b14a3ba863b63f0933`.
- Runtime: host Python standard library. OrbStack is Running, but Docker inventory fails on a containerd content blob with `operation not supported`; no container is claimed. This is a deterministic no-container simulation and makes no network, GUI, model, OS-input, or live-authority call.
- Receipt-schema replay: exact `runtime/kernel/contracts.py` source snapshot from the frozen main commit, exercising `ExecutionReceipt`, `ReleaseReceipt`, and `EffectOccurrence` locally; this validates schema shape only, not backend execution or physical input release.
- The fixture and all synthetic costs/effects are authored, not calibrated observations about a real interface.

## H / T / D / C / U

- **H:** With the same already-admissible task-action set and risk envelope, a fixed advisory dual-purpose ranker can exploit a task action that both advances a common task subgoal and yields a fresh, decision-relevant target observation. Across held-out label/observation mappings, it will lower end-to-end synthetic completion latency relative to task-only retry and explicit probing without increasing wrong-target, collateral, or unsafe effects. Stale evidence, duplicate evidence, a witness-destroying action, and absence of a safe evidence path must not be converted into authority or completion.
- **T:** Exhaustively evaluate four fixed policies over three held-out hidden-state/receipt mappings, both hidden targets, and fresh/duplicate/stale receipt conditions. Also evaluate a probe-cost reversal sensitivity and two boundary profiles (the task action destroys the independent effect witness; no safe evidence path). Policies: `TASK_ONLY` (fastest immediate task action, then fixed alternate after independently detected noncompletion), `EXPLICIT_SAFE_PROBE` (probe then state-matched task action when the fresh receipt is valid), `DUAL_PURPOSE` (fixed `beta=2.0`, rank only admitted task actions by expected immediate progress + beta × expected state entropy reduction − frozen time and risk penalties; risk admission remains an external frozen gate), and `FAIL_CLOSED_UNKNOWN` (yield when the task/effect is not independently verifiable). Candidate and independent auditor are separate one-shot formal invocations. The auditor independently reconstructs outcomes, metrics, receipt freshness/deduplication, effects, and key-release balance from frozen truth, and validates each synthetic execution receipt against the pinned real runtime dataclass contract.
- **D:** `PASS_DUAL_PURPOSE_ACTION_SCOPED` only if on the three preregistered held-out mappings (fresh receipts) DUAL completes every hidden target, its mean synthetic completion latency is strictly lower than both TASK_ONLY recovery and EXPLICIT_SAFE_PROBE, its wrong-target/collateral/unsafe counts do not exceed either comparator, every stale receipt is rejected before a target-specific commit, duplicate receipts are consumed once, every key-down has exactly one matching key-up, no authority is granted, and the witness-loss/no-path controls fail closed. Report fault, cost-reversal and boundary strata separately; never fold them into the primary latency estimate. Otherwise retain a named FAIL/HOLD/UNCERTAIN and do not tune or retry this allocation.
- **C:** Explicit probing can dominate when it is cheaper; task-only recovery may suffice when retries are cheap; the dual-purpose action may be uninformative or destroy the only independent effect witness. Fixed synthetic weights may manufacture the result.
- **U:** No live GUI, backend receipt semantics, physical release, model, latency calibration, risk calibration, application dynamics, user utility, or product safety is established. The finite held-out mappings are authored controls, not a sampled deployment distribution. `beta` and all costs are frozen before the formal run.

## Frozen action/effect boundary

All actions exist only in the simulator. Direct commits are reversible synthetic operations with risk 1 under a frozen risk budget of 1; wrong target is independently counted and incurs the authored recovery penalty. The common-task action has utility 0.25 and may return a target token; the explicit probe has zero task utility. Commit actions emit bounded key-down/key-up pairs to test exact release. These values define this toy model only. The effect oracle, not the policy's information score, decides task completion, wrong target, collateral, and witness availability. Information gain cannot grant admission, authority, or a commit.

## Invocation limits

- Construction tests may be repeated before `FREEZE.json` exists.
- After freeze: candidate formal command exactly once; auditor formal command exactly once; zero retries.
- Syntax, saved-output/hash, and repository CI checks may follow, but must not invoke candidate or auditor again.
