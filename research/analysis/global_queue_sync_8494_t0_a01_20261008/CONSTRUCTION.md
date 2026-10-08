# T0 A01 construction and gate freeze

## Scope and lineage

Issue [#8494](https://github.com/Unjuno/agent-interface/issues/8494), a CPU-only discrete-event method discriminator for cross-session synchronization under a shared delayed congestion signal. This is additive and does not change #6650's per-stream persistence-control question, #5372's admission policy, or #5494's retained-event policy. No live queue, model, GUI, user data, GPU, external service or product scheduler is exercised.

## H / T / D / C / U

**H:** On matched offered optional arrivals and one shared service bottleneck, a common synchronous gate (SYNC) creates more aligned pause/resume transitions and worse aggregate optional queue-age / useful-before-expiry service than a bounded deterministic per-session phase-offset gate (DECORRELATED), while preserving the per-session worst-service bound. INDEPENDENT is retained as a no-phase baseline. Independent-bottleneck and immediate-accurate-feedback cases are negative controls.

**T:** One deterministic discrete-time simulator; fixed work offers and unit service capacity. Policy decisions may defer only not-yet-created optional work; all offered IDs remain in an explicit ledger. Compare SYNC, INDEPENDENT, DECORRELATED on the same scenarios. Formal candidate and independent auditor are each invoked once. Mutations: missing offer, cross-session identity swap, policy/seed drift, and mandatory loss. No retries.

**D:** `METHOD_PASS_SCOPED` only when the independent auditor reconstructs all offered/delivered/deferred IDs and matched loads; mandatory work is never lost; DECORRELATED improves the frozen primary aggregate queue-age endpoint over SYNC and reduces transition-coherence on shared/delayed feedback scenarios; and per-session fairness stays within the frozen bound. `HOLD_NO_SYNCHRONIZATION` if SYNC does not produce higher alignment than the independent/negative controls. `FAIL_METHOD` for ledger/mandatory/fairness failure or if reported gains use unequal offered load. No product/runtime inference.

**C:** The finite controller may manufacture phase locking; fixed workload may favor chosen offsets; queue-age summaries may hide starvation; #6650's persistence estimator or #5372's admission policy may already remove the effect; provider quotas and service variation are absent.

**U:** Synthetic discrete-event evidence only; no inference to live sessions, service benefit, human tempo, operational fairness, or adoption of randomized pacing.

## Frozen test construction

- Sessions: four stable IDs; unit service per tick, with shared FIFO bottleneck except negative-control scenario.
- Each scenario provides a frozen offered-arrival trace, service variant, and feedback-delay condition. All three policies see the same offered IDs and work costs.
- A request's residence is `service_tick - offer_tick`; it is useful only if served before its frozen expiry. Mandatory records bypass the throttle and are separately counted; no evidence is deleted.
- SYNC decisions share one pressure phase. INDEPENDENT uses per-session pressure observations with the same threshold/hysteresis but no deliberate offsets. DECORRELATED applies a deterministic `(session_index mod 4)` tick phase to optional generation/resumption only; it does not change service priority or offered ledger.
- Primary endpoint: total expired optional requests on declared shared-bottleneck/delayed-feedback cases. Co-primary mechanism endpoint: cross-session pause/resume transition coincidence in a fixed two-tick window. Guardrails: per-session useful delivery, max queue age, offered-load equality, mandatory conservation.
- Controls: underload/immediate-feedback and independent-bottleneck scenarios should not show an artificial shared-feedback synchronization advantage.

## Construction boundary

The implementation, tests, exact scenario matrix, analysis code, hashes, container preflight and resource decision are to be frozen before the one formal candidate and one independent audit. A container/engine failure is STOP for the environment gate, not permission to silently use host execution. This file records design only and is not an experiment result.
