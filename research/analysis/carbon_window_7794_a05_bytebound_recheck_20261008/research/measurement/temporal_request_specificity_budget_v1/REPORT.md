# #1648 Temporal request-specificity budget lattice

Decision: **PASS_TEMPORAL_REQUEST_SPECIFICITY_BUDGET_LATTICE_SCOPED**

## Result

On the exact frozen #1633 grid `T={0,25,...,1000}` and anchors `A={250,275,...,825}`:

| Request information | RECENT_DENSE | LONG_BASELINE | EVENT_CENTERED | REVERSAL_BRACKET | Equal-class mean |
|---|---:|---:|---:|---:|---:|
| none | colspan | colspan | **11 total universal samples** | colspan | n/a |
| class only, anchor unknown | 4 | 2 | 8 | 6 | **5** |
| class + anchor | 4 | 2 | 2 | 2 | **5/2** |

The universal 11-sample parent theorem from #1640 was independently rechecked from the same frozen constants and witness.

## Lower-bound certificates

For class-only EVENT_CENTERED, eight genuine required intervals are pairwise disjoint: EVENT_L(250), EVENT_L(350), and EVENT_R at anchors 325,425,525,625,725,825. Therefore any schedule that must answer every EVENT anchor before the anchor is known needs at least eight timestamps. The explicit 8-point witness `(225,300,375,450,550,650,750,850)` satisfies all 24 anchors.

For class-only REVERSAL_BRACKET, six genuine required intervals are pairwise disjoint: REV_L(250), REV_L(400), and REV_R at anchors 375,525,675,825. Therefore at least six timestamps are necessary. The explicit 6-point witness `(225,375,525,650,775,850)` satisfies all 24 anchors.

RECENT_DENSE needs four recent samples by definition. LONG_BASELINE needs two samples because its early and late regions are disjoint. Once an EVENT or REVERSAL anchor is known, its required left and right regions are disjoint and each requires one point, so two samples are both necessary and sufficient; `(a-25,a+25)` is a valid witness for every frozen anchor.

## Integrity

- formal invocations: 1
- reruns/replacements/tuning: 0/0/0
- independent audit errors: []
- corruption controls: 6/6 rejected
- result digest: `ab9a73438a9af0fdb06ed3a43ed0053873912164e9c4e44c867929da2ea986fd`
- audit digest: `89073fb99a7bcd193a3c7a0ff1d12b3d068d1433543f708375bf5c2cc1c65fca`
- pre/post scientific-source SHA-256 values match exactly; the local shell diff initially stopped only because the pre-freeze manifest stored absolute filenames while the postformal manifest stored relative filenames. No scientific source changed and the formal was not rerun.

Exact formal source and evidence are retained as deterministic base64 tar.gz bundles beside this report. `RECONSTRUCT.py` restores them and verifies bundle hashes.

## Interpretation

This quantifies a three-level information-allocation lattice:

1. no later-request information: 11 universal samples;
2. relation class known but anchor unknown: 2--8 samples depending on class, mean 5 under equal class weight;
3. class and anchor known: 2--4 samples, mean 2.5.

The gain comes from **request specificity**, not image compression or model intelligence. A queryable temporal buffer should preserve enough structure for a consumer to request the relation and anchor it actually needs rather than treating all temporal queries as equivalent.

This theorem does not show model accuracy, token saving, latency improvement, GUI efficacy, or a production policy. The next empirical discriminator is a source-matched model study that varies request specificity while holding available frame history and relation semantics fixed.
