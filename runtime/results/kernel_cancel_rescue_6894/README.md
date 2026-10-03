# Lost-receipt cancellation archive rescue

Source: PR #6894, `79fd2fc18ea7f2ff97adab37db33641554f22cd1`.
Integration base: `1356385fa8f0fab788be2a4efac2e311f88b5c24`.

All 95 original files under `runtime/results/kernel-cancel-effect-01a0ff2c`
are restored with exact Git bytes. Historical failures, Windows execution records,
V3/V4 source context and independent public projections remain unmodified.
The restored staged packet was compared against the source commit (exit 0).

Fresh macOS Python 3.14 saved-record oracle runs, normal and optimized, both
exited 0 at 2026-10-03 19:09:49 UTC: two missing-possible-effect gaps before,
zero after, six directed corruptions rejected. This reruns the JSON-only oracle,
not the original producer or historical Windows/source-context tests. Private
originals and native input/effect evidence are not authenticated by this check.

No production code is replaced. Main already retains the possible-effect repair
and accepted-begin floor, plus newer nominal and effect-start guards absent from
the old lifecycle. The older branch's five in-module tests and V4 joint reviewer
tests still require an overlap review before claiming all unique regressions are
integrated. This packet rescue is not whole-branch completion or deletion authority.

Local analysis-index CI and current-tree kernel regression verification remain
pending. Formal experiments and native cancellation are not executed here.
