# Independent integration audit - Issue #3569 allocation 01

## Image identity correction

The frozen record and original PR summary say the cached image was pinned to
`sha256:0e35cdb51a82e59d359ec09b85ce835d9217a1eab65b68ce1871c9b0a85014c9`.
However, the recorded invocation in `REPORT.md` executes the mutable tag
`issue-3548-route-unit:20260920`, not that immutable digest. The retained
artifacts do not include an actual-container identity proving which image the
tag resolved to at invocation time.

Therefore the container leg is
`STOP_IMAGE_IDENTITY_UNVERIFIED`. The observed import error is retained
verbatim, but must not be attributed to the preregistered image as a verified
reproduction. The original `RESULT.json`, `REPORT.md`, and preregistration
are unchanged; this addendum corrects their integration interpretation.

## Independent route-host disposition

The separate host-capability check found no directly selectable same-model
API/CLI/MCP route affordances or verifiable usage receipts. No nonce or
task/model/route call was made. This remains `STOP_MODEL_ROUTE_UNAVAILABLE`
and does not depend on the container image identity claim.

No retry is permitted under this consumed allocation. Any future container
preflight requires a new allocation that invokes the immutable digest directly
and retains evidence of the actual container image ID. No task-performance,
route-equivalence, or transport-correctness conclusion follows.