# Adaptive System-1 integration intake

This maps proposals #3440–#3447 to the existing native path. They are research
proposals, not validated implementations ready for automatic adoption. No local
model, router, sensor or background agent is enabled by this intake.

| Proposal | Existing integration surface | Evidence required before adoption |
| --- | --- | --- |
| [#3440 backend candidates](https://github.com/Unjuno/agent-interface/issues/3440) | Proposal produced before NativeDecision / native_submit | Fixed candidate versions, hardware, cold/warm latency distributions, comparison with deterministic control |
| [#3441 adaptation](https://github.com/Unjuno/agent-interface/issues/3441) | Candidate snapshot selected before proposing a decision | Update boundary, snapshot provenance, rollback, update cost and held-out forgetting results |
| [#3442 intent alignment](https://github.com/Unjuno/agent-interface/issues/3442) | Public session_context goal plus source-bound decision | Versioned intent, changed-intent cases; current goal file hash is not a signed intent protocol |
| [#3443 residual controller](https://github.com/Unjuno/agent-interface/issues/3443) | Proposal of an explicit bounded native tail | Declared residual bounds, disturbances, deoptimization and unchanged deterministic execution checks |
| [#3444 visual grounding](https://github.com/Unjuno/agent-interface/issues/3444) | Returned image_reference and source_sequence | Grounding accuracy and abstention on missing/stale/ambiguous evidence; derived coordinates alone are not permission |
| [#3445 validation](https://github.com/Unjuno/agent-interface/issues/3445) | Existing source check, target minting, dispatch and retained result | Model/snapshot provenance and calibration envelope; current protocol checks do not validate a learned model |
| [#3446 routing](https://github.com/Unjuno/agent-interface/issues/3446) | Proposal selection before native_submit | Explicit scope, unavailable/ambiguous adapter cases and interference checks; no existing router is claimed |
| [#3447 evaluation](https://github.com/Unjuno/agent-interface/issues/3447) | Raw MCP responses, requests, application files and cleanup | Matched rich-only/fixed/adaptive arms with frozen model/context, tokens/cost, cold/update costs and independent evaluation |

The checked native path is `NativeDecision` -> `native_exchange_v1.run` source
sequence / immutable request checks -> harness target mint and click/keyboard
dispatch -> feedback and retained observation -> independent application
evaluation -> cleanup and terminal reply. A candidate proposal must enter before
the existing decision boundary. A schema-valid decision alone is not evidence
of grounding, intent alignment, or current execution permission. Existing
resume-by-digest must remain read-only after an ambiguous submission.

For integration work, consume contributors' candidate outputs and versioned
snapshots at that proposal boundary first. Do not install a model merely to
populate an adapter slot. Sensors remain outside this assistant's development
scope. Existing servo review code is a result presentation/checking path, not
proof that a learned residual controller is already integrated.

## What the retained primary-assistant traces can support

Run `python research/live_control/adaptive_system1_intake_v1/inventory.py` from
any directory. It reads three named retained runs without dispatching input and
checks reply/request digests. It reports exact action and initial-image hashes,
tool counts, process snapshots, task results and local SDK intervals.

The three runs have identical action requests and initial image bytes, but
different implementation sources and public task context: the first omitted
the Inkscape task description (see NATIVE_CONTINUATION_GOAL_CORRECTION.md).
They are useful protocol/trace integration fixtures, not controlled A/B/C model
trials or independent held-out model examples. All use the same simple static
Inkscape task. The 4/4/3 tool counts do not imply a causal speed gain: the final
run's submit SDK intervals are approximately 680/626 ms, versus 646/521 ms in
the preceding run. No performance distribution follows from these samples.

Do not feed final replies, evaluator output or saved post-action files into a
candidate's pre-action context. Separate observation/intent from labels if these
records are later exported as a dataset. Recorded source pixels are historical;
replaying them never authorizes new desktop effects.

The next useful contribution to consume is a frozen authority-neutral candidate
with an explicit input/output contract and matched local measurements. Compare
it first against existing explicit decisions, then use a fresh held-out task
with the same execution path. Formal adoption still requires the applicable
container/independent-review gate. No change to the user's WSL-only continuation
or Docker no-restart instruction is implied.
