# Issue #6561 T0b — source-bound advisory-context audit

Allocation: `SOFT-EVENT-CONTEXT-6561-T0B-WSLC-20261002-01`
Base main: `926144e0bbbc197e00aa3b4821f1d49afe831529`
Branch: `research/soft-event-context-6561-t0b-wslc-20261002`

Contract references on that base: `research/live_control/observable_signal_guard_v2.py` blob `c0955f976e3a0af6ce926f22cee4a5ddf70ef543`, SHA-256 `7be055c4bd68a1528f4b2b02b543435bd64465ea42d4452f5597d6dce08442a0`; retained v30 audit `research/doom/results/map01-split-cover-validity-v30-live-01/audit.json` blob `980acfca962e3cc4ff8c32968692374ea0b60191`, SHA-256 `fb82e0ad0e4812596c9b5f7325b6c7b1a6f714378d8e77e044b75cd56f7b5a2d`. Both blobs match the pinned T1 review references; the live audit is context only, not recomputed or changed here.

This is an additive successor to the unrun WSLc allocation proposed in Draft PR #6568. It does not alter that PR's host-only construction result, the separate #6561 adversarial-mutation T1 result, or any prior live MAP01 allocation. The T1 mutation result and PR review identified co-mutated binding acceptance, contradictory guard flags accepted as OBSERVED, unwitnessed expiry labels, and a float `current_sequence` candidate/auditor mismatch. This allocation freezes a hardened finite contract and tests those boundaries before any live work.

## H / T / D / C / U

**H.** A bounded advisory projection of a previously observed soft health event can distinguish NONE from UNKNOWN, select the latest correctly ordered event, and remain authority-free, while a standalone auditor rejects source rebinding, contradictory v2 guard semantics, unsubstantiated invalidation/expiry, malformed sequence types, stale/future evidence, and changed prompt output.

**T.** Deterministic six-case fixture: NONE, one soft event, multiple soft events, hard invalidation, unknown signal, and source expiry. Candidate emits one raw packet. Independent auditor receives the frozen fixture separately and reconstructs from that read-only source; it does not import candidate code. Construction suite contains 15 corruption controls: co-mutated packet/event binding; six individual contradictory guard flags; absent or relabeled expiry receipt; float, boolean, and negative current sequence; future event; changed event count; and prompt authority/success injection. Construction, candidate, and auditor each run in a separate WSLc container.

**D.** `PASS_METHOD_SCOPED` only if all six baseline cases pass exact reconstruction, the 15 corruptions are rejected, all OBSERVED rows preserve zero authority and no-success claims, NONE/UNKNOWN/HARD/EXPIRED are distinct, all three formal stages exit 0, and the raw packet copied to the auditor is byte-identical. Any formal mismatch is retained as FAIL/STOP; no retry, repair, or output replacement.

**C.** This is a finite synthetic packet-boundary contract. The auditor's binding authority comes from the separately frozen read-only fixture; its scope is only that fixture and this serializer. The fixture does not execute the production controller or independently establish the truth of an environment observation.

**U.** No claim about whether a live caller exposes this state, whether a planner uses the summary, whether it improves a decision, whether the guard is empirically correct, or whether MAP01 survival/exit improves. It is not the live-control gate in #59 and authorizes no GUI, game, model, or input allocation.

## Runtime and invocation cap

Use native WSLc 3.0.1.0 and cached image `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (Python 3.12.14), `--pull never --network none --cpus 1 --memory 512M --user 65534:65534`. No GPU is used: this small deterministic Python fixture has no training or accelerated numerical workload. Memory enforcement is requested, not presumed; record WSLc/cgroup warnings. One construction, one candidate, and one auditor invocation maximum; retries=0. The audit input copy must be byte-identical to candidate raw output.
