# V39 paired health/ammo A03 — initial auditor mismatch

This is a preservation-only extract of the unique initial audit receipt from closed PR #7713, head `8f1e138289c85c45a6e6208990d1f29e90347fb3`.

`AUDIT_INITIAL.json` records `AUDIT_FAILED` with 25/26 checks. PR #7713 reports that the later 26/26 result corrected an auditor status label only; the candidate was not rerun. Therefore this is an auditor-oracle failure record, not a candidate-method failure or an accepted scientific result.

The broader paired-epoch construction result is preserved in the merged current-main package [`v39_ammo_cover_pair_guard_59_a03_20261005/`](../v39_ammo_cover_pair_guard_59_a03_20261005/), originating in PR #7711. This extract does not duplicate its candidate, fixture, or corrected audit, and it does not change that result.

The original PR #7713 package manifest lists the SHA-256 of this exact file; the value is retained in this extract's `SHA256SUMS`. No candidate, auditor, or runtime was rerun.
