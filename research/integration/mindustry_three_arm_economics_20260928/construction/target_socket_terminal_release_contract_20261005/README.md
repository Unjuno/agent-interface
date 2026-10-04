# Require a completed Mindustry socket terminal

Date: 2026-10-05. Parent research question: #57 / #5130. Scope: host-side target-socket consumer only.

## H / T / D / C / U

**H.** A matching socket terminal with `status="failed"`, `"cancelled"`, or no status must not be promoted to a successful action receipt merely because its release object says `verified=true`.

**T.** Feed the adapter a synthetic matching terminal with a verified release and vary only its terminal status across `failed`, `cancelled`, `needs_decision`, and missing. Compare against the existing completed-terminal control. Do not start a bridge or target process.

**D.** Accept the completed control and reject each noncompleted/missing status with `SocketSubmitStop`. The check is supported if the unpatched consumer returns success for at least one noncompleted response and the patched focused test rejects all four.

**C.** A terminal status may be advisory or absent in some bridge versions. Existing controls encode `completed`, but live producer compatibility has not been tested. This check complements the explicit empty-key/button release-array validation in PR #7683.

**U.** Synthetic host-side protocol evidence only. It does not establish upstream producer behavior in a live run, physical input release, Mindustry effect, model/provider use, Docker availability, or second-domain economics. The #5130 resource gate remains unchanged.

## Result

The adapter now requires `terminal.status == "completed"` before issuing its successful terminal/released result. `test_noncompleted_matching_terminal_cannot_be_promoted` exercises the four negative statuses while preserving the existing verified-release control. Against current-main baseline blob `ffaa64cb04f0457c11e52393b32a5ba9b2b733b0`, an in-memory response with matching `status="failed"` and `release.verified=true` returned `{"terminal": true, "released": true}`. No release-array validation is included in this change; that contract is handled by PR #7683.

This is a construction regression, not formal evidence for #57's integrated live comparison.

## Composition check with the release-array PR

The status-only change was locally composed with the current PR #7683 head
`1d7bb20bcde67333f58e41a24f8dce68f8561ffd` over main
`6556d46b1045ca4d45fc32dc8700321dcbef519a`. The merge was clean after moving
the status regression to its own test method; the combined test suite passes
22 focused tests (2 expected Windows AF_UNIX skips) and 125 full-package tests
in both normal and optimized Python (2 skips each). This verifies host-side
adapter/test compatibility between the two open patches only; neither PR was
merged by this probe, and no live producer, input, Mindustry, Docker,
provider, or economics behavior was exercised.
