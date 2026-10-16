# A01 — retained A04 coast scalar-rule replay

## Result

`FAIL_PROTOCOL_POSTHOC_WINDOW_FREEZE`. The Issue #59 comment fixed the exploratory threshold, five eligible coast intervals, and decision-4 exclusion, but not the exact timestamp windows, baseline rule, or independent oracle. Those were specified after inspecting A04. The first-trigger rows below are retained as post-hoc observations, not a preregistered pass. Decisions 0, 1, 2, 3, and 5 crossed the scalar predicate at sequences 5, 98, 130, 178, and 221; decision 4 remains excluded.

| Decision | Retrospective baseline sequence / health | Window samples | First crossing sequence / health | After derived window start | Before report-level terminal |
| --- | --- | ---: | --- | ---: | ---: |
| 0 | 2 / 97 | 69 | 5 / 91 | 778.308 ms | 18,868.564 ms |
| 1 | 72 / 79 | 45 | 98 / 74 | 7,356.755 ms | 5,637.717 ms |
| 2 | 118 / 68 | 36 | 130 / 63 | 3,530.931 ms | 6,627.866 ms |
| 3 | 155 / 46 | 39 | 178 / 38 | 6,407.947 ms | 4,532.443 ms |
| 5 | 217 / 30 | 45 | 221 / 24 | 1,024.761 ms | 11,676.209 ms |

These are crossings of an offline scalar rule over existing typed observations. They do not establish that a consumer received a monitor event, canceled work, changed input, or improved the next decision.

## Method and custody

The prior Issue #59 comment [5988485217](https://github.com/Unjuno/agent-interface/issues/59#issuecomment-5988485217) selected the candidate, five unauthored intervals, and decision-4 exclusion. The exact interval formula, retrospective baseline selection, and oracle were determined after reviewing A04. That is the primary protocol failure. The original first-calculation extraction, stdout, and candidate/oracle invocation receipts were not retained. The scripts in this package were added afterward; they reproduce a retrospective calculation from the ZIP and do not repair original-run custody.

The threshold values (5-point drop; 2 low samples among the latest 3) were read from PR #7527 head `1c12f87d9316f2faa3b2e4b5da55f23ceb2296d4`. Input is PR #7990 head `3c6862937f30a22aad6380699f23da92d5d2c6f9`, retained ZIP SHA-256 `b6e8529a51e89e6f1c51374fbd27f121bab594c92014ee2fe73aa2f94ef98163`.

The execution uses a local `CANDIDATE.py` scalar-rule reimplementation and a separate raw-only scalar oracle; neither imports nor executes the actual #7527 `UnauthoredCoastMonitor`, its typed extractor, or its unknown/age/binding fail-closed behavior. A post-hoc separate-process comparison of these scripts matched the five reconstructed rows after one auditor output-schema correction. The original first-calculation outputs remain unavailable.

The selected interval is defined by `report.planner_terminal_observed_ns - report.model_ns` through the report terminal. These are report-level proxy boundaries, not the protocol's sent `turn/start` and received `turn/completed` timestamps. The report terminal follows protocol completion by 49.508–140.596 ms across these decisions. The selected retrospective baseline sequences (2/72/118/155/217) also differ from the actual cover-admission source sequences (1/71/117/154/216). The crossings happen to be the same under these two baselines, but their timings and baseline definitions are not interchangeable. The listed “before terminal” offsets refer only to the report-level proxy boundary.

No threshold/window search was performed during the reconstruction. The first disposition remains a protocol failure; no rerun or relabeling as a pass is permitted.

## Limitations

This retrospective scalar-rule application is neither an efficacy estimate nor a counterfactual recovery estimate. A04 source provenance remains unresolved: the staged controller manifest declares 80,787 bytes and SHA-256 `10a80334ef21b5dadd5d160ceec11ff2400f6b30ea8b55ffa0aeab3dde832f29`, while the controller at A04's frozen main commit `6860b585305e539ec93896f5adcbf658cbbd8592` is 79,562 bytes. The raw ZIP contains no source file to validate the staged digest. Retained original A04 outcomes remain authoritative.

No game, model, GUI, input, container, or GPU was used. The consumed A04 allocation was not rerun.
