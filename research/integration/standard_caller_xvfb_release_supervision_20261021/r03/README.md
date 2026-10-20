# Standard-caller Xvfb release-supervision diagnostic — r03

## Frozen run and custody

- GitHub Actions run [39447636867](https://github.com/Unjuno/agent-interface/actions/runs/39447636867), PR #9290 head `0c82e4f1d7d072b37d292cfca0dc65f12b1dcd5e`, rebased on main `4100d0ab0a07b74b6f80fbb5ec080a6f22bf5c8e`.
- `.github/workflows/runtime-x11-v1.yml`, Ubuntu runner, private Xvfb. Compilation and experimental bridge boundary passed. The first Xvfb suite had one error; all subsequent Xvfb server-stop, four cancellation trace runs, and artifact-retention steps completed.
- Downloaded JSON and PNG artifact files are copied unchanged. `SHA256SUMS` covers those files, excluding this README and the manifest itself.

## Outcome and diagnosis

The failing test was `XResDisconnectFenceIntegrationTests.test_dead_owner_delayed_xtest_outcome_after_fresh_cleanup`. It attempted `json.loads(idle_marker.read_text())` after observing that the child-created marker path existed; the file was empty at that instant, raising `JSONDecodeError` at line 1 column 1. The child writes the marker directly, and the parent polls only for path existence before reading. This is consistent with a publication/read race in the integration fixture; it does not show a failure in the worker-receipt code path. It must still be treated as an actual failed run, not erased or called a pass.

The later standard-caller blocked-owner trials completed and their raw receipts are preserved here, but they do not change this run's failed overall Xvfb job. The earlier separate instrumented run 39446039020 remains the prior scoped pass. A follow-up fixture change writes the JSON marker to a sibling temporary file and atomically replaces the published path. The change passed the fresh Xvfb rerun [39448218110](https://github.com/Unjuno/agent-interface/actions/runs/39448218110), preserved separately in [r04](../r04/README.md). Do not infer cross-run reliability from these diagnostic runs.

No WSLc allocation or physical desktop input was used. The whole-server-stop, MAP01, task-effect integration, reliability, and matched-efficiency limits recorded in r01/r02 remain.
