# Allocation -03 duplicate formal-seed reconciliation

**Disposition: `STOP_DUPLICATE_FORMAL_SEED_COLLISION`.** The source-bound fresh-seed allocation registered by Issue #5189 cannot be treated as a valid formal experiment because the same allocation ID/path/seeds were consumed in a separate execution before this branch's runner started.

## Evidence and chronology

- Issue #5184 comment [#5863253525](https://github.com/Unjuno/agent-interface/issues/5184#issuecomment-5863253525) reports the competing source/freeze commit `2a96313df5edffb1f7d180bee6c142917ac79e37`, the same allocation -03, path, and seeds 484431/484432, and says no formal runner had started at that point.
- Issue #5184 comment [#5863380137](https://github.com/Unjuno/agent-interface/issues/5184#issuecomment-5863380137) reports that competing Docker runner and auditor had completed, gives the competing raw hash `51d9c7fed88a5a491a7e1f4fb5a33349ffe58c486a44a946b573a1a18838e300`, and reports the same training/test seeds. It explicitly says the run is not an independent replication and must not be pooled.
- Issue #5189 comment [#5863362548](https://github.com/Unjuno/agent-interface/issues/5189#issuecomment-5863362548) independently reports the collision and the same competing raw hash. Comment [#5863398816](https://github.com/Unjuno/agent-interface/issues/5189#issuecomment-5863398816) gives the competing runner start as `2026-09-28T13:18:08+09:00` and compares it with this branch's freeze commit time (`13:22:33 +0900`).
- This branch's frozen source is commit `fcf06f1bf4ce85952658cf9f53e38899dfc51530`; its runner container inspect records creation at `2026-09-28T04:24:55.869523368Z` (13:24:55 JST), after the competing runner's reported start. Its retained raw file hash is `74dfede0db4676fdaf0d6385c625c2c3731a75ffe8572d7f7a45dbc060e42a22` (1,542,155 bytes). Its separate auditor reports 4,800 rows, zero errors and 16/16 corruption controls rejected.
- Issue #5189 was closed with an explicit duplicate-allocation retirement and the instruction not to run these seeds again. The competing commit is no longer retrievable through the GitHub commit API at reconciliation time; its source/result details above are therefore preserved as contemporaneous issue reports, not independently re-read Git objects.

## Interpretation

The competing execution's reported result is `HOLD_COVERAGE_TRADEOFF`; this branch's own raw metrics also happen to miss the frozen efficacy gates. Neither numeric output is a valid independent fresh-seed estimate, and their agreement on a coarse disposition does not make the runs replicates. Keep both raw bundles separate and unpooled. The raw-only audit on this branch establishes internal consistency of this raw artifact only; it does not repair allocation provenance or seed novelty.

Accordingly, `RUN_RECORD.json` records zero valid fresh-allocation invocations and one actual duplicate-seed runner invocation on this source. The earlier result interpretation in the first PR commit is superseded by the correction in a later commit; Git history retains both. No rerun, seed substitution, or gate change was made.

## Correction validation

The unchanged construction test was run once in Docker Desktop `desktop-linux` with the pinned image digest, `--pull=never`, network disabled, read-only root/source, and the frozen CPU/memory/PID/security bounds. Result: 1/1 pass, container `b18ccecfce9dd4a306bf68dabbb7b46eeb1dcc2abf9887e3fbd805d2f194223d`, exit 0; container removed after inspection. This uses only construction seeds 59003/59004 and does not rerun the formal runner or auditor. `RUN_RECORD.json` parses as JSON and local `git diff --check` is clean.

## Scope

This is an execution-provenance STOP, not a scientific PASS or FAIL about the hypothesis. It supports no classifier generalization, GUI, runtime, safety, model-quality, performance, or product claim.
