# EntityTrack continuity experiment for Issue #4121 / parent #35

## Disposition

- Allocation 01: `STOP_OUTER_EXECUTION_TIMEOUT / HOLD_FORMAL_INCOMPLETE` after 41/48 complete first rows. No runner terminal receipt; zero reruns.
- Allocation 02: complete 48/48 in four immutable 12-case batches, but **`FAIL_ENTITY_TRACK_CONTINUITY_GATE`** under the prospectively frozen scientific gates.
- Frozen raw-only auditor: evidence errors `[]`, but its bundled mutation helper rejected only 7/8 copied-evidence mutations (`state` mutation missed by the helper). Therefore the frozen audit does not satisfy the preregistered corruption-control gate.
- Separately versioned posthoc raw-integrity auditor: 48 rows, errors `[]`, 8/8 copied-evidence mutations rejected. This validates retained bytes/row consistency only and does **not** upgrade the scientific FAIL.

## H / T / D / C / U

### H
A short-lived EntityTrack initialized from the visually marked target and updated by bounded motion association would complete separable-motion cases with fewer `NEEDS_DECISION` outcomes than a current-frame candidate-set policy, while yielding before input on crossing ambiguity, disappearance/reappearance, replacement-after-loss and stale current evidence.

### T
Provided Linux x86_64 execution container, CPython 3.13.5, Tk 8.6, Python-Xlib 0.15, fresh TCP-disabled Xvfb. Three policies (`SINGLE_FRAME_FIRST`, `CANDIDATE_SET`, `ENTITY_TRACK`) × eight fixed scenarios × two repetitions = 48 fresh Tk Canvas cases. Task: move the rectangle that was blue-marked in observation 0. Marker disappears after observation 0. A fresh capture is taken before XTEST click. Independent application state before/after the click scores which object moved. No model/provider/network/user desktop.

### D — complete allocation 02

| Policy | Cases | Correct target effects | Wrong-entity effects | YIELD |
|---|---:|---:|---:|---:|
| SINGLE_FRAME_FIRST | 16 | 6 | 8 | 2 |
| CANDIDATE_SET | 16 | 2 | 0 | 14 |
| ENTITY_TRACK | 16 | 10 | 0 | 6 |

The first, second, third, fifth, sixth, seventh and eighth prospectively frozen gates passed. The fourth gate failed: `ENTITY_TRACK` was required to YIELD in every `CROSSING_AMBIGUOUS`, `OCCLUDE_REAPPEAR`, `REPLACEMENT_AFTER_LOSS` and `STALE_AFTER_CAPTURE` row. It instead acted in both `CROSSING_AMBIGUOUS` repetitions, moving T correctly each time. Because the declared contract required fail-closed ambiguity handling rather than rewarding a lucky/correct action, the complete scientific disposition is `FAIL_ENTITY_TRACK_CONTINUITY_GATE`.

The other negative controls behaved as intended: both `OCCLUDE_REAPPEAR` and `REPLACEMENT_AFTER_LOSS` repetitions yielded after target loss; both stale-current cases yielded after fresh revalidation changed.

All 48 terminal X-server key/button observations were neutral. `CANDIDATE_SET` made zero wrong-entity effects but completed only 2 tasks; `ENTITY_TRACK` made zero wrong-entity effects and completed 10 tasks. That descriptive improvement cannot override the failed ambiguity gate.

### C
Exact-color two-object Tk fixture with deterministic barrier-selected trajectories and cooperative state journal. The tracker is intentionally small and finite. Pixel-identical incarnation replacement remains outside what appearance can prove; after an actual LOST state, this candidate does not re-link. The crossing check is a candidate implementation mechanism, not a general identity theorem.

### U
No Inkscape transfer, >2 objects, arbitrary decoration/scale, partial occlusion, pointer grabs, Wayland/compositor coverage, learned perception, model utility/tokens, natural failure rate, performance benefit or production action admission. No Docker/OrbStack image identity was available.

## Allocation 01 preservation

The original single-process formal invocation was source-first frozen on GitHub. The outer execution envelope ended at 41/48 complete case files before the runner could write `RESULT.json`, `END.json` or its own `STOP.json`. No study process remained afterward. The unchanged full auditor returns `case_count` and `terminal_schema`; the unbalanced prefix is retained, not pooled.

## Allocation 02 execution-envelope correction

Repository failure-routing guidance was followed: no wrapper-only successor Issue was created. Under the same Issue, a fresh allocation changed only serialization into four exact 12-case batches plus aggregation. Scientific source, schedule, scenarios, policies and gates were byte-identical to allocation 01. All four batches completed 12/12; every batch Xvfb exit was 0. No batch was retried or replaced.

## Audit chronology

Frozen `audit.py` independently reconstructs all complete rows and reports `errors=[]`; its scientific gate result agrees with the candidate. Its post-run `mutations()` helper, however, failed to reject the copied `pre_state` mutation because that helper did not compare the reconstructed movement list against the stored movement list. That weakness is preserved.

`posthoc_audit.py` is a separately versioned, read-only integrity hardening pass. It reconstructs movement from raw pre/post state, capture hashes, effect flags and terminal neutrality, and rejects all eight copied-evidence mutations. Its disposition is `POSTHOC_RAW_INTEGRITY_PASS_SCIENTIFIC_FAIL`; it never changes the frozen candidate or frozen scientific gates.

## Hashes

- Allocation-01 FREEZE SHA-256: `5ba82482fd2962b0b2b09669653efbc409b4bcab9b0d708eb266541ac0eb333f`
- Allocation-02 FREEZE_V2 SHA-256: `b5ecddd354549626990d2a3e595d3392be93a5d62316a097f91553b77bdb2cb6`
- Allocation-02 RESULT SHA-256: `b1542fd10a3e0e05590cee20a9a006ad7915bdd35861d2360b2c564f676a89eb`
- Frozen AUDIT_V2 SHA-256: `bd02643bca600bf21ba6b4774395d188be4e4146b9b6dac70a34cb14d141c63f`
- Posthoc audit SHA-256: `417d3fa81565cae25581404b2e69b720eb35ad9a6a43907509d65145215aae59`

## Integration decision

Do **not** promote this EntityTrack candidate as satisfying #35. The result does show a useful contrast: current-frame uniqueness can be safe but highly refusing, while bounded continuity can recover additional correct actions without wrong-entity effects in this fixture. The missing requirement is explicit ambiguity semantics at trajectory crossing. Any successor must preserve this FAIL and test a genuinely revised association/ambiguity rule in a fresh allocation; it must not relabel these 48 rows or reuse them as a candidate PASS.
