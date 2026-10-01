# Issue #6256 T0 — backward-derived observable guards

## H / T / D / C / U

**H.** On a finite typed transition table, universal backward preimage enumeration identifies missing and overstrong authored guards, preserves exact-effect, forbidden-prefix, bounded-termination, and verified-empty-release obligations, and returns `UNKNOWN_NOT_OBSERVABLE` when permitted fresh evidence cannot distinguish states with different safe outcomes.

**T.** Allocation `BACKWARD-OBSERVABLE-GUARDS-6256-T0-20261002-01`. Freeze `MODEL.json`, `candidate.py`, `audit.py`, and `test_model.py`; run construction tests before freeze. Then run the deterministic candidate once and, only after candidate exit 0, one independent raw-only audit. The action horizon is 3 steps. Enumerate every declared outcome, compute the universal total-correctness preimage, enumerate permitted cue subsets for the predeclared `certificate_status=verified` stratum, and classify all full-cue belief cells. Compare a loose hand-authored guard and a layout-overstrict guard. Include nondeterministic save/no-effect, same-pixel committed/uncommitted, stale-generation, release-failure, late-completion, and unobservable silent-effect alias cases. Retries: 0. No GUI, model, user files, network, external actions, or OS input. Host CPU fallback is used only because the Docker Desktop daemon/status calls do not return; the computation is a pure finite enumeration.

**D.** `PASS_METHOD_SCOPED` only if the candidate and independent oracle agree on every outcome and preimage state; a minimum sufficient cue set exists in the verified stratum; the pixel-only duplicate alias is `UNKNOWN_NOT_OBSERVABLE` while a fresh typed commit receipt separates that pair; the missing-certificate safe/silent alias remains UNKNOWN; every mutation control exposes its unsafe shortcut; and no admitted belief cell contains a state outside the exact preimage. Otherwise retain FAIL/HOLD/STOP unchanged.

**C.** The state/outcome table is an authored deterministic simulator. Its completeness is assumed for this finite method check; the audit independently evaluates the frozen table, not real application semantics.

**U.** No real GUI, tool transport, task success, physical input, model behavior, general guard synthesis, live safety, latency/efficiency benefit, or product claim. A finite method PASS does not authorize an interaction or replace post-action effect verification.

## Pre-execution record

- Current base at freeze: `2610efa8e5dd577e5cffb0753f9744e092b8caa6`.
- Construction checks before freeze: 7 unit tests passed; Python syntax and JSON parsing passed; no candidate output was generated.
- Frozen source/input SHA-256 identities are in `FREEZE.json`.
- Candidate invocations: 0; independent audits: 0; retries: 0.
- Environment: Windows 11 host, CPython 3.12.10, Docker context `desktop-linux`. Docker Desktop/backend processes and named pipes exist, but `com.docker.service` is Stopped and `docker desktop status` did not return within 15 seconds; the bounded status request was interrupted. No service, engine, container, or shared resource was started/stopped or modified. Because this test is a deterministic finite-state computation with no external effects, proceed on host CPU under the explicit fallback; no Docker workload is claimed.
