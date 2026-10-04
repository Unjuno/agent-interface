# MAP01 V39 unknown-HUD recovery candidate (T0)

**Disposition:** `PASS_CONSTRUCTION_STRUCTURE`; no live efficacy claim. This is an additive, source-only successor candidate for Issue #59's recorded unknown HUD stop. It is not a lease, rollout, game run, or model comparison.

## Hypothesis and boundary

The source-only hypothesis is that V39's `RuntimeError("cover validity source health unavailable")` on UNKNOWN can be replaced by an explicit fail-closed stop that prevents an unqualified cover or planner action, while session cleanup still emits the available terminal score and persists controller evidence. V40 must require health and ammunition from the same observed capture and binding; it does not reuse earlier numbers. If source becomes unknown after a cover is accepted, it must cancel and prove an empty input state before stopping.

The candidate does not demonstrate game performance, HUD parser correctness on the Issue #59 PNGs, reduced deaths, or comparison against a reference controller. The exact PNG031/PNG035 evidence described in issue comment 5978714723 is not available in this checkout. No game, model, GUI, operating-system input, WSLc runtime, or formal allocation was used.

## Provenance

- Repository: `Unjuno/agent-interface`.
- Base commit: `5ce152e1479bedac08f55db45d24b3dd1405cb16` (`origin/main` at preparation).
- Untouched predecessor: `research/doom/map01_overlap_controller_v39.py`, blob `0f3dfcada36520acb24fceaf26a4124c96e050b3`.
- Candidate: `research/doom/map01_overlap_controller_v40.py`, SHA-256 `961eadb2b14d23d9c1f4972addebb58e12553b8667db01a91701f4505dc826b0`.
- Candidate tests: `research/doom/test_map01_overlap_controller_v40_unknown_source.py`, SHA-256 `363dc53fc708bcdf27a38c7c0913f65d3059aef266b3ad7a68ab8b59f18cea72`.
- Independent structural audit source: `audit_map01_unknown_source_recovery_v1.py`, SHA-256 `4b5ce09f833c5b294dcd69de3a687e339b9f8ad446a6c97071cbba5a58a7462d`.
- Audit result: `audit.json`; all five source-ordering, rejection, cleanup, and release checks passed.

## Evidence

- Candidate construction tests: 8/8 passed. Tests cover unknown/mismatched source rejection, a valid same-source control, verified empty release, preflight and post-acceptance gate ordering, cleanup/score persistence, score emitted on EOF, and exception cleanup.
- V39 regression tests: 2/2 passed.
- Observable-signal guard: 4/4 passed.
- Final-action admission: 6/6 passed.
- Python compilation and `git diff --check`: passed.
- HUD parser V3 suite: blocked in this checkout because `_vizdoom/vizdoom/freedoom2.wad` is absent (three setup errors). This does not test the saved PNGs from the issue.
- Raw command outputs and exit codes are preserved in the adjacent `*.log` files.

## Candidate behavior

V40 returns an explicit, non-admitted monitor receipt for unusable health evidence rather than raising before the controller can record its stop. It checks health/ammo source identity before any cover submission and again after acceptance, before a planner call. The stop receipt carries no action authority. Release is accepted only when cancellation is confirmed and the verified held-key/button state is empty. A registered session-custody handler attempts finish/EOF cleanup, waits again for a score emitted after EOF, and persists controller events plus cleanup receipt; unresolved child shutdown remains explicitly unverified. Child stderr is redirected to a file so a full pipe cannot block cleanup.

## Next boundary

Review the candidate diff and custody semantics independently. If accepted, replay the exact retained issue PNGs against the pinned WAD/parser in an environment that has those artifacts, then consider a formally scoped allocation. Neither step is implied by this construction result.
