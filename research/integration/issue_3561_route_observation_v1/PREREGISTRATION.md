# Issue #3561 — current-main route observation successor

Parent chain: #3544 → #3548 → #3557 → #3561. Prior STOPs and allocation
evidence remain unchanged. This is a separate OrbStack allocation on current
main and tests whether the earlier 500x260 result reproduces under #3561's
320x240 request at the same route boundary.

## H/T/D/C/U

**H** — At main `b092d73893ccb283def5886cdd2ee2b6c3a01089`, direct public API,
CLI and stdio MCP each make exactly one read-only capture of a fresh same-recipe
fixture for region `[0,0,320,240]`; request lineage and decoded RGB pixels are
identical. This is transport/capture replication, not task or efficiency
comparison.

**T** — Freeze main SHA, runner/auditor source commit, image ID and package
versions. Preflight imports without route calls. In one new network-disabled,
read-only-source OrbStack container with isolated Xvfb, run API, CLI and MCP
once each, recreating the fixture; retain every raw request, report, image,
process receipt, output timing, image/pixel hash and cleanup record. Run the
independent audit from a second container against a separate read-only frozen
source mount. No route retries, models or GUI input.

**D** — PASS only if exactly three returned read-only observations satisfy the
requested region, matching raw-capture lineage, identical independently
decoded RGB hashes, clean fixture/transport cleanup, immutable raw manifest,
and all frozen-source/provenance checks. Unavailable route, semantic mismatch,
or incomplete audit remain distinct STOP/FAIL/HOLD outcomes.

**C** — Same OrbStack host/image/display, source, fixture recipe, frame and
requested region; one fresh fixture per route. Timing remains descriptive and
route boundaries differ. No model-visible prompt, token, cost, task correctness,
recovery, or router policy is measured.

**U** — Does the route equivalence persist on current-main source and the
successor issue's requested 320x240 region? A pass supports only this fixture
and capture unit; it does not replace the separate matched agent/task study.
