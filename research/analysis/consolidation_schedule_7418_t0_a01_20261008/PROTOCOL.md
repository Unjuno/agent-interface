# Issue #8406 T0 A01 — frozen schedule-sensitivity contract

## H / T / D / C / U

**H.** For one fixed, ordered, source-bound finite episode ledger, four consolidation schedules produce aligned but schedule-specific intermediate derived-memory states. The T0 claim is only that the schedule intervention, immutable ledger, query checkpoints, provenance, rare exception, contradiction, history delta, and held-out unknown are represented and independently auditable. It does not claim that any LLM behaves differently.

**T.** Process the same six episodes through `episodic_only`, `per_episode`, `batch_2`, and `terminal`. Snapshot every arm after each prefix 1–6 (24 snapshots). All snapshots retain the same full episode ledger digest, the exact prefix IDs/digest, the same five query IDs, and the same fixed zero-model-call budget. `episodic_only` performs no abstraction rewrite; per-episode updates six times; batch size two updates three times; terminal updates once at prefix six. A deterministic transformation derives a common success pattern only after two source episodes, a source-linked rare forbidden-effect exception, an `UNKNOWN` for two conflicting verified observations, and a source-linked baseline/current history delta. A held-out conjunction is never emitted as a claim.

A separate raw-only auditor independently enumerates all expected prefixes, updates, state digests, claims, source links, and budgets without importing the candidate. Frozen hostile controls alter an episode, drop the exception, remove provenance, silently resolve a contradiction, misalign a checkpoint, infer the held-out conjunction, and change the query budget.

**D.** `PASS_T0_METHOD_SCOPED` only if the audit reconstructs the immutable six-episode ledger and all 24 snapshots exactly, confirms the four schedules' update totals (0/6/3/1), all source/provenance and conflict/UNKNOWN conditions, identical query checkpoints/budgets, and rejects every frozen mutation. Otherwise preserve `FAIL`/`STOP`. No T1/model endpoint is measured here.

**C.** The schedule harness and memory transformation are hand-authored; a clean audit proves the fixture contract only. A difference among stored intermediate states does not imply a downstream task answer changes.

**U.** No LLM, GUI, user data, action, memory writeback, task accuracy, token use, latency, safety, or optimal cadence result. One synthetic corpus cannot estimate real exception frequency or schedule effects.

## Source and environment

The episode ledger and query set are `model.json`; candidate, auditor, and mutation controls are frozen by SHA-256 in `FREEZE.json`. The process is native macOS CPython under `sandbox-exec` with network access denied. This is a small deterministic no-model CPU fixture; it is not a Docker/OrbStack or resource-cap reproduction. No GUI, OS input, external effect, or model service is used.

## Frozen commands

Run from the repository root, once each, in order, with zero retries:

1. `sandbox-exec -p '(version 1) (allow default) (deny network*)' python3 research/analysis/consolidation_schedule_7418_t0_a01_20261008/candidate.py research/analysis/consolidation_schedule_7418_t0_a01_20261008/model.json --output research/analysis/consolidation_schedule_7418_t0_a01_20261008/results/FORMAL_A01/candidate.json > research/analysis/consolidation_schedule_7418_t0_a01_20261008/results/FORMAL_A01/candidate.stdout.txt`
2. `sandbox-exec -p '(version 1) (allow default) (deny network*)' python3 research/analysis/consolidation_schedule_7418_t0_a01_20261008/auditor.py research/analysis/consolidation_schedule_7418_t0_a01_20261008/results/FORMAL_A01/candidate.json --output research/analysis/consolidation_schedule_7418_t0_a01_20261008/results/FORMAL_A01/audit.json > research/analysis/consolidation_schedule_7418_t0_a01_20261008/results/FORMAL_A01/auditor.stdout.txt`

The candidate and auditor create their JSON outputs exclusively (`open(..., "x")`). At freeze, formal candidate/auditor invocations are 0/0 and retries are 0. Construction tests are separate from formal execution.
