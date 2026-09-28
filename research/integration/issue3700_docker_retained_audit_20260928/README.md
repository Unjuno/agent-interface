# Docker re-audit of the retained Issue #3700 comparison

This is an independent, read-only Docker replay of the published record
verifier. It is not a new 50/250 ms experimental row and does not rerun Calc,
the primary model, or any user input. It adds an environment-diverse audit of
the existing four-row evidence package.

## H / T / D / C / U

**H.** Running the committed verifier over the exact published archive in an
isolated Docker container will either reproduce its retained-record consistency
PASS or expose a reproducibility failure.

**T.** The source files were fetched from GitHub raw at main snapshot
`7be3499f515636875edbe071ec127fcc88714220`. The public verifier and evidence
archive were mounted read-only in the cached `issue2704-calc-readiness:formal01`
image, with `--network none`, read-only root, 1 CPU, 512 MiB memory and 64 PID
limit. The command and exact artifact/image identities are in `AUDIT.json`.

**D.** Container exit 0; verifier returned
`PASS_RETAINED_RECORD_CONSISTENCY`, checked 258 archive members, and found all
four rows' recorded saved-result/release consistency true. Exact stdout is
retained in `audit-output.json`.

**C.** The audit checks hashes, inventory, frozen source and plan identity,
request/response and PNG agreement, saved FODS values/formula, recorded
declarations, timing arithmetic, releases and recorded container cleanup. The
container had no network and could not write to the mounted evidence.

**U.** This does not independently view the model's images, prove that primary
declarations match model cognition, verify live cleanup, establish host-render
or model-useful-feedback timestamps, recover provider tokens/cost, remove order
or cache effects, provide held-out validation, or prove a causal wait benefit.
The existing `HOLD_PRODUCTION_ADOPTION` disposition remains unchanged. No
production default or historical row was changed.

## Provenance note

Main advanced to `3553dc1af1125441a6b44256755e7e22df40836d1` during this audit.
Before publishing, GitHub Contents API readback at that current main confirmed
that `RESULT.json`, `manifest.json`, `evidence.zip`, and `verify.py` have the
same Git blob identities as the pinned `7be3499` snapshot. No current-main
evidence bytes were substituted into the run.
