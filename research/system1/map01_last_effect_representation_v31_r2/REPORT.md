# v31 last-effect representation R2 — retained result

Issue: #1511  
Task: `LOCAL-SYSTEM1-MAP01-LAST-EFFECT-REPRESENTATION-V31-R2-20260918-001`  
Decision: **PASS_LAST_EFFECT_REPRESENTATION_V31_R2_SCOPED**

## First outcome

Exactly one deterministic replay was executed after source-first publication/readback. Formal invocations: 1. Reruns/replacements/tuning: 0.

- retained rows: 8
- #937-identical eligible rows: **5** (`[1,2,3,4,5]`)
- prompt-only signature groups: **4**
- prompt-only collision groups: **1**, exactly iterations **1/2**
- enriched prompt+last-effect signature groups: **5**
- enriched collision groups: **0**
- independent audit: **PASS**, errors `[]`

The known collision is source-exact: iterations 1/2 share prompt Git blob `02edc59200629518b01080e16f7a4e132cda5c60` but retain distinct canonical teacher labels. The added caller-visible historical feature is derived only from earlier admitted/completed plans:

- iteration 1: `NONE` because no earlier admitted completed plan exists;
- iteration 2: `{action: retreat_fire, extent: short, result: visible_change}`, sourced from iteration 1's retained final effect receipt.

The remaining eligible rows derive, in order, `fire/pulse/no_visible_effect`, `strafe_left/medium/visible_change`, and `retreat_fire/short/visible_change` from their immediately preceding admitted/completed plans. Source iteration is retained for audit provenance but is not part of the representation signature.

## Integrity

Pinned Git blobs:
- v31 report: `2aed2e7e3f58b4f8b013fc98c79482a4036225ae`
- #937 SOURCE_ROWS: `4ab9129253b0c2d976c932d07ed744528ea23734`
- #937 RESULT: `d08d66c07ed70cd4f02609a1122df664b90f1a2c`

Toy-only preformal controls passed 8/8, including `NONE != UNKNOWN`, forged/current/future receipt rejection, and image/oracle field rejection. Exact frozen source publication read back 7/7 after one preformal transport-only correction of `run.py`/`audit.py` NUL escaping; formal remained 0 during that correction.

`RESULT.json` SHA-256: `472ff585e22be4e98d5970bb6e8eed36b6c736cdff928aa4c7e4ffa9de897412`  
`AUDIT.json` SHA-256: `e213cb5d3c60ae027c77fb29a0a01b7d198306769791416416155c9757e85f85`

## Interpretation boundary

This removes the **known v31 prompt-only collision** on five retained eligible rows using one already-caller-visible typed history feature. It does not prove population-level representation sufficiency, learner value, unique optimality of Astra labels, or general MAP01 control. The receipt can correlate with omitted visual state without being causally sufficient.

Therefore this result clears one specific blocker named by #1026/#1027, but it does **not** activate classifier or adaptive-TTC work by itself: a materially larger leakage-free real residual corpus and an independent semantic/effect oracle are still required.
