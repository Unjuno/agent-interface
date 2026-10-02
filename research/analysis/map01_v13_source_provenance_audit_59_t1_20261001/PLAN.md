# Issue #59 — current-main v13 source-closure audit successor T1

## H / T / D / C / U

- **H:** The complete declared source inventory in the retained v13 telemetry-session preregistration is either unchanged or detectably drifted in current main; resolving the repository root from the runner's own path will avoid the T0 command-boundary STOP without weakening source identity.
- **T:** Freeze one exact current-main commit. Read `research/doom/map01_measurement_integration_live_v2_prereg.json` from that commit. Hash the exact union of its `source_sha256` and `canonical_upstream_sha256` Git blobs with SHA-256. Run the candidate once, then the independent raw auditor once if the candidate exits 0. Both tools derive the repository root from their own source path unless explicitly overridden.
- **D:** `PASS_SOURCE_CLOSURE_ONLY` requires exact prereg map validity, complete path-set equality, every current-main blob present and equal to every single prereg pin, candidate/raw agreement, and zero audit errors. Any validly audited changed/missing pinned source is `FAIL_PINNED_SOURCE_DRIFT`. Missing/extra/duplicate candidate rows or malformed preregistration are `FAIL_AUDIT_INTEGRITY`. Execution/setup failure is STOP, not a scientific failure.
- **C:** Git-object contents at one immutable commit; no working-tree files are hashed. The expectation is the historical preregistration itself, not a newly authorizing preregistration. The script-derived root is checked independently by running from the package directory without a root override.
- **U:** A clean source-closure result would not establish that the pinned implementation is correct, that its source inventory is complete beyond declared files, or that v13 is current-main-compatible. It does not execute ViZDoom, X11, release telemetry, scorer polling, or Actions; it cannot establish physical release, scorer isolation under load, or task efficacy. Historical allocation `map01-measurement-integration-live-02` remains consumed/historical; live MAP01 remains unauthorized without a fresh current-main allocation and exact exclusive environment/resource grant.

## Freeze

- Current main commit: `c7346fe1ad0c0d40254c6aa7898a8ed6de76c0dc`.
- Preregistration Git blob on that commit: `88dddea060ad1434a8bc7d67469382928a70ddd7`.
- Preregistration names historical base `7356970b15406c74bd2b404327f39c2e6b546022` and allocation `map01-measurement-integration-live-02`; this T1 does not reuse the allocation.
- The predecessor T0 `STOP_RUNNER_REPO_ROOT` remains unchanged at its own additive path and PR #5966.
- The T1 branch/path collision check returned no match.

## Execution boundary

Host-only CPython over the fetched local Git object database. No network calls from candidate/auditor, container, GPU, game, model, GUI, OS input, or Actions dispatch. Docker Desktop/OrbStack ownership remains unresolved; this T1 is not the live integration allocation.
