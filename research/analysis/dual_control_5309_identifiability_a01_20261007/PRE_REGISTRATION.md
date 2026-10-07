# Issue #5309 identifiability A01 — pre-registration

Status: PRE-RUN; no candidate or oracle has been invoked.

## H / T / D / C / U

- **H:** A one-step entropy/information-gain selector and repeated success on a benign branch can leave a pair of hidden states observationally equivalent even though the states require incompatible future safe commits. A bounded pairwise distinguishability audit will surface every such pair and return `UNKNOWN/YIELD`, without granting authority.
- **T:** Freeze a finite deterministic hidden-state machine, admissible action/observation table, safe-commit mapping, task horizon, expiry, and exogenous opportunity stream. Compare (1) one-step information ranking, (2) repetition of the same benign action, and (3) exhaustive pairwise distinguishability over bounded admissible sequences. Include: a frequent benign branch; an aliased incompatible-commit pair with an admissible separator; an otherwise equivalent pair with no admissible separator; expiry before separation; and a null control where one step already separates. Record proposal, admission/refusal, executed action (including none), and observation separately. Independently score task progress, wrong/collateral effects, and action-induced loss of future eligibility against the paired no-action counterfactual.
- **D:** `METHOD_PASS_SCOPED` only if the exhaustive audit enumerates every relevant hidden-state pair and admissible sequence within the frozen horizon, detects all unseparable incompatible-commit pairs, accepts the separating and one-step-null controls, returns `UNKNOWN/YIELD` when no valid separator remains before expiry, never treats a refused action's counterfactual observation as observed, never grants authority, and matches an independently represented effect/opportunity oracle. `FAIL` on a missed pair, false rejection of a valid separator, authority promotion, or misattributed counterfactual observation. `HOLD` if the hidden-state set, admissibility, or independent oracle cannot be pinned.
- **C:** Explicit safe probes plus existing freshness/risk gates may suffice; a finite pairwise audit may add needless cost or reject useful paths. A fixed fixture may make the separator or branch too easy.
- **U:** Completeness is only relative to the declared finite state/action/horizon model. It establishes no global impossibility, UI transfer, nonstationary behavior, live safety, or task utility.

## Frozen comparison rules

All arms receive the same already-admissible action set and exogenous opportunity schedule. A guard refusal is recorded as a proposal/refusal with `executed_action=null` and `observation=null`; no belief update may use its counterfactual. State displacement/opportunity loss is measured only by comparing the same exogenous stream under the independently scored executed trajectory and the no-action counterfactual. Information gain is advisory and cannot change admission or authority.

## Execution boundary

Pure deterministic CPU method fixture; no model, GUI, network, external action, or live allocation. OrbStack is preferred, but preflight found image enumeration failing with containerd `operation not supported`; no unrelated existing VM/container may be borrowed. If no safely addressable cached image can be established, preserve a pre-invocation STOP rather than repair OrbStack or pull/build an image without user direction.

Frozen checkout: `research/8135-persistent-counterparty-t1-prep-main2c1c90-20261005`, HEAD `133dafbd8f616b7d2f2ca8b14a3ba863b63f0933`. The pre-existing untracked #8135 package is outside this new directory and must remain untouched.
