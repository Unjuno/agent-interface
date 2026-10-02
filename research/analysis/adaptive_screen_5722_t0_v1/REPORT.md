# Issue #5722 T0 result — safety-gated screening and sealed confirmation

## H / T / D / C / U

**H.** In the declared finite heterogeneous world, a balanced safety-gated screen can find a correctness-preserving candidate that passes a separate sealed matched confirmation using fewer development opportunities than safety-gated equal-full evaluation. Easy-first scalar screening can falsely eliminate the delayed-recovery candidate.

**T.** Frozen inputs and source are in `FREEZE.md`, `world.json`, `runner.py`, and `audit.py`, committed before execution on branch `research/5722-screen-confirmation-t0-20261001` at freeze commit `80dc1136b12b8c5c9d59bd14fc389597a6440cc0` (base main `5ff239141f49c1603c0f6b078268f4a2f6e082df`). Exact-byte GitHub readback passed before the run. Candidate and independent raw-only auditor were executed once each, sequentially, on Windows host CPython 3.12.10. No Docker container was launched.

**D.** `PASS_METHOD_SCOPED` for this finite T0 only. Equal-full used 26 development opportunities; adaptive screening used 20 and saved 6. With the same 12 setup resource units charged to each policy, total declared resource units were 38 versus 32. The naive easy-first control falsely eliminated `slow_recover` after its 0/2 early easy score; the balanced policy stopped `unsafe_easy_first` on its first hard-stratum forbidden effect and labeled `weak` as `ELIMINATED_BY_SCREEN_NOT_PROVEN_INFERIOR`. It selected `slow_recover`. In the separate 16-attempt sealed cohort, `slow_recover` had easy 3/4 (baseline 3/4), hard 3/4 (baseline 2/4), and no forbidden effects. The confirmation rule passed. A separate auditor did not import the candidate and independently reconstructed all schedules, 56 development attempts across the three policies, and all 16 sealed attempts; it rejected 6/6 corruptions (missing attempt, duplicate sealed variant, forged safety record, wrong selection, sealed/development reuse, and promotion under contention).

**C.** All outcomes and setup costs are authored, deterministic table values. The screen's weak-arm disposition is budget elimination, not proof that the arm is inferior. Equal matched evaluation remains simpler and may be preferable when affordable.

**U.** This is host-only synthetic method evidence, not a Docker result or empirical Agent Interface result. It makes no claim about real GUI efficiency, safety, model behavior, task effects, candidate superiority, or actual shared-resource savings. No live T1 allocation is requested or authorized.

## Execution receipts

- Candidate command: `python -B runner.py`; exit 0, invoked once. Exact stdout: `runner.stdout.json`. Retained raw: `candidate_raw.json`, SHA-256 `0257be0e634a76700046c069143bb6a5abca35e5dcece3ae9c2eb9acd4d2aae3`.
- Independent audit command: `python -B audit.py`; exit 0, invoked once after candidate exit 0. Exact stdout: `audit.stdout.json`. Retained audit: `audit_result.json`.
- Candidate and audit source hashes were frozen before execution; `SHA256SUMS.txt` records the frozen input/source set. `RESULT_SHA256SUMS.txt` records raw and audit artifacts.
- No retries, model, GPU, GUI, game, X11, input, network, or GitHub Actions were used.

## Container disposition

The issue's T0 is a no-model finite simulator and requires no live allocation. The user prefers containerized iteration, but Docker Desktop's Linux engine was unavailable at this run: `com.docker.service` was stopped; `docker desktop start --timeout 60` returned “Docker Desktop is already running” without making the engine responsive. Shared queue Issue #5085 still records four nonterminal Created containers with unresolved lifecycle/ownership. No container inventory mutation or restart was attempted. Therefore this T0 used the permitted host-only fallback and is explicitly not represented as container evidence.
