# Issue #3676 — independent Docker audit validation

This is a separate Docker Desktop audit-validation allocation for the exact
source and retained raw on branch `research/issue-3676-audit-hardening-v1` at
`4ad919f773af0e788d1f7b173fd0abd0ebed5115`. It does not modify the original
#3675 raw, freeze, or audit, and does not repeat the OrbStack/XRes experiment.

## H/T/D/C/U

- **H:** The hardened offline auditor accepts the exact source-bound #3675 raw,
  rejects the prior three and eight added corruption cases, and produces the
  same result through direct function and CLI routes in isolated Docker.
- **T:** Freeze source/blob hashes and Docker image/engine. Run the four frozen
  tests once in one network-disabled container, then run the documented CLI
  audit once in a second fresh container over unchanged evidence.
- **D:** See `FREEZE.json`. PASS requires all four tests, nine rejected
  mutations, exact raw/source/freeze hashes, and a separate-container CLI PASS
  with zero errors. Any altered source bytes stop before interpretation.
- **C:** One local Docker Desktop Linux/amd64 audit-validation allocation.
  No GUI, X11, native input, model/provider, network, product, general
  completeness, or original XRes-runtime claim.
- **U:** This finite mutation set cannot establish resistance to arbitrary
  corruptions or independently reproduce the OrbStack XRes behavior.

## Result

`PASS_DOCKER_AUDIT_VALIDATION` is recorded in `RESULT.md`. The exact test
transcript and second-container CLI JSON are retained under
`artifacts/issue3676-audit-hardening-docker-desktop-01/` and SHA-256-bound
there. The earlier un-frozen Windows checkout attempt is documented as an
input-byte preflight stop; it is not counted as an experiment or a code failure.

The source must be mounted from exact Git blob bytes. On Windows with
`core.autocrlf=true`, a regular checkout changes these frozen LF files and
intentionally fails the source/hash gate. The validated run used a
`git -c core.autocrlf=false archive` snapshot.
