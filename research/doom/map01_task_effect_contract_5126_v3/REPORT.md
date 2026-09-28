# #5126 cross-plane identity contract v3 result

**Disposition: `PASS_CROSS_PLANE_IDENTITY_CONTRACT` (synthetic, host-only).**

## H / T / D / C / U

**H.** A scorer `source_event_id` colliding with either physical edge must not
qualify as a task effect. Duplicate scorer/effect records are a distinct
failure class and retain `UNRESOLVED_DUPLICATE_EFFECT`.

**T.** After five focused construction tests passed, v3 source and input hashes
were frozen in `FREEZE.json`. One formal corpus invocation classified the
immutable 13-row #5126 v1 raw input with v3 candidate and separate oracle; one
raw-only audit independently reconstructed the gate. A separate unit control
mutated a formerly valid raw positive after classification and confirmed the
auditor rejects it.

**D.** Candidate/oracle agreement **13/13**; expected-gate agreement **13/13**;
raw-only audit errors **0**; construction tests **5/5**. The cross-plane
collision is `UNRESOLVED_DUPLICATE_SOURCE_EVENT`; the same-plane duplicate
scorer/effect case remains `UNRESOLVED_DUPLICATE_EFFECT`. Input/task authority
remain false.

Corpus SHA-256:
`dc2e0120d1c05e573e74f45339a9cb72b635031224c5bd340f3b035d8402dcf2`.
Audit SHA-256:
`aff5676d909c08a4761204d793b20b9c2f5495113c9f85729c9fd6ed731d9c8f`.
Immutable input corpus SHA-256:
`536de27a25cdc7b9936235dc1ef900cf174f2acbf16239a696474ede5f69fa9f`.

**C.** This is synthetic standard-library host CPU evidence. The earlier v2
expected-taxonomy failure remains preserved at
`../map01_task_effect_contract_5126_v2/REPORT.md`; its output was not
overwritten. The current-main source identity limitation is separately
recorded by merged PR #5141 as `HOLD_SOURCE_IDENTITY_INSUFFICIENT`.

**U.** No live source identity, scorer epoch binding, cross-process clock
comparability, causal task effect, actual input, MAP01 efficacy, model usage,
efficiency, or runtime readiness is established. No container was run because
Issue #5126 has no explicit CPU slot assignment; the shared slot is assigned
to another lane. This PASS repairs the synthetic contract boundary only.

Commands after the freeze gate (repository root):

```sh
python3 research/doom/map01_task_effect_contract_5126_v3/run.py
python3 research/doom/map01_task_effect_contract_5126_v3/audit.py
```
