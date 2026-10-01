# Dynamic assurance-case finite T0

Allocation: `dynamic-assurance-case-5332-t0-20260930-01`
Issue: [#5332](https://github.com/Unjuno/agent-interface/issues/5332)
Issue-registration intake main: `322faf504a5ac993b092f154733d83bc13767e60`
Current main at freeze: `bdd093f24c626c7ffadaa7ba2a6c8e408814675c`
Branch: `research/dynamic-assurance-case-5332-t0-20260930`

## H/T/D/C/U

**H.** For one synthetic `SAFE_TO_RELEASE` top claim, a compositional assurance graph with currentness, coverage, defeater, and independence gates rejects seeded stale, incomplete, correlated, and contradicted support more reliably than flat receipt-count aggregation, while preserving the pre-successor graph revision byte-for-byte. Argument status is not external truth or authority.

**T.** Required subclaims are `scope`, `protocol`, `freshness`, `causal_attribution`, and `release`; the separate `effect` support requires two independent evidence domains. Six states: clean baseline, changed dependency revision, missing causal subclaim with an unrelated extra receipt, correlated duplicate effect support, direct unresolved defeater, and a negative successor appended after a supported historical revision. Compare `FLAT_RECEIPTS`, `STATIC_CASE`, `DYNAMIC_CASE`, `DEFEATER_AWARE`, `INDEPENDENCE_AWARE`, and `COMPOSITE_DYNAMIC_CASE`.

**D.** `PASS_ASSURANCE_CASE_T0_SCOPED` iff the baseline is supported; the composite policy rejects or marks stale/partial/conflicted every seeded fault; each single-dimension policy rejects its targeted fault; flat receipt aggregation exposes the seeded unsound-PASS cases; the negative successor preserves the prior graph digest; all 36 policy/state rows match the independent oracle; no authority/effect is emitted; and six corruption controls are rejected.

**C.** Deterministic stdlib-only host CPU pilot. No Docker/OrbStack invocation because the shared lane has no named grant and an owner-unconfirmed container is recorded at #5085 comment #5907959998. No network, model/provider, GUI/input, or external effect. Construction tests and the one raw runner invocation are separate. The branch was fast-forwarded from registration main `322faf5` through `0be8311` to current main `bdd093f`; the intervening changes did not touch this additive experiment path.

**U.** Synthetic graph/schema only; does not establish real-world effect truth, causal identification, correctness of arbitrary argument links, production safety, or transfer across GUI/code/RAG. A container rung remains separate and gated.

## Frozen execution

Freeze all source/gate hashes in `FREEZE.json` before invoking `runner.py` once. Preserve its one raw output; invoke the independent auditor once against that immutable raw. Any missing or contradictory evidence is retained as STOP/HOLD, with no rerun or tuning. Run local CI against the exact proposed PR head before publication.
