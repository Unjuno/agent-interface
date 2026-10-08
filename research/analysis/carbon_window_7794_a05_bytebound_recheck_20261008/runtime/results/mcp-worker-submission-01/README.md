# MCP pre-worker admission repair

Issue #5539 identifies a real shutdown ThreadPoolExecutor rejection before invoke starts. The old public MCP implementation leaves its busy slot held even after a healthy executor is restored. This integration repairs that source boundary; it does not rerun or replace the research worker's frozen formal allocation or claim its unpublished raw evidence as locally verified.

Baseline main 59ffec5d551b0adcf11057eee6da814237a748c8 has the exact Issue source blob 7227f105aa4481a6110cd384a038bc72aa0aabda. Candidate executable/tests/docs are committed at 75b9dee93523dfb08c60980e259eb25650a8b95d.

A per-call admission transfers atomically to callable entry or is revoked while pending. Executor submission is synchronous with copied context, so rejected pending work releases capacity and cannot later enter. Started work remains exclusive through existing report/finalization. Completed/cancelled futures revoke only still-pending work. Shielding, busy refusal and no automatic request replay remain.

Engineering validation on WSL3.0.1/kernel6.18.40.1, Python3.12.3:
- Real shutdown executor: baseline remains busy after a healthy replacement; candidate closes the never-opened owner with no native session/release.
- Queue-then-reject control: revoked late callable creates no second operation artifact.
- Start-then-raise control: running call stays busy/exclusive until finalization; effect remains unknown in the error response; caller ContextVar preserved.
- Accepted failed future without callable entry: failed-before/passing-after pending revocation.
- Existing started-transport cancellation and overlapping-call tests remain green.
- Focused66, fullCLI240, sharedprotocol324 + harness135 tests pass.

Retained first test-writing error: direct FastMCP raises ToolError rather than returning an error response. The first red log is an ERROR and is not the defect assertion. red-02 is the corrected baseline FAIL at recovered.isError; callback-red is the additional failing ownership case. No native GUI/input/model call or performance result belongs to these injected dependency-lifecycle checks. The adversarial executor subclasses are integration controls, not observed production incidence.

34 exact raw/source/log files in raw.tar.gz. Read-only verifier: python3 -O verify.py. It accounts for frozen bytes and recorded test results, not physical truth or an independent execution of the tests. No overall #2789 completion or general reliability claim. Wider useful-feedback/perception work remains open.
