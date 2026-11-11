# Architecture audit: make implicit control state explicit (proposal, not runtime promotion)

**Date:** 2026-11-06. **Source baseline:** main `57573394c4d88988a40b0e57c270c945a3a621cd`. **Status:** design review and test contract only; no runtime change, no live input or performance result. Parent research: [#5320](https://github.com/Unjuno/agent-interface/issues/5320), [#5704](https://github.com/Unjuno/agent-interface/issues/5704), [#1657](https://github.com/Unjuno/agent-interface/issues/1657), [#59](https://github.com/Unjuno/agent-interface/issues/59), [#57](https://github.com/Unjuno/agent-interface/issues/57), [#9004](https://github.com/Unjuno/agent-interface/issues/9004).

## 1. What was inspected and what was not

Inspected current main's `README.md`, `docs/architecture.md`, `docs/principles.md`, `ROADMAP.md`, `docs/CURRENT_GOAL.md`, `docs/WORKER_WORK_MAP.md`, `runtime/README.md`, `runtime/kernel/contracts.py`, `runtime/kernel/lifecycle.py`, `runtime/cli_v1/attempt.py`, `runtime/cli_v1/owned_guarded_session.py`, and directory inventory of `runtime/core_v1`, `runtime/kernel`, and `runtime/cli_v1`. Checked related open Issue and PR titles. This is **not** an exhaustive review of every source line, OS backend, GUI, or external dependency; do not use it as an all-code audit certificate.

The current `RequestLifecycle` is already a real explicit *per-request* state machine: NEW → OBSERVED → BOUND → AUTHORIZED → EXECUTED → VERIFIED / CONTRADICTED / UNAVAILABLE, with STOPPED. Its `record_execution` requires a released terminal receipt. The CLI `attempt.py` separately has durable request/report files and an explicit UNKNOWN/no-replay rule. The owned X11 session separately tracks process, held-input obligations, cancellation, worker retirement and external readback. These are useful and should **not** be replaced by a new global enum.

**Architectural gap (inference, not a proven defect):** the composed public path has *multiple concurrent state axes*. A single request stage or a successful process exit cannot encode input custody, external effect uncertainty, late delivery, generation, and report persistence simultaneously. Historical R06's post-cancel duplicate A effects and UNKNOWN cleanup, and R23's receipt-overhead result, are concrete reasons to test this composition. They are **not** proof that this exact missing product model caused either failure.

## 2. Explicit product state (do not collapse axes)

| Axis | States / representation | Evidence authority | Non-equivalence |
|---|---|---|---|
| Semantic intent | proposed, scoped, revoked, needs_decision | rich planner's versioned intent plus independent constraints | agreement ≠ permission |
| Observation/binding | absent, fresh(epoch, source, target), stale, unknown | source-bound current capture | pixel change ≠ task success |
| Admission/lease | none, active(epoch, deadline, scope), fenced, expired | deterministic owner admission | expired ≠ physically released |
| Dispatch/delivery | not_sent, admitted, sent_unknown, delivered, rejected | actual backend/transport receipt | RPC accepted ≠ application effect |
| Physical input custody | no_obligation, held, release_requested, release_verified, release_unknown | independent backend/server readback and exact owner | process exit ≠ key up |
| External task effect | none_proven, possible, verified, contradicted, unavailable | independently correlated app/effect oracle | release_verified ≠ effect_verified |
| Cancellation/recovery | idle, requested, owner_retired, reconciling, fenced_unknown, resumable_new_epoch | original and new-generation evidence | fresh task success ≠ old task success |
| Evidence durability | unrecorded, request_durable, result_durable, partial_or_torn, unavailable | exact hashes + file/commit protocol | report persisted ≠ true effect |
| Controller/model wait | running, pending, yielded, terminal | local scheduler/actual provider receipts | model timeout ≠ cancellation completed |

The product is intentionally *sparse*: do not enumerate all Cartesian combinations. Persist only transitions relevant to a particular command/owner, and derive a conservative read-only view from existing source receipts. No extra synchronous receipt is added to the hot path before measuring its overhead.

## 3. Cross-axis invariants and transitions

**I1 (fencing):** any stale observation, changed generation, lost authority, expired lease, unknown identity, or unknown source *disables new consequential admission*. This does not assert that already queued input was undone.

**I2 (custody):** a canceled/retired worker may remain `release_unknown`. Only an authenticated exact-owner, exact-generation, exact-input-obligation neutral readback may establish `release_verified`. Parent cleanup or process exit alone is insufficient.

**I3 (effects):** task success requires a correlated independent effect oracle. If an action was admitted/sent but effect evidence is missing, status stays `possible/unavailable`; no automatic retry, replay or success promotion.

**I4 (monotone uncertainty):** a late successful cleanup receipt may refine physical custody only. It must not rewrite the first failed command, erase old possible effects, or upgrade its task result.

**I5 (generation):** after cancellation, a fresh task may be admitted only with new validated binding/lease and no unresolved *overlapping input authority*. The old generation's effect status remains unchanged. Do not assume all UNKNOWN old effects have ceased.

**I6 (single-owner side effects):** a repeated or out-of-order event with the same command/epoch/idempotency identity must never cause a second admission. Distinguish duplicate *receipt* from duplicate *external effect*; a journal hash chain alone does not prove either.

**I7 (temporal):** timestamps and deadlines use one explicitly declared monotonic clock domain or carry a conversion proof; late arrival does not retroactively authorize a previous action. No wall-clock deadline claims from synthetic ticks.

**I8 (evidence):** report serialization failure retains the original outcome and UNKNOWN durable status. Saved-only audit must detect torn/missing/mismatched records without triggering input or rewriting history.

### Minimal transition table

| Event | Precondition | Allowed state change | Forbidden promotion |
|---|---|---|---|
| observe/bind | trusted source, matching epoch | absent→fresh | binding→authority |
| admit | fresh binding, lease valid, owner available | none→active | stale→active |
| send | active exact lease and command | not_sent→admitted/sent_unknown | sent→verified effect |
| cancel | any in-flight state | lease→fenced; custody→release_requested/unknown | cancel→released |
| owner death | exact owner identity | retire owner, retain obligations | exit→release_verified |
| neutral readback | exact source/owner/epoch, complete held set | release_unknown→release_verified | effect_unknown→success |
| effect receipt | exact command/target/generation, independent oracle | possible→verified/contradicted | effect from unrelated generation |
| new task | new binding/lease, no overlapping authority | new command active; old immutable | old UNKNOWN→success |
| report failure | any | evidence→partial_or_torn | retry or erase prior evidence |

## 4. Design and UX/API improvements

The public API should expose *separate* `control_status`, `release_status`, `effect_status`, `evidence_status`, and `replay_allowed`, plus source/epoch/command IDs. A single `completed=true` is ambiguous. A compact user-facing result can say **action sent / input released / effect unverified**, not “done”. Make `UNKNOWN` an explicit, actionable result; show the smallest next safe step (read-only inspect, rebind, yield, or require independent release) and retain a stable correlation link to raw evidence. Do not expose internal process IDs or unredacted paths to untrusted clients.

Keep the rich model semantic planner, deterministic guard/owner, and independent effect verifier separate. The local System-1 path may act only under current lease and fresh evidence; a System-2 agreement is a planning signal, not a permission token. Favor existing kernel and owner mechanisms; implement a **read-only cross-axis projection/auditor first**, not a second state machine competing for authority.

## 5. Smallest staged implementation (no parallel-worker collision)

1. **P0 — Read-only receipt projection.** In a new additive research path, parse retained public caller, kernel, owner, effect and persistence receipts into the typed axes above. Return UNKNOWN for absent/ambiguous fields. Do not mutate runtime or historical raw. Cross-check against existing tests.
2. **P0 — Counterexample suite.** Frozen traces: cancel while key held; owner dies before release; late input after cancel; repeat-generated extra effect; stale generation; report write torn; duplicate receipt; late cleanup; fresh task while old effect unknown; clock mismatch. Independent expected outcome per trace; mutation tests verify fail-closed behavior.
3. **P1 — Differential replay.** Compare read-only projection with actual current-main public route on the *same* saved traces, normal and `python -O`. A mismatch becomes an Issue with first raw, source SHA and owner; do not silently fix history.
4. **P1 — One opt-in boundary.** Only if a real residual remains, add a small versioned, additive structured status response at the public API boundary. Preserve old fields and semantics; reject ambiguous legacy values instead of guessing.
5. **P2 — Controlled end-to-end comparison.** Same model/task/environment and independent effect scorer; compare old/new status projection for accuracy, safety, time-to-useful-feedback, model calls, latency, token and resource overhead. Require a prospective source freeze and separate owner/resource allocation.

**Avoid:** a monolithic central coordinator, extra per-action network calls, reinterpreting synthetic PASS as physical release, changing global input repeat policy, weakening hard gates to improve score, or making System-1/System-2 consensus a mandatory safety authority.

## 6. H/T/D/C/U (proposed gates, not measured)

- **H:** The read-only product projection detects all predeclared cross-axis contradictions that a single terminal status cannot express, with no false VERIFIED/RELEASED and without modifying original receipts.
- **T:** Frozen minimum 10 counterexample traces + 10 valid controls, ≥2 distinct backends/receipt families where available, normal and optimized Python, independent raw-only auditor, at least 5 deliberate evidence mutations. Separate fixture construction from first formal run; no source/threshold changes after freeze.
- **D:** PASS_METHOD_SCOPED iff 20/20 exact classifications, all five mutations rejected, no old-effect promotion after late cleanup, all UNKNOWN preserved, all source hashes verified. Otherwise FAIL/HOLD. Runtime promotion additionally requires a same-task integrated comparison with zero safety regressions and predeclared overhead budget.
- **C:** Existing kernel+CLI guards may already cover all sampled contradictions; new projection may add zero useful information, duplicate logic, or create stale status races. In that case stop; do not promote it.
- **U:** Selection bias in retained traces, unavailable original raw, backend timing/ABI differences, correlated source/effect receipts, missing physical-release oracle, clock-domain conversion and synthetic-vs-live mismatch. No general reliability inference from finite controls.

### Measurement symbols / units

| Symbol | Meaning (日本語) | SI unit | Definition / domain | Type |
|---|---|---|---|---|
| `t` | 単調時計時刻 | s | monotonic per declared clock domain, t≥0 | scalar |
| `e` | 世代番号 | 1 | integer ≥0, no reuse within owner | integer scalar |
| `c` | コマンド識別子 | 1 | opaque nonempty ID, unique within epoch | categorical scalar |
| `S` | 積状態 | 1 | tuple of nine axis values above | finite product |
| `δ` | 遷移関数 | 1 | partial mapping (S,event)→S or UNKNOWN | function |
| `L` | 有効期限 | s | lease deadline in t's clock domain | scalar |
| `Δt` | 実行経路の遅延 | s | end-start on same clock | nonnegative scalar |
| `N` | 検証ケース数 | 1 | positive integer; proposed ≥20 | integer scalar |
| `u_c` | 合成標準不確かさ | s | timing sources only after clock validation | scalar |
| `k` | 包含係数 | 1 | preregistered if uncertainty interval reported | scalar |

Dimensional check: `t`, `L`, `Δt`, `u_c` must all have time dimensions and compatible clock domains; `e`, `N`, `k` and `S` are dimensionless. Do not compare wall-time timestamps to monotonic deadlines.

## 7. Evidence and prior-art boundary

- Session types/typestate (existing [#5320](https://github.com/Unjuno/agent-interface/issues/5320)) concern protocol compliance, not external-effect truth.
- Dijkstra's self-stabilization (existing [#5704](https://github.com/Unjuno/agent-interface/issues/5704), DOI [10.1145/361179.361202](https://doi.org/10.1145/361179.361202)) motivates convergence to *no authority*, not rollback of GUI effects.
- Interface automata learning (existing [#1657](https://github.com/Unjuno/agent-interface/issues/1657)) concerns discovering application transitions, not certifying owner custody.
- Product-state monitoring is related to distributed systems, formal methods, control engineering and human-computer interaction. These analogies do not establish measured speed or safety.

**Decision:** retain existing runtime components and authority boundaries; propose a read-only product-state evidence layer and differential counterexamples. This RFC is an architecture improvement plan and explicit contract, **not** a deployed fix or validated runtime change.
