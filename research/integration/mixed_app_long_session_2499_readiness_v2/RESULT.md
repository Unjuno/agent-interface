# #2937 readiness guard v2 result

Date: 2026-09-21

Decision: `PASS_STRICT_FAIL_CLOSED_READINESS_CONTRACT`

Ran locally in pinned Docker image
`python:3.12-slim-bookworm@sha256:1aaa65a85fda306ffb8b910824d4e93bdce61e212c7e87168123ea3073b41a1a`
with `--network none`, read-only source mount, and tmpfs. Six tests passed:

- missing and auxiliary-only identity refuse before operation
- malformed XID shapes (`True`, negative, zero, leading-zero, nonnumeric,
  missing) refuse
- malformed surface generations (bool, negative, float, string, missing)
  refuse
- a malformed same-role candidate cannot be masked by a valid candidate
- multiple main candidates refuse; one valid main plus auxiliary admits
- old receipt refuses after XID change/reuse, surface-generation change, or
  role change

This repairs the two review findings from closed/unmerged PR #2944. It is still
a contract-only readiness result; the live #2499 formal four-transition
session and all-app integration remain unverified.
