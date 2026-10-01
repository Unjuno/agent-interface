# Observation source-role composition — formal result

Task `OBSERVATION-SOURCE-ROLE-COMPOSITION-20260918-001`, Issue #1471.

## Decision

**`PASS_OBSERVATION_SOURCE_ROLE_COMPOSITION_SCOPED`**

This is a retained/synthetic composition result over the already-retained semantics of #615/#629 and #721. It does not rerun or relabel those parents and makes no live GUI/model/input claim.

## Frozen comparison

The single factor is whether a reused observation carries a non-rebindable source role.

- `ROLE_BOUND_RECEIPT` binds source digest, lineage, currentness and one of `CURRENT_PLANNER_CONTEXT`, `TERMINAL_EVIDENCE`, or `NEW_CURRENT_PLANNER_CONTEXT`; every receipt grants zero semantic/input authority and old action authority is never reused.
- `UNTYPED_REUSE` is the negative discriminator and does not jointly enforce role/currentness/proof use.

Formal source was frozen on GitHub before output. One deterministic invocation used seed `147120260918001` and 100,000 generated receipt/use rows. Reruns/replacements/tuning were 0/0/0.

## Result

- candidate/oracle full decision+state mismatches: **0 / 100,000**;
- terminal historical evidence accepted as current planner context: **0 / 25,000** candidate versus **25,000 / 25,000** untyped discriminator;
- changed recapture rebound as proof of the old terminal predicate: **0 / 25,000** candidate versus **25,000 / 25,000** untyped discriminator;
- semantic/input-authority escape outputs: **0**;
- old-action reuse accepts: **0**;
- second use of replayed accepted receipt: **0**;
- valid controls remained live: reanchor planner-context **3,312/3,312**, terminal feedback **3,391/3,391**, new-current planner-context **3,265/3,265**.

The formal row digest is `4022b3f63bc2b6defca09a6d7c7ebfb4383a2f9d000e27eac1ee9ee82cce019e`.

## Independent audit and integrity

The independent audit regenerates the 100,000-row corpus, replays candidate/oracle state, recomputes the row digest and independently checks schedule cardinalities. It returns no errors and rejects 8/8 copied-result corruptions: mismatch, terminal upgrade, terminal-proof rebind, authority escape, replay escape, formal-invocation count change, discriminator suppression and row-digest mutation.

Post-formal source SHA-256 values are byte-identical to the source-first freeze. Formal result SHA-256 is `442037665bb13af29628ecf8c0a1c3a9a80f1e69fdb3c28cbc3e455b38946233`; audit SHA-256 is `981f98ae2b50248901293a4cc6b6fd01f2d598700cbfb42a560c44c0734b6c7f`.

## Interpretation

The composition rule supported here is narrower than “reuse observations whenever possible”:

1. A current post-recovery observation may seed a **new planner context** without an extra recapture, but it is not input/semantic authority and cannot resurrect the discarded old action.
2. An observation that already supported a terminal predicate may seed **terminal feedback** without recapture, but it stays historical-at-return (`currentness_asserted=false`).
3. A later recapture is a **new current context**. It cannot be silently rebound as proof for the earlier terminal predicate.

Thus reuse eligibility depends on source role, not only on having valid bytes or a recent digest. This is directly compatible with the governing invariant: preserve rich-model intent and remove redundant local work without turning cached/history evidence into current authority.

## Evidence limits

#721's complete 79-file raw packet was not located through current-main code search during intake. This study therefore pins #721's retained Issue result contract and published freeze/formal hashes; it does **not** claim to rehash or replay #721's historical raw frames. #615/#629 main-retained result blobs are pinned directly.

No latency, token, provider/model quality, physical-actuation, X11, MAP01-clear, human-tempo, reliability-rate or production-ABI claim follows. A production ABI may encode these roles as separate receipt types rather than one enum.
