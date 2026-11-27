# Isolated prestarted-supervisor Xvfb run 39619576394

## Frozen execution

- GitHub Actions run 39619576394, job `prestarted-cancel-xvfb`, PR #9315.
- PR head commit: `084a7259c3aedcdc4cf084ac75a844fe9a5afb03`.
- Raw `GITHUB_SHA`: `9de4cbf3a6cd2d6b459b164bf7161a56bc7a4271` (the PR merge ref).
- Ubuntu 26.04, Python 3.12.15, Xvfb 2:21.1.22-1ubuntu1.3. Raw JSON, observation image and empty server log are copied byte-for-byte from the artifact.
- SHA-256: `raw.json` `6f61517e5ef94afc15190e06f7c7d44c519e6c5f03d8fbe5dc9da47b7952bc3b`; `observation.png` `751e00d5f926a15128a45baec1b2310aabee740b363119bd79dd224986d81f01`; `xvfb.log` `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

## Outcome

The corrected trace wrapper reached the owner cancellation method; the owner process retired with exit `-15`. Cancellation returned in 13.250 ms. The prestarted worker still returned `unknown / invalid_cleanup_request`; no XRes disconnect or release/readback occurred. The public result remained cleanup UNKNOWN, release unconfirmed, task_success null, and replay denied. Independent release readback, late-request horizon readback, and independent task oracle are null. Later harness cleanup saw both keys up, but this is not evidence of supervisor cleanup.

The new worker-side `invalid_fields` diagnostic was added in source commit `084a7259`, but the owner adapter reduced the worker result to a generic reason and dropped that field. Thus this run does not identify the rejected predicate. The request mapping is changed in a later local commit to retain the diagnostic through the caller. Do not infer the field from the other visible owner snapshot values; the raw artifact does not include the actual serialized request.

The sibling `x11-integration` job in this same run also failed two existing integration assertions because the new bounded API returned `pending` where the tests assumed a terminal cancellation response. The tests were revised in commit `422f7ea6` to measure the response separately and retrieve the terminal cancellation through `interface_results`; that revision was not part of this run. Other Xvfb artifacts from the sibling job remain distinct from this supervisor trial.

## Scope

This is a failed live-Xvfb composition attempt. It does not prove release, task effect, bounded recovery, reliability, WSLc portability, MAP01, or matched efficiency. Preserve this first outcome unchanged.
