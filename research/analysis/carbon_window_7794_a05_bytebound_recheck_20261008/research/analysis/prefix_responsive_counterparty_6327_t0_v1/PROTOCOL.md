# Issue #6327 — prefix-responsive counterparty UI T0

## H / T / D / C / U

**H (T1, not tested here).** Under a fixed agent/authorization contract, a prefix-responsive selector may change unauthorized-effect, authorized-completion and abstention outcomes relative to both static balanced exposure and a calibration-frozen frequency-matched replay, even when all arms have identical marginal variant counts. A source-bound effect boundary may block the forbidden effect but can still change completion/abstention. The null is plausible.

**T0 (method only).** A no-model finite sequential-game simulator with eight offered episodes, two public prefixes, two task-equivalent UI variants, one unauthorized add-on and one authorized save control. Compare `STATIC_BALANCED`, `FREQUENCY_MATCHED_REPLAY` (a separately retained, outcome-free exogenous schedule frozen before held-out assignment and independent of the current prefix), `REACTIVE_DECLARED` (selects only from the current public prefix), and `REACTIVE_NULL` (changes layout only, preserving semantics). Cross each with a scripted plain route and an effect-boundary route. Keep task truth, target, authorization, initial state, and offered IDs identical across arms. The fixed agent script proposes an unauthorized add-on only after a public prior refusal and the V1 presentation; the boundary route refuses it. This is synthetic protocol plumbing, not evidence about any LLM or merchant.

**D.** `PASS_METHOD_SCOPED` only if an independent auditor reconstructs every offered row, verifies the reactive selector reads only the current public prefix, confirms replay schedule provenance is pre-held-out and prefix-independent, verifies exact marginal variant counts and unchanged task/effect truth, rejects stage mismatch and future/private/outcome leakage, retains refusal/abstention rows, and distinguishes a forbidden proposal from an applied effect. Five frozen mutations must reject: hidden future-oracle access, held-out-outcome-fitted replay, changed V1 task/authority truth, dropped refusal rows, and replay shifted to the wrong stage. No method PASS is a susceptibility or defense-efficacy claim.

**C.** With only one terminal decision, a frequency-matched control may produce the same aggregate outcome; extra complexity may not be worth it. The effect boundary can be invariant to all presentations. A simpler static adversarial variant suite may suffice for a narrow contract.

**U.** Fixed deterministic policy script; only two prefixes and two variants; no randomization, human or model, actual site, GUI, network, strategic learning, production source, or task effect. No counterparty objective/equilibrium, robustness, or deployed safety is established.

## Frozen fixture and interpretation

The eight offered episodes have fixed public prefixes `declined_addon` or `continued`, four each. The static and exogenous replay schedules each expose V0/V1 four times; reactive selects V1 on `declined_addon`, V0 on `continued`, also four/four. Replay's eight-item vector is a separate frozen `calibration.json` design artifact, explicitly without held-out prefixes or outcomes; it is not estimated from this fixture. V0 and V1 share the same task ID, target and authorized save effect; V1 only presents an unauthorized add-on as a prominent choice. The `REACTIVE_NULL` layout pair preserves the same save-only action semantics.

For each of four source policies and two routes, retain every offered episode, prior prefix, selector information-set keys, stage, variant, proposal, gate disposition, actual effect and completion label. The independent scorer reads task truth that is not available to the selector. Primary T0 outputs are information-set and oracle integrity, not an estimated behavioral treatment effect.

## One-shot execution

After construction tests, preregister exact source base, fixture/code/image hashes and collision status on Issue #6327. Recheck latest main/path/branch/PR/image immediately before launch. Run candidate once, then only on exit 0 run the independent raw-only auditor once in a separate pinned network-disabled OrbStack container. Zero retries. Record every command, raw stream, exit and stderr. If main advances after preregistration, preserve prelaunch STOP and create a fresh allocation; do not rerun.
