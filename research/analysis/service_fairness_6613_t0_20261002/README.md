# Issue #6613 T0 — long-horizon service fairness

This is a finite deterministic method study, not a live multi-user GUI or human-equity result.

## H / T / D / C / U

**H.** With identical admission predicates, a per-principal service-debt scheduler will reduce the longest consecutive bypass streak and starvation episodes for repeatedly eligible principals versus FIFO, fastest-ready and short-window batching, without violating a frozen floor for independently verified on-time effects.

**T.** Replay the same frozen synthetic traces under four deterministic policies. The traces include equal load, asymmetric repeated arrivals, bursty variable-duration work, a revoked principal, a missing joint grant, an unsuccessful attempted effect, a mandatory release, and an all-ineligible stream. Candidate emits only dispatch attempts and timing. A separate auditor replays the public traces independently and joins outcomes to a hidden effect ledger. Construction mutations cover counting denied work as starvation, crediting attempts as verified effects, allowing deficit to bypass authorization, and suppressing mandatory release.

**D.** `METHOD_PASS_SCOPED` only if all policy rows are independently reconstructed; no denied, revoked, expired, conflicting or missing-joint-grant request is dispatched; the release precedes any dispatch at its event time; attempts count as verified only when the hidden effect ledger confirms them; service-debt strictly reduces maximum consecutive eligible bypasses against each baseline in the frozen asymmetric trace; the minimum on-time verified-effect floor is met in every eligible policy/trace; and all four corruptions are rejected. Otherwise preserve FAIL/HOLD/STOP without rerun.

**C.** Authored arrival/service distributions may favor a policy; service cost is known here but not in a real GUI; and a finite trace cannot characterize strategic requesters or feasibility under sustained overload.

**U.** No real principal, human request, model, GUI, authority decision, latency benefit or production fairness is established. The result is method-only for this finite simulator.

## Execution and scope

The WSLc/OrbStack shared runtime was not used; the simulator is tiny, pure Python and deterministic, and shared runtime workers were active. It ran once on the local Windows host CPU using CPython 3.11.9 and the standard library. No GPU, CUDA, model, GUI, input, network, install, stress test or user data.

Run `python -B -m unittest -v test_method.py`, then exactly once each:

```powershell
python -B run_candidate.py candidate_raw.json
python -B run_audit.py candidate_raw.json audit.json
```

The candidate does not read `oracle_truth.json`. Raw outputs are collision-guarded and immutable after the one-shot run.
