# Health-only invalidation identity repair

The health-only monitor returned sequence/outcome/timing but omitted the originating observation's capture time and pointer binding. PR #7963's frame barrier therefore raised before next planning on both hard health loss and unavailable health extraction. This repair copies capture time and binding into the monitor event and preserves the RGB hash when supplied. Binding is deep-copied. Missing identity remains missing; no later observation or nested extracted signal supplies a replacement.

This package is a local regression repair, not a new formal experiment or consumed-allocation replay. Parent: #59. Dependency: #7963 at `0d08aa48521c343bdfb4936400910363a9d56eb6`. The controller production source and its frame-barrier validation are unchanged by this follow-up. Review origin: https://github.com/Unjuno/agent-interface/pull/7963#discussion_r4180809593 .

## Decision and observed results

H: Preserving the source observation identity lets valid health-only invalidations cross the existing V39 barrier without weakening rejection of incomplete identity.
T: Add real-monitor identity/alias tests and two deterministic `controller.main()` schedules (hard and extractor-UNKNOWN); reproduce on the old producer, then repair and run adjacent wait, cleanup, paired-signal and dispatch tests.
D: PASS only if the old producer reproduces the identity failure, the candidate reaches the next planner iteration from the fresh observation, and existing negative and paired paths pass. Missing source identity must not be invented.
C: A fake invalidation event carrying metadata can hide this defect; the new schedules call the real `build_cover_monitor`, guard and monitor with a fake signal reader.
U: Fake process/queue/readers/executor and scripted images; no live application, pixel extraction, native input, real planner interruption, reaction latency, task effect or recovery benefit is established.

| Retained invocation | Outcome |
|---|---|
| `red` | 16 methods executed; 4 expected error records (two monitor subcases and two main-controller cases). Controller errors are the missing-observation-identity RuntimeError. |
| `green` | 16/16 PASS with unchanged tests and the repaired producer. |
| `adjacent` | 28 executed cases PASS plus one cleanup-module import error: the initial command omitted its required Python search path. |
| `adjacent-repaired` | 40/40 PASS after explicit `PYTHONPATH=research/doom:research/live_control`; no further production changes. |

The successful focused and adjacent sets contain 56 distinct tests. Each receipt includes source hashes, command, environment, start/end timestamps, exit code and log hashes. This is normal Python 3.12.14 on macOS 27.0.1 arm64 using the existing bundled Pillow runtime; no installation or container launch occurred. Durations in test logs are not performance measurements.

The controller schedules use an immediate executor: invalidation arrives in the post-result cover-cancellation wait. They exercise the real wait dispatcher, actual health-only monitor, actual frame barrier and next planning iteration, but do not exercise pending-model-loop timing. The earlier fake-monitor schedule uses the same immediate executor and has the same limitation. The newer frame is already latest when the terminal arrives, while the saved invalidation must still identify the earlier source sequence 11/capture 110. The inherited typed schedule exercises waiting past stale frames. Existing tests retain incomplete-identity, wrong-binding, wrong-RGB and older-capture rejection. Unit tests additionally verify copying and two-way nested-binding alias isolation and refusal to borrow missing identity from the nested signal.

## Reproduce and inspect

From a checkout of this proposal with Python and Pillow available:

```sh
python -B research/doom/invalidation_identity_59_e0cc_20261005/run_regression.py --label local-focused
python -B research/doom/invalidation_identity_59_e0cc_20261005/run_regression.py --label local-adjacent --adjacent
```

Labels are write-once. To reproduce RED, in a separate disposable checkout keep the proposal's tests and replace only `research/live_control/observable_signal_guard_v2.py` with that path from the pinned dependency commit above. Do not replace historical logs. `baseline-source-manifest.json` binds the 27 original source/dependency files; execution receipts bind candidate tests and repaired source. `static-checks.json` records syntax compilation and the changed-source hashes. No project-level Python lint configuration was found among root lint/config entries; scoped syntax compilation and `git diff --check` were used. The full publication diff reports one trailing space emitted by unittest in the retained RED stderr; that evidence byte is preserved. Source, test, runner, JSON and Markdown changes pass the scoped whitespace check.

Original local logs and receipts are retained privately. Published log copies replace only absolute repository and Python-runtime path prefixes with `<repo>` and `<python-runtime>`; the relevant receipts record original and published hashes. The setup note retains an earlier path-resolution failure before the runner existed. The first adjacent import failure remains published and was repaired in the runner, not by changing production code or hiding a case.

## Review and integration boundary

The existing separate bugbot agent inspected the final diff and first RED/GREEN logs without rerunning: no material defect found in the producer change or regression assertions, with the synthetic and post-result limitations above. This technical review is not a preassigned quorum vote. No main merge or whole-goal completion is claimed. Content quorum, exact-tree nonauthor integration and current protection checks remain required for main.
