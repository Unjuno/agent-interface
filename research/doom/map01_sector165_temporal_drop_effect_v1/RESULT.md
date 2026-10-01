# MAP01 sector165 temporal drop-effect result

Decision: **PASS_TEMPORAL_DROP_EFFECT_SCOPED / PASS_AUDIT**.

Task `MAP01-SECTOR165-TEMPORAL-DROP-EFFECT-20260917-004`, Issue #776. Source-first formal freeze `6c7c860022751f2f2c11bc18120aae5b291eddec` on immutable BASE `cd4fe74fb886864a56dfe2fb8f66e65bbab06caa`.

This rung changed observation timing only. It reused the exact #733 relation (`>=80` valid LK tracks and median vertical dy `<= -20px` in ROI `[x=20:620,y=20:300]`) but applied it to timestamped consecutive X11 frames retained during the bounded `use80ms -> forward450ms -> settle350ms` program. No new dy threshold, hidden controller state, model call, automap, pause/save or ATTACK was introduced.

Formal first outcomes: six hidden lower-floor positives (two each at requested 35/55/75deg headings) plus two one-sided-wall controls.

Independent retained-byte audit:
- hidden positive drops: **6/6**;
- temporal pixel detections: **6/6**;
- inherited endpoint detections: **2/6**;
- temporal gain over endpoint: **+4 positives**;
- wall temporal false positives: **0/2**;
- every case retained >=13 eligible consecutive frame pairs (frozen minimum 6) and >=14 frames (minimum 8);
- release failures: **0/8**.

The four endpoint misses at 55/75deg were recovered by short-lived temporal events. Example minima among eligible consecutive pairs were approximately -27.55/-34.02px for the 55deg group and -25.71/-24.44px for the 75deg group, while wall controls bottomed near -1.90/-1.88px. The two 35deg positives were detected by both endpoint and temporal relations.

The independent auditor re-decodes all retained PNG pairs, uses capture-start timestamps rather than nominal cadence, recomputes the unchanged LK statistic, checks source hashes, hidden setup/effect scoring and all InputOwner release records, then reapplies the frozen PASS/HOLD/FAIL rule.

Evidence archive `map01_sector165_temporal_drop_effect_v1_evidence.tar.xz`: 13,325,284 bytes, SHA-256 `7c6a3d558b94076ac0e75f4de2c960ef2353479c22c9cdc38419bfc0ef7cd5f3`; manifest SHA-256 `2bcdc8ba64fde95cc180bc636142b90d2b62f51cb4dfba0560ce7f59fe4b7dad`, 226 files excluding the manifest. Fresh extraction reproduced the audit byte-identically.

Interpretation remains narrow: a short retained pixel history recovers one MAP01 fall-effect relation that endpoint-only observation lost across approach headings. It does not prove generic fall detection, MAP01 navigation/clear, combat/model benefit, or a generic optical-flow threshold. The next rung may test this temporal event only as a bounded local subgoal termination signal, with hidden topology still evaluator-only and without composing recovery/model semantics in the same first transfer.
