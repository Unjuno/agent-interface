# MAP01 sector165 cross-heading pixel-drop result

Decision: **HOLD_PIXEL_DROP_VIEW_DEPENDENT / PASS_AUDIT**.

Task `MAP01-SECTOR165-DROP-CROSS-HEADING-20260917-003`, Issue #754. Source-first formal freeze: `d2a067b359b93bfde5940344f5503432eb5b580f` on immutable BASE `ac114c6648ad47673214e341df8edbba592d1c5e`.

The frozen #733 relation was unchanged: `DROP_COMPLETED` iff >=80 valid LK tracks and median vertical displacement <= -20 px in ROI `[x=20:620,y=20:300]`, with the same `use80ms -> forward450ms -> settle350ms` program. Only setup approach heading varied for lower-floor positives.

All six positive fixtures independently reached the hidden lower-floor scorer state (sector38/Z-128). Pixel results:
- 35deg group: 2/2 detected; actual median 42.1875deg; dy -51.287 / -52.360 px.
- 55deg group: 0/2 detected; actual median 54.4922deg; dy -1.070 / -1.070 px.
- 75deg group: 0/2 detected; actual median 73.8281deg; dy +1.022 / +2.871 px.
- two wall controls: 0 false positives.
- realized heading-median span: 31.6406deg (frozen minimum 30deg).
- controller/setup release failures: 0.

Therefore the #733 vertical-flow effect sensor is viewpoint-dependent at the same physical task transition. Do not promote it as a navigation termination signal and do not tune the -20px threshold to rescue these misses; actual high-heading drops have near-zero/positive median vertical flow.

The first post-formal auditor stopped on a plan-field KeyError. No live case was rerun. The retained audit-v2 correction changes only heading-group enumeration, deriving the authored non-null headings from `plan['cases']`; metric, threshold, raw evidence and scientific decision logic are unchanged.

Full conversation archive: `map01_sector165_drop_cross_heading_v1_evidence.tar.xz`, 1,753,260 bytes, SHA-256 `aa44d611a7906a90be2bd8c1c0d25d9fab83b8a109bbf15c711608c51587d6a5`. Fresh extraction reproduced the corrected audit byte-identically.

Next: use a viewpoint-aware geometry/task relation and coordinate with the separate image-registration lane (#747) before defining a successor. No MAP01-clear/navigation/combat/model/general optical-flow claim.