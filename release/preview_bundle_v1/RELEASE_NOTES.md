# Agent Interface Research Preview RC1

Release-candidate base: frozen by Issue #515 and the `release/research-preview-20260917-rc1` branch.

## What is promoted

This preview packages the existing Golden Desktop Demo v3 path and its complete tracked source/evidence closure. The release does not automatically absorb newer mechanisms from moving research `main`.

The promoted demo retains the narrow desktop evidence already documented under `runtime/GOLDEN_DESKTOP_DEMO_V3.md`: six exact tasks in the frozen first v3 run, stale-reference refusal/repair, and verified terminal releases at that experiment's declared scope.

## Packaging change in RC1

Earlier release-readiness work showed that the reduced offline research bundle omitted files required by `audit-retained`. RC1 therefore packages the complete tracked release-candidate tree instead of attempting an inferred/pruned dependency closure. The bundle builder checks required retained files, launcher executable modes, checkout preflight, extracted-archive preflight, and emits a SHA-256 manifest.

## Supported target

RC1's preview target is WSLg / Linux-X11 with Chromium and the Windows Codex CLI bridge visible from WSL. Native Windows, native macOS, generic Linux, Wayland-native execution, general GUI reliability, human-level speed, and stable API compatibility are not claimed.

## Acceptance still requiring the supported host

Packaging CI can validate deterministic archive construction and retained-audit source closure on a generic Linux runner. It cannot substitute for the intended WSLg host. Final publication acceptance still requires, on the supported host, `setup`, `doctor`, one no-retry fresh golden run, and `audit-live`; a failure is retained release evidence rather than tuned away.
