# Oracle-boundary swaps — Issue #6230 T0

**Overall disposition: `HOLD_AUDITOR_INTENT_EQUIVALENCE`.** The one-shot raw-only audit emitted `PASS_METHOD_SCOPED` and rejected 7/7 implemented corruptions. Post-run static inspection found that the independent audit does not verify the Issue's execution-only pairing invariant: its model intent must equal the matched `actual` arm's frozen model intent. Therefore the formal D gate is incomplete; the raw sub-result is preserved, not promoted to an overall PASS. Candidate and auditor were not rerun or edited.

## H / T / D / C / U

- **H:** In a finite fixed-model fixture, separately swapping observation, execution, or both distinguishes planted semantic-, observation-, execution-, and joint-only failure classes. This is a method hypothesis, not measured or deployable headroom.
- **T:** Seven fixed cases × four arms (28 rows): four diagnostic classes; ambiguous truth; answer leakage; and reset/carryover. Observation oracle must not provide answer, plan or authorization. Execution oracle must preserve the exact intent. All arms must start from the same reset state. The raw-only auditor uses no candidate imports and implements seven corruption controls.
- **D:** `PASS_METHOD_SCOPED` requires exact arm/case accounting, planted outcome matrix, paired frozen-intent preservation, leakage/ambiguity rejection, reset identity, no safety bypass and all corruption controls rejected. The raw audit output meets its implemented checks, but does not check paired actual/execution-only model-intent equality. Overall D is therefore **HOLD**, not PASS.
- **C:** Cases and ground truth are authored, deterministic and deliberately finite. This tests method/accounting logic only, not real models, GUI, actuators, latency, or causal benefit.
- **U:** Oracle sufficiency, oracle-to-deployable evidence gap, adaptation, task transfer, reset quality, population representativeness, model stochasticity, human tempo and independently grounded real task effects remain untested.

## Retained one-shot result

The outcome vectors below are ordered `actual / observation oracle / execution oracle / joint`:

| Frozen case | Effect-correct vector | Interpretation |
|---|---|---|
| Semantic-limited | `0 / 0 / 0 / 0` | Exact execution cannot repair wrong semantics. |
| Observation-limited | `0 / 1 / 0 / 1` | Current task-relevant observation changes the intended effect. |
| Execution-limited | `0 / 0 / 1 / 1` | Exact execution helps when the intent is already correct. |
| Joint-only | `0 / 0 / 0 / 1` | The two interventions interact; gains are not additive. |
| Ambiguous | `0 / 0 / 0 / 0` | All arms marked `UNDEFINED`, no credit. |
| Answer leakage | `0 / 0 / 0 / 0` | Leaking observation-oracle arms are rejected, never credited. |
| Reset/carryover | `0 / 0 / 1 / 1` | Clean formal arms share one initial-state identity; injected contamination is exercised only as an auditor mutation. |

Candidate: one invocation, exit 0. Independent raw-only auditor: one invocation, exit 0; its output is `PASS_METHOD_SCOPED`, zero implemented-check errors, 7/7 mutation controls rejected. Retries/substitutions: 0. Six construction tests passed before freeze; their RED phase first failed (missing implementation), then exposed and led to fixes for planted arm mapping and mutation targeting. No model/provider, network, GUI, game, OS input or external task effect was used.

## Post-run audit gap and disposition

The execution-oracle source fixture sets its intent from the actual arm's intent, and the per-row check verifies `executed_intent == model_intent`. However, `_check` does not compare the `execution_oracle` row's `model_intent` against that case's `actual` row's `model_intent`. Since D requires the *same frozen intent*, a corrupted paired intent could be changed while retaining the Boolean outcome matrix and evade all seven retained mutations. This is a static audit-coverage finding after the one-shot invocation, not a new experiment and not evidence that the candidate actually violated the contract.

The formal raw PASS is retained exactly; the package-level outcome is HOLD. No posthoc source repair, rerun, relabeling or successor allocation is claimed. Any strengthened check needs a separately frozen allocation; it must add a mutation that alters the execution-only model intent relative to actual while leaving its local executed/model-intent equality intact.

## Execution environment and scope

CPython 3.12.10, Windows x64, stdlib, host CPU. Docker Desktop is installed, but `com.docker.service` was Stopped/Manual and the engine status request was unresponsive. This finite no-model method fixture has no container-dependent semantics; no Docker engine, container, WSL or shared allocation was started or modified. Host-only is a scoped fallback, not container evidence. See [RUN.md](RUN.md), [FREEZE.md](FREEZE.md), `candidate.json`, `audit.json` and `SHA256SUMS`.
