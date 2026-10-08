# Custody qualification

Final disposition: `HOLD_CUSTODY_FREEZE_NOT_COMMITTED_BEFORE_RUN`.

The allocation's fixture, oracle, candidate, independent auditor, construction
tests, and source hashes were locally frozen before the one formal candidate
invocation. However, that freeze had not been committed to Git before the
candidate/auditor were run. The repository's commit-before-run custody gate was
therefore missed. A later Git commit cannot retroactively satisfy that order.

The freeze manifest also names a preregistration file as `README.md`; that file
was renamed to `REPORT.md` after the run and its exact pre-run bytes are not
separately preserved under the original path. Its recorded digest remains in
`FREEZE.json`, but cannot be revalidated against a same-path retained file.
This is included in the custody HOLD rather than silently treating the later
edited report as the frozen preregistration.

The first-run candidate output and independent audit are preserved byte-for-byte
as `candidate_raw.json` and `audit.json`. The audit reports 66 rows checked,
zero replay errors, and a method-level PASS; that internal audit disposition
does not override the custody HOLD. No second invocation of this allocation is
authorized by this record. Any genuinely new study must be a new successor with
new allocation identity, provenance, and pre-run commit.

The run remains useful as a retained diagnostic: 10 of 14 fixed nontrivial
partitions shift A's share from 2/4 to 3/4 under presented-ID debt, four are
nulls, and trusted-parent accounting reproduces the baseline. It is not
promoted as a formal research PASS or as evidence about real users, identity,
GUI behavior, or production fairness.

