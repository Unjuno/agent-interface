# Issue #6147 T0 freeze — safe distinguishing probes for aliased states

## Identity and ownership

- Allocation: `AI-6147-T0-20261002-02` (fresh; no predecessor outputs, outcomes, or seeds reused)
- Owner: Codex autonomous-research thread `01a0b990-3d17-72f1-a908-9a2072104ce5`
- Repository base: `Unjuno/agent-interface` `main` at `fe0f2117810d52b1997bf1513cf3da68ef6a2278`
- Freeze window (UTC): 2026-10-01 17:28–18:05
- Additive output: `research/analysis/safe_probe_identifiability_6147_t0_20261002_a02/`
- Planned branch: `research/safe-aliased-probe-6147-t0-20261002-a02`
- No shared GPU/Docker coordinator resource requested: this is a CPU-only finite analytical fixture, not a GUI/live allocation.
- Governing context read at freeze: README blob `f8cf85390eda4c6d26ceaf8e7df995e8132e504c`; CURRENT_GOAL blob `dd6d691331bd602f97d9aa0e3f52fc6202b06525` (r133: retained v38/v39 posthoc only, no new model/GUI calls); ROADMAP blob `c322beb5fc2a9f6217dd3cc6205b9cbf05e84c19`.
- Collision check: #6147 open; no matching PR or branch; its two comments are specification/impossibility reasoning only and contain no executed T0. No other allocation or owner found for this exact ID/path.

## H / T / D / C / U

**H.** On a finite deterministic fixture with aliased initial outputs, exhaustive safe-probe reasoning will (i) find a minimum depth-two sequence that separates action-different states, (ii) stop without claiming hidden identity when the candidate states are action-equivalent, and (iii) return YIELD for action-different states related by a safe-output-preserving bisimulation, while excluding an unsafe but informative probe.

**T.** No-model/no-GUI exhaustive CPU method check. Freeze three independent two-hypothesis cases, each initially outputting `READY`:

1. `separable_action_different`: safe `p` preserves alias and moves to a state where safe `q` yields `LEFT`/`RIGHT`; `q` first and `recapture` do not distinguish. The action/effect envelopes differ. Unsafe `u` is deliberately outside the admissible alphabet and would distinguish immediately.
2. `action_equivalent_alias`: hidden states stay output-aliased, but the declared safe next-action/effect envelope is identical; terminal action-equivalence is sufficient and must not be reported as singleton identity.
3. `safe_bisimulation_impossible`: different action envelopes remain output-equivalent under every safe probe; relation `R={(E0,F0),(E1,F1)}` is output-equal and closed under `p`, `q`, and `recapture`. Unsafe `u` distinguishes, but remains excluded. Distinguish an exhaustive finite-depth miss from the separate exact unbounded relation certificate.

Enumerate every admissible output-contingent policy tree for depth limits 0, 1, and 2, with unit probe costs. A resolved leaf is either a singleton hypothesis or an action-equivalent belief; otherwise the only safe terminal is `YIELD`. Select minimum worst-case depth, then worst-case cost, total leaf depth, then canonical JSON lexicographic order. Retain every tree/branch partition and a deterministic digest. A separate raw-only auditor reconstructs the fixture independently, enumerates all trees using a separate implementation, validates every branch and the selected optimum, exhaustively checks fixed safe words (complete for these deterministic two-hypothesis cases), and checks closure of `R`.

Five frozen corruptions must be rejected: admitting unsafe `u`; deleting an observed-output branch; claiming a singleton from an aliased observation; using a non-closed bisimulation relation; and treating same-image `recapture` as state identification.

**D.** `PASS_METHOD_SCOPED` only if (a) all tree sets, partitions, counts and digests match the independent auditor; (b) case 1 has no depth-1 solution and a minimum depth-2 solution; (c) case 2 terminates immediately as action-equivalent, not singleton; (d) case 3 has no safe solution through depth 2 and the exact relation proves all-safe-word ambiguity; (e) unsafe `u` is never admitted; and (f) all five corruption controls reject. Any mismatch is `FAIL_AUDIT`/`FAIL_METHOD`; missing/invalid raw or runtime failure is STOP/HOLD, never retried.

**C.** A typed application/effect query or ordinary YIELD may be simpler; fixture separation can be an artifact of its transition table. An action-equivalence annotation is useful only if independently established and current.

**U.** Finite deterministic machine only. This is not evidence that real GUIs are finite/stationary, that any real probe is safe, that hidden state is identified in an application, or that action/effect authority is granted. No product, runtime, or Issue #59 empirical claim.

## Frozen source and execution

- Candidate source: `candidate.py`, SHA-256 `2347d25ea8185a9c495c3582852e007d8a6a07afd6a083d04a53ad4a978cd5d7`.
- Independent auditor source: `audit.py`, SHA-256 `944858325f54bf3f45f3298ba0326927dc2ee8ded5b58722ddc0db92a89036e7`.
- Interpreter: host CPython 3.11.9, executable SHA-256 `5f7b89a612c9b8af1d6456cdfcd1dbe5ca630849e79aebced9bee9a6694952ec`; standard library only.
- Formal commands, each once: `python -I candidate.py --raw RAW.json`; then separate process `python -I audit.py RAW.json`.
- Candidate invocation=1; auditor invocation=1; retries=0; no model, GPU/CUDA, GUI, game, network, physical input, or container workload.
- Docker readiness diagnostic only: Docker CLI 29.8.0; `docker info` read-only probe timed out after 7 s while Docker Desktop/backend were already running and WSL `docker-desktop` reported Running. No service restart or other workload interruption. This small deterministic method run therefore uses host CPU; the diagnostic is not an experiment result.
- Output-collision gate: raw path is a new allocation-specific file under this fresh path and must not already exist before candidate invocation. Never overwrite. If it exists or an invocation begins and fails, preserve first bytes/status and stop.

## Frozen report status

The predecessor freeze `AI-6147-T0-20261002-01` was withdrawn before candidate or auditor invocation because main advanced from `a39606e...` to `fe0f211...`; its branch remains unexecuted and its output path is unused. No candidate or auditor has run for this allocation as of freeze. Record the first raw outcome, independent audit, commands, process exit codes, and hashes additively. No result or claim may be inferred from construction/syntax review.

