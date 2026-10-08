# A02 provenance metadata correction

`FROZEN.json` records the intended branch as
`research/8135-persistent-counterparty-t0-a02-20261005`, but the actual checked
branch at formal execution was
`research/8135-persistent-counterparty-t0-a01-20261005`. This arose because
A02's freeze template was copied from A01 and its `branch` constant was not
updated. The frozen file and source are deliberately not rewritten.

The experiment's exact-main gate did pass: the checked-out `HEAD`, its
merge-base with `origin/main`, and frozen `base_commit` were all
`b6907899f11b036f2af572e8d4794ebb4b7e5c83`; the allocation files were
uncommitted additive paths on that base. Candidate/auditor source hashes,
manifest/truth hashes, image identity, invocation counts and raw outputs are
unchanged. This is a branch-label metadata deviation, not a different source
base or a scientific reclassification. It is retained explicitly so the
reported PASS remains auditable rather than silently correcting frozen bytes.
