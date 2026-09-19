# #1216 current-evidence validity anchor result

Decision: **PASS_CURRENT_EVIDENCE_VALIDITY_ANCHOR_SCOPED**.

Exact merged #1200 first-result SHA-256 `ad1bf71d…` was replayed without regeneration. The original source-applied anchor reproduces all 36 predecessor admission dispositions exactly. With the same 120 ms duration anchored instead at the fresh current ROI evidence capture end, exactly one row changes: `f11_temporal` from `EXPIRED` to `ADMITTED`. All 17 previously admitted local rows remain admitted.

Fresh random formal: 350,000 timing/evidence cases. Candidate vs independent oracle mismatches0; stale/mismatched/late current-evidence re-anchor admissions0. Evidence that is not strictly ordered source→current capture→prep→future receives `CURRENT_EVIDENCE_NOT_ANCHORABLE`; authority false, digest mismatch and branch miss remain fail-closed.

The result does **not** lengthen the branch lifetime; it changes only the provenance of the 120 ms interval to the observation that actually justified branch preparation. It remains a replay/contract result. A fresh private-X11 transfer is still required before treating this as a live scheduling repair.
