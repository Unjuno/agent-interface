# Standard-caller Xvfb release-supervision diagnostic — r04

## Frozen run and custody

- GitHub Actions run [39448218110](https://github.com/Unjuno/agent-interface/actions/runs/39448218110), PR #9290 source commit `8169d5762575cfeca86e61e8d46f6c213556faea`.
- `.github/workflows/runtime-x11-v1.yml`, Ubuntu runner, private Xvfb. Compile, bridge boundary, the private Xvfb integration, and all artifact-retention steps passed.
- JSON and PNG files were downloaded unchanged. `SHA256SUMS` covers all downloaded raw files and excludes this README and the manifest.

## Outcomes

All five blocked-owner cancellation trials completed. Each independent synthetic task oracle passed: exactly one initial `a` effect, no delayed `b` press, both keys up after release and at the 8.5 s horizon. Cancel returned in 627.536–879.206 ms; independent release-worker elapsed time was 549.207–569.696 ms. Each runtime receipt remained `release_confirmed=false`, cleanup `UNKNOWN`, `task_success=null`, with replay denied. This is a scoped test-oracle result, not a runtime task-success promotion.

The target-generation/recovery scenario passed: stale-generation dispatch was refused; the fresh post-recovery effect `[3]` was independently observed 52.975 ms from call start. Runtime task-success API remained null. The separate whole-Xvfb-stop scenario still failed its original task oracle: key `a` remained down at the 8.5 s horizon while the server was unavailable. Its later fresh-target recovery task is a separate observation and does not repair the failed outage task.

This is one private-Xvfb workflow run, not a reliability estimate. No WSLc allocation or physical input was used. Outage-time release, MAP01, product task success, matched efficiency, and cross-run reliability remain unproven.
